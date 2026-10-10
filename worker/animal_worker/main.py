"""Animal Logger worker: video source -> YOLO -> BioCLIP -> dedupe -> Supabase.

Examples:
  python -m animal_worker.main --source sample_videos/park.mp4 --dry-run
  python -m animal_worker.main --source "https://.../stream.m3u8" --camera "River Overlook"
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from dotenv import load_dotenv

from .dedupe import Deduper

log = logging.getLogger("worker")
ROOT = Path(__file__).resolve().parents[2]


def parse_args():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--source", required=True, help="video file, webcam index, or RTSP/HLS/HTTP URL")
    p.add_argument("--camera", default="Camera 1", help="camera name stored with each sighting")
    p.add_argument("--location", default=None, help="human-readable camera location")
    p.add_argument("--species-file", default=str(Path(__file__).resolve().parents[1] / "species.json"))
    p.add_argument("--fps", type=float, default=1.0, help="frames per second to analyse")
    p.add_argument("--cooldown", type=float, default=60.0, help="seconds before the same species on the same camera is logged again")
    p.add_argument("--min-confidence", type=float, default=0.5, help="minimum BioCLIP confidence to log")
    p.add_argument("--dry-run", action="store_true", help="print sightings instead of writing to Supabase")
    return p.parse_args()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv(ROOT / ".env")
    args = parse_args()

    from .capture import frames
    from .classifier import SpeciesClassifier, load_species
    from .detector import AnimalDetector

    detector = AnimalDetector()
    classifier = SpeciesClassifier(load_species(args.species_file), min_confidence=args.min_confidence)
    deduper = Deduper(cooldown_s=args.cooldown)

    store = None
    if not args.dry_run:
        from .db import SightingStore

        store = SightingStore()

    log.info("Watching %s as camera %r (dry_run=%s)", args.source, args.camera, args.dry_run)
    for ts, frame in frames(args.source, fps=args.fps):
        for det in detector.detect(frame):
            result = classifier.classify(det.crop)
            if result is None:
                continue
            species, conf = result
            if not deduper.should_log(args.camera, species.scientific_name, ts):
                continue
            log.info("SIGHTING %s (%s) %.0f%% on %s", species.common_name, species.scientific_name, conf * 100, args.camera)
            if store:
                store.insert_sighting(
                    species_id=store.species_id(species.common_name, species.scientific_name),
                    camera_id=store.camera_id(args.camera, args.location),
                    confidence=conf,
                    snapshot_url=store.upload_snapshot(det.crop),
                )


if __name__ == "__main__":
    main()
