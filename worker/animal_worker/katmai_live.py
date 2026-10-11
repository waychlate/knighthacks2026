"""Collect Katmai frames, run the reviewed detector, and publish live sightings."""

from __future__ import annotations

import argparse
import json
import logging
import os
import queue
import threading
from datetime import date, datetime, timezone
from pathlib import Path

from .annotate import frame_extras
from .classifier import Species
from .dedupe import Deduper
from .katmai_cameras import KATMAI_CAMERAS
from .katmai_multi_poller import run_cameras
from .main import in_bear_season, process_frame

log = logging.getLogger("katmai_live")
WORKER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = WORKER_ROOT.parent
REQUIRED_CAMERA_NAMES = {camera.name for camera in KATMAI_CAMERAS.values()}


class KatmaiLabelClassifier:
    """Translate the reviewed detector's two broad classes into safe taxa."""

    SPECIES = {
        "bear": Species("Brown bear", "Ursus arctos", "bear"),
        "bird": Species("Bird (unidentified)", "Aves", "bird"),
    }

    def classify_for_label(self, crop, broad_label: str, detector_score: float):
        species = self.SPECIES.get(broad_label)
        return (species, detector_score) if species else None


class LiveSightingSink:
    """Append an audit row locally and optionally insert the sighting in Supabase."""

    def __init__(self, output: Path, *, store=None, cameras=None):
        self.output = Path(output)
        self.store = store
        self.cameras = cameras or KATMAI_CAMERAS
        self.metadata = {}
        self.source_path = Path("")

    def set_context(self, metadata: dict, source_path: Path):
        self.metadata = metadata
        self.source_path = Path(source_path)

    def record_detection(self, species, confidence, detection, camera, timestamp):
        captured_at = self.metadata["captured_at"]
        source_kind = self.metadata.get("source_kind", "replay")
        row = {
            "park": "katmai",
            "camera": camera,
            "captured_at": captured_at,
            "source_kind": source_kind,
            "source_file": str(self.source_path),
            "broad_label": detection.label,
            "common_name": species.common_name,
            "scientific_name": species.scientific_name,
            "confidence": round(float(confidence), 6),
            "detector_confidence": round(float(detection.score), 6),
            "box": list(detection.box),
            "published": False,
        }
        error = None
        if self.store is not None:
            try:
                camera_config = next((item for item in self.cameras.values() if item.name == camera), None)
                location = camera_config.location if camera_config else None
                self.store.insert_sighting(
                    species_id=self.store.species_id(species.common_name, species.scientific_name),
                    camera_id=self.store.camera_id(camera, location, "katmai"),
                    confidence=confidence,
                    snapshot_url=self.store.upload_snapshot(detection.crop),
                    source_kind=source_kind,
                    seen_at=captured_at,
                    **frame_extras(self.store, species, confidence, detection),
                )
                row["published"] = True
            except Exception as exc:
                error = exc
        self.output.parent.mkdir(parents=True, exist_ok=True)
        with self.output.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
        if error is not None:
            raise error


class LiveFrameProcessor:
    def __init__(self, detector, sink, *, cooldown=120):
        self.detector = detector
        self.sink = sink
        self.classifier = KatmaiLabelClassifier()
        self.deduper = Deduper(cooldown)

    def process(self, frame, metadata: dict, source_path: Path) -> int:
        captured = datetime.fromisoformat(metadata["captured_at"].replace("Z", "+00:00"))
        self.sink.set_context(metadata, source_path)
        count = process_frame(
            frame, captured.timestamp(), metadata["camera"], self.detector,
            self.classifier, self.deduper, self.sink,
        )
        if count:
            action = "published" if self.sink.store is not None else "recorded"
            log.info("%s: %s %d new sighting(s)", metadata["camera"], action, count)
        return count


def process_queue(work, processor):
    """Run inference serially so three camera threads do not compete for the GPU."""
    while True:
        item = work.get()
        try:
            if item is None:
                return
            processor.process(*item)
        except Exception:
            log.exception("Live frame processing failed")
        finally:
            work.task_done()


def enqueue_latest(work, item, *, log_message=log.warning):
    """Keep collection current when inference falls behind."""
    try:
        work.put_nowait(item)
    except queue.Full:
        try:
            work.get_nowait()
            work.task_done()
        except queue.Empty:
            pass
        log_message("Detector is behind; dropped the oldest queued frame")
        work.put_nowait(item)


def check_supabase(store) -> int:
    """Verify the live feed tables and canonical Katmai camera rows are readable."""
    response = store.client.table("cameras").select("name").eq("park", "katmai").execute()
    names = {row["name"] for row in response.data}
    missing = sorted(REQUIRED_CAMERA_NAMES - names)
    if missing:
        raise RuntimeError(
            "missing Katmai cameras: " + ", ".join(missing)
            + "; run supabase/schema.sql and supabase/katmai-cams.sql"
        )
    # This also confirms the sightings table exists and can be read with this key.
    store.client.table("sightings").select("id").limit(1).execute()
    return len(names)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="sample_videos/katmai-live")
    parser.add_argument("--every", type=int, default=60, help="seconds between frames (min 30)")
    parser.add_argument("--max-frames", type=int, help="frames per camera; default runs until Ctrl+C")
    parser.add_argument("--camera", action="append", choices=sorted(KATMAI_CAMERAS),
                        help="camera id; repeat for several (default: all three)")
    parser.add_argument("--weights", default="training/katmai/current.pt")
    parser.add_argument("--cooldown", type=float, default=120)
    parser.add_argument("--bear-confidence", type=float, default=0.40)
    parser.add_argument("--bird-confidence", type=float, default=0.40)
    parser.add_argument("--tile-size", type=int, default=512)
    parser.add_argument("--publish", action="store_true",
                        help="write accepted sightings to Supabase; otherwise local audit only")
    parser.add_argument("--replay", metavar="DIR",
                        help="demo: loop the JPEGs in DIR through the detector, one per --every seconds (min 1), tagged replay; needs one --camera")
    parser.add_argument("--check", action="store_true",
                        help="verify model and, with --publish, Supabase setup; do not contact cameras")
    return parser.parse_args(argv)


def replay_folder(folder: Path, args, processor):
    """Demo: loop saved frames through the live pipeline forever, as fresh `replay` sightings."""
    import time

    import cv2

    if not args.camera or len(args.camera) != 1:
        raise SystemExit("--replay needs exactly one --camera")
    camera = KATMAI_CAMERAS[args.camera[0]]
    processor.deduper = Deduper(0)  # the same stills repeat on purpose
    paths = sorted(folder.rglob("*.jpg"))
    if not paths:
        raise SystemExit(f"No JPEGs in {folder}")
    try:
        while True:
            for path in paths:
                frame = cv2.imread(str(path))
                metadata = {"camera": camera.name, "source_kind": "replay",
                            "captured_at": datetime.now(timezone.utc).isoformat()}
                processor.process(frame, metadata, path)
                time.sleep(args.every)
    except KeyboardInterrupt:
        log.info("Stopping Katmai replay")


def main(argv=None):
    from dotenv import load_dotenv

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    if args.every <= 0 or args.cooldown < 0 or (args.max_frames is not None and args.max_frames < 1):
        raise SystemExit("--every/--max-frames must be positive and --cooldown cannot be negative")
    weights = Path(args.weights)
    if not weights.is_file():
        raise SystemExit(f"Model weights not found: {weights}")

    store = None
    if args.publish:
        load_dotenv(REPO_ROOT / ".env")
        missing = [name for name in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") if not os.getenv(name)]
        if missing:
            raise SystemExit("Cannot publish: missing " + " and ".join(missing) + " in the environment")
        from .db import SightingStore
        store = SightingStore()

    if args.check:
        print(f"Model ready: {weights}")
        if store is not None:
            try:
                count = check_supabase(store)
            except Exception as exc:
                raise SystemExit(f"Supabase check failed: {exc}") from None
            print(f"Supabase ready: {count} Katmai camera rows and sightings table are readable")
        else:
            print("Local mode ready. Add --publish to check Supabase too.")
        return

    from .detector import AnimalDetector
    detector = AnimalDetector(
        weights=str(weights), min_score=min(args.bear_confidence, args.bird_confidence),
        tile_size=args.tile_size,
        class_min_scores={"bear": args.bear_confidence, "bird": args.bird_confidence},
    )
    output = Path(args.out)
    sink = LiveSightingSink(output / "live_sightings.jsonl", store=store)
    processor = LiveFrameProcessor(detector, sink, cooldown=args.cooldown)
    work = queue.Queue(maxsize=6)
    thread = threading.Thread(target=process_queue, args=(work, processor), daemon=True)
    thread.start()

    if args.replay:
        return replay_folder(Path(args.replay), args, processor)

    cameras = [KATMAI_CAMERAS[key] for key in (args.camera or KATMAI_CAMERAS)]
    source_kind = "live" if in_bear_season(date.today()) else "replay"
    mode = "Supabase + local audit" if store else "local audit only"
    log.info("Starting %s (%s, source_kind=%s)", ", ".join(c.name for c in cameras), mode, source_kind)

    def on_frame(frame, metadata, path):
        metadata = {**metadata, "source_kind": source_kind}
        enqueue_latest(work, (frame, metadata, path))

    try:
        run_cameras(cameras, output, every=args.every, max_frames=args.max_frames,
                    on_frame=on_frame, log=log.info)
    except KeyboardInterrupt:
        log.info("Stopping Katmai live detector")
    finally:
        work.join()
        work.put(None)
        thread.join()


if __name__ == "__main__":
    main()
