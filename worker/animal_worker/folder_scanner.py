"""Scan locally captured camera frames and write deduplicated sightings JSON."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .dedupe import Deduper
from .main import process_frame

log = logging.getLogger("folder_scanner")
WORKER_ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="sample_videos/katmai", help="folder containing captured JPEGs")
    parser.add_argument("--output", default=None, help="output JSON path (default: INPUT/sightings.json)")
    parser.add_argument("--species-file", default=str(WORKER_ROOT / "species_katmai.json"))
    parser.add_argument("--park", default="katmai")
    parser.add_argument("--camera", default=None, help="override camera name from frames.jsonl")
    parser.add_argument("--cooldown", type=float, default=120.0)
    parser.add_argument("--detector-confidence", type=float, default=0.4)
    parser.add_argument("--bird-confidence", type=float, default=0.15)
    parser.add_argument("--bear-confidence", type=float, default=0.3)
    parser.add_argument("--species-confidence", type=float, default=0.8)
    parser.add_argument("--tile-size", type=int, default=512)
    parser.add_argument("--weights", default="yolov8n.pt", help="YOLO weights, including a trained best.pt")
    parser.add_argument("--identify-bird-species", action="store_true",
                        help="experimental: let BioCLIP name detected birds")
    return parser.parse_args()


def load_manifest(folder: Path) -> dict[str, dict]:
    path = folder / "frames.jsonl"
    if not path.exists():
        return {}
    records = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            records[record["file"]] = record
    return records


def capture_timestamp(path: Path, metadata: dict) -> tuple[float, str]:
    value = metadata.get("captured_at")
    if value:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        parsed = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
    return parsed.timestamp(), parsed.astimezone(timezone.utc).isoformat()


class LocalSink:
    def __init__(self, park: str, metadata: dict[str, dict]):
        self.park = park
        self.metadata = metadata
        self.current_file = ""
        self.current_captured_at = ""
        self.rows = []

    def record_detection(self, species, confidence, detection, camera, timestamp):
        source = self.metadata.get(self.current_file, {})
        self.rows.append({
            "park": self.park,
            "camera": camera,
            "captured_at": self.current_captured_at,
            "observation_time": source.get("observation_time"),
            "source_kind": source.get("source_kind", "replay"),
            "source_file": self.current_file,
            "broad_label": detection.label,
            "common_name": species.common_name,
            "scientific_name": species.scientific_name or None,
            "confidence": round(float(confidence), 6),
            "detector_confidence": round(float(detection.score), 6),
            "box": list(detection.box),
        })


class FolderClassifier:
    """Keep bird labels broad unless experimental species naming is requested."""

    def __init__(self, classifier, identify_bird_species: bool = False):
        self.classifier = classifier
        self.identify_bird_species = identify_bird_species

    def classify(self, crop):
        return self.classifier.classify(crop)

    def classify_for_label(self, crop, broad_label: str, detector_score: float):
        if broad_label == "bird" and not self.identify_bird_species:
            from .classifier import Species

            return Species("Bird (unidentified)", "", "bird"), detector_score
        return self.classifier.classify_for_label(crop, broad_label, detector_score)


def scan_folder(folder: Path, output: Path, *, species_file: Path, park: str,
                camera: str | None, cooldown: float, detector_confidence: float,
                species_confidence: float, tile_size: int,
                bird_confidence: float = 0.15,
                bear_confidence: float = 0.3,
                identify_bird_species: bool = False,
                weights: str = "yolov8n.pt") -> dict:
    import cv2

    from .classifier import SpeciesClassifier, load_species
    from .detector import AnimalDetector

    folder = Path(folder)
    files = sorted(folder.glob("*.jpg"))
    if not files:
        raise RuntimeError(f"No JPEG frames found in {folder}")
    metadata = load_manifest(folder)
    detector = AnimalDetector(
        weights=weights,
        min_score=detector_confidence,
        tile_size=tile_size,
        class_min_scores={"bird": bird_confidence, "bear": bear_confidence},
    )
    classifier = FolderClassifier(
        SpeciesClassifier(load_species(species_file), min_confidence=species_confidence),
        identify_bird_species,
    )
    deduper = Deduper(cooldown)
    sink = LocalSink(park, metadata)

    for index, path in enumerate(files, 1):
        frame = cv2.imread(str(path))
        if frame is None:
            log.warning("Skipping unreadable image %s", path)
            continue
        frame_metadata = metadata.get(path.name, {})
        timestamp, captured_at = capture_timestamp(path, frame_metadata)
        camera_name = camera or frame_metadata.get("camera") or "Katmai Camera"
        sink.current_file = path.name
        sink.current_captured_at = captured_at
        process_frame(frame, timestamp, camera_name, detector, classifier, deduper, sink)
        log.info("Scanned %d/%d: %s", index, len(files), path.name)

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "park": park,
        "model": str(weights),
        "thresholds": {
            "detector": detector_confidence,
            "bear": bear_confidence,
            "bird": bird_confidence,
        },
        "source_folder": str(folder),
        "frames_scanned": len(files),
        "sightings": sink.rows,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    folder = Path(args.input)
    output = Path(args.output) if args.output else folder / "sightings.json"
    result = scan_folder(
        folder, output,
        species_file=Path(args.species_file), park=args.park, camera=args.camera,
        cooldown=args.cooldown, detector_confidence=args.detector_confidence,
        species_confidence=args.species_confidence, tile_size=args.tile_size,
        bird_confidence=args.bird_confidence,
        bear_confidence=args.bear_confidence,
        identify_bird_species=args.identify_bird_species,
        weights=args.weights,
    )
    print(f"wrote {len(result['sightings'])} sightings from {result['frames_scanned']} frames to {output}")


if __name__ == "__main__":
    main()
