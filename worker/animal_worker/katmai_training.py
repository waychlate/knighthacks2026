"""Prepare reviewed Katmai camera detections for custom YOLO training.

The review manifest is deliberately separate from YOLO's predictions: training
must not silently treat a model's guesses as ground truth.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CLASSES = ("bear", "bird")
BEAR_LIKE_COCO_LABELS = {"bear", "cow", "horse", "sheep", "elephant", "dog", "giraffe"}


def _detection_id(camera: str, source_file: str, box: list[int]) -> str:
    value = f"{camera}|{source_file}|{','.join(map(str, box))}"
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def initialize_review(root: Path, review_path: Path, crops_dir: Path,
                      source_name: str = "sightings.json") -> dict:
    """Create or refresh a review manifest while preserving human decisions."""
    root, review_path, crops_dir = Path(root), Path(review_path), Path(crops_dir)
    previous = {}
    if review_path.is_file():
        old = json.loads(review_path.read_text(encoding="utf-8"))
        previous = {item["id"]: item for item in old.get("detections", [])}

    detections = []
    crops_dir.mkdir(parents=True, exist_ok=True)
    for camera_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        sightings_path = camera_dir / source_name
        if not sightings_path.is_file():
            continue
        data = json.loads(sightings_path.read_text(encoding="utf-8"))
        for row in data.get("sightings", []):
            box = [int(value) for value in row["box"]]
            item_id = _detection_id(camera_dir.name, row["source_file"], box)
            old = previous.get(item_id, {})
            original = row["broad_label"]
            suggested = "bear" if original in BEAR_LIKE_COCO_LABELS else "bird"
            item = {
                "id": item_id,
                "camera": camera_dir.name,
                "source_file": row["source_file"],
                "box": box,
                "original_label": original,
                "detector_confidence": row["detector_confidence"],
                "label": old.get("label", suggested),
                "status": old.get("status", "pending"),
            }
            source = camera_dir / row["source_file"]
            if source.is_file():
                with Image.open(source) as image:
                    image = image.convert("RGB")
                    margin = max(12, round(max(box[2] - box[0], box[3] - box[1]) * 0.25))
                    crop_box = (
                        max(0, box[0] - margin), max(0, box[1] - margin),
                        min(image.width, box[2] + margin), min(image.height, box[3] + margin),
                    )
                    crop = image.crop(crop_box)
                    draw = ImageDraw.Draw(crop)
                    relative = (
                        box[0] - crop_box[0], box[1] - crop_box[1],
                        box[2] - crop_box[0], box[3] - crop_box[1],
                    )
                    draw.rectangle(relative, outline="#ff3030", width=max(2, min(crop.size) // 100))
                    draw.text((4, 4), f"{item_id}  YOLO: {original}", fill="white",
                              stroke_width=2, stroke_fill="black", font=ImageFont.load_default())
                    crop.save(crops_dir / f"{item_id}.jpg", quality=94)
            detections.append(item)

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "instructions": "Set status to accepted or rejected. Accepted rows require label bear or bird.",
        "classes": list(CLASSES),
        "detections": detections,
    }
    review_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def review_interactively(root: Path, review_path: Path, crops_dir: Path):
    """Open a small keyboard-driven reviewer and save each decision immediately."""
    import tkinter as tk
    from tkinter import messagebox

    from PIL import ImageTk

    root, review_path, crops_dir = Path(root), Path(review_path), Path(crops_dir)
    if not review_path.is_file():
        initialize_review(root, review_path, crops_dir)
    data = json.loads(review_path.read_text(encoding="utf-8"))
    items = data["detections"]
    pending = [index for index, item in enumerate(items) if item["status"] == "pending"]
    position = 0

    window = tk.Tk()
    window.title("Katmai YOLO label review")
    window.geometry("1000x760")
    heading = tk.Label(window, font=("Segoe UI", 13), justify="left")
    heading.pack(padx=12, pady=8, anchor="w")
    image_label = tk.Label(window)
    image_label.pack(expand=True, fill="both", padx=12, pady=8)
    help_label = tk.Label(
        window,
        text="B = bear    I = bird    X = reject false detection    U = undo previous    Q = save and close",
        font=("Segoe UI", 11),
    )
    help_label.pack(padx=12, pady=8)

    def save():
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        review_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def show():
        nonlocal position
        if position >= len(pending):
            save()
            messagebox.showinfo("Review complete", "Every candidate has been reviewed.")
            window.destroy()
            return
        item = items[pending[position]]
        image = Image.open(crops_dir / f"{item['id']}.jpg").convert("RGB")
        image.thumbnail((940, 610), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        image_label.configure(image=photo)
        image_label.image = photo
        heading.configure(text=(
            f"{position + 1} of {len(pending)} pending | {item['camera']} | {item['source_file']}\n"
            f"YOLO said {item['original_label']} ({float(item['detector_confidence']):.0%}); "
            f"suggestion: {item['label']}"
        ))

    def decide(label: str | None):
        nonlocal position
        if position >= len(pending):
            return
        item = items[pending[position]]
        item["status"] = "accepted" if label else "rejected"
        if label:
            item["label"] = label
        save()
        position += 1
        show()

    def undo():
        nonlocal position
        if position == 0:
            return
        position -= 1
        items[pending[position]]["status"] = "pending"
        save()
        show()

    buttons = tk.Frame(window)
    buttons.pack(pady=6)
    tk.Button(buttons, text="Bear (B)", width=18, command=lambda: decide("bear")).pack(side="left", padx=5)
    tk.Button(buttons, text="Bird (I)", width=18, command=lambda: decide("bird")).pack(side="left", padx=5)
    tk.Button(buttons, text="False / Branch (X)", width=18, command=lambda: decide(None)).pack(side="left", padx=5)
    tk.Button(buttons, text="Undo (U)", width=12, command=undo).pack(side="left", padx=5)
    window.bind("<b>", lambda _event: decide("bear"))
    window.bind("<i>", lambda _event: decide("bird"))
    window.bind("<x>", lambda _event: decide(None))
    window.bind("<u>", lambda _event: undo())
    window.bind("<q>", lambda _event: (save(), window.destroy()))
    window.protocol("WM_DELETE_WINDOW", lambda: (save(), window.destroy()))
    show()
    window.mainloop()


def _split(camera: str, source_file: str) -> str:
    # Keep nearby frames together to reduce leakage from near-identical webcam images.
    time_block = source_file[:12]
    bucket = int(hashlib.sha1(f"{camera}|{time_block}".encode()).hexdigest()[:8], 16) % 100
    return "train" if bucket < 70 else "val" if bucket < 85 else "test"


def _yolo_line(label: str, box: list[int], width: int, height: int) -> str:
    class_id = CLASSES.index(label)
    x1, y1, x2, y2 = box
    x_center = ((x1 + x2) / 2) / width
    y_center = ((y1 + y2) / 2) / height
    box_width = (x2 - x1) / width
    box_height = (y2 - y1) / height
    return f"{class_id} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}"


def export_dataset(root: Path, review_path: Path, output: Path,
                   negatives_per_camera: int = 40) -> dict:
    """Export reviewed detections and scenery negatives in YOLO format."""
    root, review_path, output = Path(root), Path(review_path), Path(output)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    by_frame = defaultdict(list)
    for item in review.get("detections", []):
        by_frame[(item["camera"], item["source_file"])].append(item)

    if output.exists():
        shutil.rmtree(output)
    for split in ("train", "val", "test"):
        (output / "images" / split).mkdir(parents=True, exist_ok=True)
        (output / "labels" / split).mkdir(parents=True, exist_ok=True)

    exported = defaultdict(int)
    skipped_pending = 0
    for (camera, source_file), items in sorted(by_frame.items()):
        if any(item["status"] == "pending" for item in items):
            skipped_pending += 1
            continue
        accepted = [item for item in items if item["status"] == "accepted"]
        for item in accepted:
            if item["label"] not in CLASSES:
                raise ValueError(f"Invalid label {item['label']!r} for {item['id']}")
        _export_frame(root, output, camera, source_file, accepted)
        exported[_split(camera, source_file)] += 1

    # Frames with no candidate detections teach the model that water, rocks, and
    # branches are background. Limit them so negatives do not swamp positives.
    for camera_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        candidates = []
        for source in sorted(camera_dir.glob("*.jpg")):
            if (camera_dir.name, source.name) not in by_frame:
                candidates.append(source)
        if negatives_per_camera and len(candidates) > negatives_per_camera:
            step = len(candidates) / negatives_per_camera
            candidates = [candidates[int(i * step)] for i in range(negatives_per_camera)]
        for source in candidates:
            _export_frame(root, output, camera_dir.name, source.name, [])
            exported[_split(camera_dir.name, source.name)] += 1

    yaml = (
        f"path: {output.resolve().as_posix()}\n"
        "train: images/train\nval: images/val\ntest: images/test\n"
        "names:\n  0: bear\n  1: bird\n"
    )
    (output / "dataset.yaml").write_text(yaml, encoding="utf-8")
    summary = {
        "exported_images": dict(exported),
        "skipped_frames_with_pending_reviews": skipped_pending,
        "pending_detections": sum(item["status"] == "pending" for item in review["detections"]),
        "accepted_detections": sum(item["status"] == "accepted" for item in review["detections"]),
        "rejected_detections": sum(item["status"] == "rejected" for item in review["detections"]),
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def restore_review_from_export(root: Path, review_path: Path, dataset: Path,
                               source_name: str = "sightings.json") -> dict:
    """Restore prior decisions from an exported dataset after expanding candidates."""
    root, review_path, dataset = Path(root), Path(review_path), Path(dataset)
    data = json.loads(review_path.read_text(encoding="utf-8"))
    current = {item["id"]: item for item in data["detections"]}
    restored = 0
    for camera_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        source_json = camera_dir / source_name
        if not source_json.is_file():
            continue
        old_rows = json.loads(source_json.read_text(encoding="utf-8")).get("sightings", [])
        for row in old_rows:
            box = [int(value) for value in row["box"]]
            item = current.get(_detection_id(camera_dir.name, row["source_file"], box))
            if not item or item["status"] != "pending":
                continue
            label_name = f"{camera_dir.name}__{Path(row['source_file']).stem}.txt"
            matches = list((dataset / "labels").rglob(label_name))
            if not matches:
                continue
            with Image.open(camera_dir / row["source_file"]) as image:
                expected_tail = _yolo_line("bear", box, image.width, image.height).split(" ", 1)[1]
            accepted_label = None
            for line in matches[0].read_text(encoding="utf-8").splitlines():
                class_id, coordinates = line.split(" ", 1)
                if coordinates == expected_tail:
                    accepted_label = CLASSES[int(class_id)]
                    break
            item["status"] = "accepted" if accepted_label else "rejected"
            if accepted_label:
                item["label"] = accepted_label
            restored += 1
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    review_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {"restored": restored}


def _export_frame(root: Path, output: Path, camera: str, source_file: str, items: list[dict]):
    source = root / camera / source_file
    if not source.is_file():
        return
    split = _split(camera, source_file)
    destination_name = f"{camera}__{source_file}"
    shutil.copy2(source, output / "images" / split / destination_name)
    with Image.open(source) as image:
        lines = [_yolo_line(item["label"], item["box"], image.width, image.height) for item in items]
    label_name = f"{Path(destination_name).stem}.txt"
    (output / "labels" / split / label_name).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def train(dataset_yaml: Path, base_weights: str, epochs: int, image_size: int,
          project: Path, name: str):
    from ultralytics import YOLO

    model = YOLO(base_weights)
    return model.train(data=str(Path(dataset_yaml).resolve()), epochs=epochs, imgsz=image_size,
                       project=str(Path(project).resolve()), name=name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="create review.json and boxed detection crops")
    init.add_argument("--root", default="sample_videos/katmai")
    init.add_argument("--review", default="training/katmai/review.json")
    init.add_argument("--crops", default="training/katmai/review-crops")
    init.add_argument("--source-name", default="sightings.json")
    export = sub.add_parser("export", help="export reviewed labels as a YOLO dataset")
    export.add_argument("--root", default="sample_videos/katmai")
    export.add_argument("--review", default="training/katmai/review.json")
    export.add_argument("--out", default="training/katmai/dataset")
    export.add_argument("--negatives-per-camera", type=int, default=40)
    review = sub.add_parser("review", help="review candidates with B/I/X keyboard controls")
    review.add_argument("--root", default="sample_videos/katmai")
    review.add_argument("--review", default="training/katmai/review.json")
    review.add_argument("--crops", default="training/katmai/review-crops")
    restore = sub.add_parser("restore-export", help="restore decisions from the last exported dataset")
    restore.add_argument("--root", default="sample_videos/katmai")
    restore.add_argument("--review", default="training/katmai/review.json")
    restore.add_argument("--dataset", default="training/katmai/dataset")
    restore.add_argument("--source-name", default="sightings.json")
    fit = sub.add_parser("train", help="fine-tune YOLO after review and export")
    fit.add_argument("--data", default="training/katmai/dataset/dataset.yaml")
    fit.add_argument("--weights", default="yolov8n.pt")
    fit.add_argument("--epochs", type=int, default=50)
    fit.add_argument("--image-size", type=int, default=640)
    fit.add_argument("--project", default="training/katmai/runs")
    fit.add_argument("--name", default="bear-bird-v1")
    args = parser.parse_args(argv)

    if args.command == "init":
        result = initialize_review(Path(args.root), Path(args.review), Path(args.crops), args.source_name)
        print(f"wrote {len(result['detections'])} candidates to {args.review}")
    elif args.command == "review":
        review_interactively(Path(args.root), Path(args.review), Path(args.crops))
    elif args.command == "restore-export":
        result = restore_review_from_export(
            Path(args.root), Path(args.review), Path(args.dataset), args.source_name,
        )
        print(f"restored {result['restored']} prior decisions")
    elif args.command == "export":
        result = export_dataset(Path(args.root), Path(args.review), Path(args.out), args.negatives_per_camera)
        print(json.dumps(result, indent=2))
    else:
        train(Path(args.data), args.weights, args.epochs, args.image_size, Path(args.project), args.name)


if __name__ == "__main__":
    main()
