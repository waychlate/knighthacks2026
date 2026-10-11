import json
from pathlib import Path

from PIL import Image

from animal_worker.katmai_training import export_dataset, initialize_review


def _camera(root: Path):
    camera = root / "cam"
    camera.mkdir(parents=True)
    Image.new("RGB", (100, 50), "green").save(camera / "20261010T120000Z.jpg")
    Image.new("RGB", (100, 50), "blue").save(camera / "20261010T121000Z.jpg")
    data = {"sightings": [{
        "source_file": "20261010T120000Z.jpg", "broad_label": "horse",
        "detector_confidence": 0.7, "box": [10, 5, 50, 25],
    }]}
    (camera / "sightings.json").write_text(json.dumps(data), encoding="utf-8")


def test_review_preserves_decisions_and_suggests_bear(tmp_path):
    root, review, crops = tmp_path / "frames", tmp_path / "review.json", tmp_path / "crops"
    _camera(root)
    result = initialize_review(root, review, crops)
    item = result["detections"][0]
    assert item["label"] == "bear"
    assert item["status"] == "pending"
    assert (crops / f"{item['id']}.jpg").is_file()
    item["status"] = "accepted"
    review.write_text(json.dumps(result), encoding="utf-8")
    assert initialize_review(root, review, crops)["detections"][0]["status"] == "accepted"


def test_export_writes_yolo_labels_and_negative_frame(tmp_path):
    root, review, crops = tmp_path / "frames", tmp_path / "review.json", tmp_path / "crops"
    _camera(root)
    data = initialize_review(root, review, crops)
    data["detections"][0]["status"] = "accepted"
    review.write_text(json.dumps(data), encoding="utf-8")
    output = tmp_path / "dataset"
    summary = export_dataset(root, review, output)
    assert sum(summary["exported_images"].values()) == 2
    labels = list((output / "labels").rglob("*.txt"))
    assert len(labels) == 2
    assert any(path.read_text().startswith("0 0.300000 0.300000 0.400000 0.400000") for path in labels)
    assert (output / "dataset.yaml").is_file()
