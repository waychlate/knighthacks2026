"""Run YOLO over every saved frame without sighting cooldown or BioCLIP."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("candidate_scanner")


def scan_camera(camera_dir: Path, output_name: str, detector) -> dict:
    import cv2

    files = sorted(Path(camera_dir).glob("*.jpg"))
    rows = []
    for index, path in enumerate(files, 1):
        frame = cv2.imread(str(path))
        if frame is None:
            log.warning("Skipping unreadable image %s", path)
            continue
        for detection in detector.detect(frame):
            rows.append({
                "source_file": path.name,
                "broad_label": detection.label,
                "detector_confidence": round(float(detection.score), 6),
                "box": list(detection.box),
            })
        log.info("%s: scanned %d/%d", camera_dir.name, index, len(files))
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "camera": camera_dir.name,
        "frames_scanned": len(files),
        "sightings": rows,
    }
    (camera_dir / output_name).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def scan_root(root: Path, output_name: str, *, weights: str, detector_confidence: float,
              bird_confidence: float, bear_confidence: float, tile_size: int | None) -> dict:
    from .detector import AnimalDetector

    detector = AnimalDetector(
        weights=weights,
        min_score=detector_confidence,
        tile_size=tile_size,
        class_min_scores={"bird": bird_confidence, "bear": bear_confidence},
    )
    cameras = []
    for camera_dir in sorted(path for path in Path(root).iterdir() if path.is_dir()):
        if any(camera_dir.glob("*.jpg")):
            cameras.append(scan_camera(camera_dir, output_name, detector))
    return {
        "frames_scanned": sum(item["frames_scanned"] for item in cameras),
        "detections": sum(len(item["sightings"]) for item in cameras),
        "cameras": cameras,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="sample_videos/katmai")
    parser.add_argument("--output-name", default="training_candidates.json")
    parser.add_argument("--weights", default="yolov8n.pt")
    parser.add_argument("--detector-confidence", type=float, default=0.4)
    parser.add_argument("--bird-confidence", type=float, default=0.15)
    parser.add_argument("--bear-confidence", type=float, default=0.3)
    parser.add_argument("--tile-size", type=int, default=512)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = scan_root(
        Path(args.root), args.output_name, weights=args.weights,
        detector_confidence=args.detector_confidence, bird_confidence=args.bird_confidence,
        bear_confidence=args.bear_confidence, tile_size=args.tile_size,
    )
    print(f"wrote {result['detections']} candidates from {result['frames_scanned']} frames")


if __name__ == "__main__":
    main()
