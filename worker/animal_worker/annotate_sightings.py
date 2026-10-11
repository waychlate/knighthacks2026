"""Draw saved YOLO detection boxes onto local camera frames."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

COLORS = {
    "bear": "#ff3030",
    "bird": "#ffd23f",
}
DEFAULT_COLOR = "#31c7ff"


def annotate_camera(camera_dir: Path, output_dir: Path, sightings_name: str = "sightings.json") -> dict:
    """Create one annotated copy for every source frame in sightings.json."""
    sightings_path = camera_dir / sightings_name
    data = json.loads(sightings_path.read_text(encoding="utf-8"))
    by_file = defaultdict(list)
    for row in data.get("sightings", []):
        by_file[row["source_file"]].append(row)

    output_dir.mkdir(parents=True, exist_ok=True)
    # This directory is derived output. Remove annotations from an older scan so
    # a new model or threshold cannot be confused with stale labeled images.
    for stale in output_dir.glob("*_annotated.jpg"):
        stale.unlink()
    written = []
    for source_name, rows in sorted(by_file.items()):
        source = camera_dir / source_name
        if not source.is_file():
            continue
        image = Image.open(source).convert("RGB")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        line_width = max(3, round(min(image.size) / 240))
        for row in rows:
            label = row["broad_label"]
            detector_confidence = float(row["detector_confidence"])
            species_confidence = float(row.get("confidence", detector_confidence))
            display_name = str(row.get("common_name") or label)
            color = COLORS.get(label, DEFAULT_COLOR)
            box = tuple(int(value) for value in row["box"])
            draw.rectangle(box, outline=color, width=line_width)
            text = f"{display_name} {species_confidence:.0%}"
            text_box = draw.textbbox((box[0], box[1]), text, font=font, stroke_width=1)
            text_height = text_box[3] - text_box[1] + 6
            text_width = text_box[2] - text_box[0] + 8
            text_y = max(0, box[1] - text_height)
            draw.rectangle((box[0], text_y, box[0] + text_width, text_y + text_height), fill="black")
            draw.text((box[0] + 4, text_y + 2), text, fill=color, font=font, stroke_width=1)

        output_name = f"{source.stem}_annotated.jpg"
        destination = output_dir / output_name
        image.save(destination, quality=92)
        written.append({
            "source_file": source_name,
            "annotated_file": output_name,
            "detections": len(rows),
        })

    return {
        "camera": camera_dir.name,
        "model": data.get("model", "yolov8n.pt"),
        "thresholds": data.get("thresholds"),
        "source_sightings": str(sightings_path),
        "annotated_images": len(written),
        "images": written,
    }


def annotate_root(root: Path, output: Path, sightings_name: str = "sightings.json") -> dict:
    root, output = Path(root), Path(output)
    cameras = []
    for camera_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        if (camera_dir / sightings_name).is_file():
            cameras.append(annotate_camera(camera_dir, output / camera_dir.name, sightings_name))
    models = sorted({camera["model"] for camera in cameras})
    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(root),
        "output_root": str(output),
        "model": models[0] if len(models) == 1 else models,
        "cameras": cameras,
        "annotated_images": sum(camera["annotated_images"] for camera in cameras),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="sample_videos/katmai", help="parent folder containing camera folders")
    parser.add_argument("--out", default=None, help="output folder (default: ROOT/annotated)")
    parser.add_argument("--sightings-name", default="sightings.json",
                        help="JSON filename inside each camera directory")
    args = parser.parse_args(argv)
    root = Path(args.root)
    output = Path(args.out) if args.out else root / "annotated"
    result = annotate_root(root, output, args.sightings_name)
    print(f"wrote {result['annotated_images']} annotated YOLO images to {output}")


if __name__ == "__main__":
    main()
