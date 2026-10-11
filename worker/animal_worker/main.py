"""Animal Logger worker: video source -> YOLO -> BioCLIP -> dedupe -> Supabase.

Examples:
  python -m animal_worker.main --source sample_videos/park.mp4 --dry-run
  python -m animal_worker.main --source "https://.../stream.m3u8" --camera "River Overlook"
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .dedupe import Deduper

log = logging.getLogger("worker")
ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", required=True, help="video file, webcam index, or RTSP/HLS/HTTP URL")
    p.add_argument("--camera", default="Camera 1", help="camera name stored with each sighting")
    p.add_argument("--location", default=None, help="human-readable camera location")
    p.add_argument("--species-file", default=str(Path(__file__).resolve().parents[1] / "species.json"))
    p.add_argument("--fps", type=float, default=1.0, help="frames per second to analyse")
    p.add_argument("--cooldown", type=float, default=60.0, help="seconds before the same species on the same camera is logged again")
    p.add_argument("--min-confidence", type=float, default=0.5, help="minimum BioCLIP confidence to log")
    p.add_argument("--park", default="yellowstone", help="park slug stored with the camera")
    p.add_argument("--source-kind", choices=["live", "replay"], default=None,
                   help="override; default is 'live' for an image URL source, 'replay' for files/video")
    p.add_argument("--every", type=float, default=60.0, help="seconds between polls of an image URL (min 30)")
    p.add_argument("--weights", default="yolov8n.pt", help="YOLO weights, including a trained best.pt")
    p.add_argument("--detector-confidence", type=float, default=0.4)
    p.add_argument("--bird-confidence", type=float, default=0.15)
    p.add_argument("--bear-confidence", type=float, default=0.3)
    p.add_argument("--tile-size", type=int, default=None, help="overlapping tile size for distant animals")
    p.add_argument("--dry-run", action="store_true", help="print sightings instead of writing to Supabase")
    return p.parse_args(argv)


def is_image_url(source: str) -> bool:
    return source.lower().startswith(("http://", "https://")) and source.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png"))


class LogSink:
    """--dry-run sink: just logs the sighting."""

    def record(self, species, conf, crop, camera):
        log.info("SIGHTING %s (%s) %.0f%% on %s", species.common_name, species.scientific_name, conf * 100, camera)


class StoreSink(LogSink):
    """Logs, then writes the sighting (and its snapshot) to Supabase."""

    def __init__(self, store, location=None, park="yellowstone", source_kind="replay"):
        self.store, self.location, self.park, self.source_kind = store, location, park, source_kind

    def record(self, species, conf, crop, camera):
        super().record(species, conf, crop, camera)
        s = self.store
        s.insert_sighting(
            species_id=s.species_id(species.common_name, species.scientific_name),
            camera_id=s.camera_id(camera, self.location, self.park),
            confidence=conf,
            snapshot_url=s.upload_snapshot(crop),
            source_kind=self.source_kind,
        )


def process_frame(frame, ts, camera, detector, classifier, deduper, sink) -> int:
    """Detect, classify and dedupe one frame; send new sightings to `sink`. Returns how many were logged."""
    logged = 0
    for det in detector.detect(frame):
        if hasattr(classifier, "classify_for_label") and hasattr(det, "label"):
            result = classifier.classify_for_label(det.crop, det.label, det.score)
        else:
            result = classifier.classify(det.crop)
        if result is None:
            continue
        species, conf = result
        species_key = species.scientific_name or species.common_name
        if not deduper.should_log(camera, species_key, ts):
            continue
        if hasattr(sink, "record_detection"):
            sink.record_detection(species, conf, det, camera, ts)
        else:
            sink.record(species, conf, det.crop, camera)
        logged += 1
    return logged


def main():
    from dotenv import load_dotenv

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv(ROOT / ".env")
    args = parse_args()

    from .classifier import SpeciesClassifier, load_species
    from .detector import AnimalDetector

    image_mode = is_image_url(args.source)
    source_kind = args.source_kind or ("live" if image_mode else "replay")
    if image_mode:
        from .capture import image_frames

        frame_iter = image_frames(args.source, every=args.every)
    else:
        from .capture import frames

        frame_iter = frames(args.source, fps=args.fps)

    detector = AnimalDetector(
        weights=args.weights,
        min_score=args.detector_confidence,
        tile_size=args.tile_size,
        class_min_scores={"bird": args.bird_confidence, "bear": args.bear_confidence},
    )
    classifier = SpeciesClassifier(load_species(args.species_file), min_confidence=args.min_confidence)
    deduper = Deduper(cooldown_s=args.cooldown)

    if args.dry_run:
        sink = LogSink()
    else:
        from .db import SightingStore

        sink = StoreSink(SightingStore(), args.location, args.park, source_kind)

    log.info("Watching %s as camera %r (dry_run=%s, source_kind=%s)", args.source, args.camera, args.dry_run, source_kind)
    for ts, frame in frame_iter:
        process_frame(frame, ts, args.camera, detector, classifier, deduper, sink)


if __name__ == "__main__":
    main()
