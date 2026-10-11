import json

from PIL import Image

from animal_worker.annotate_sightings import annotate_root


def test_annotates_sighting_frames_into_camera_directories(tmp_path):
    root = tmp_path / "katmai"
    camera = root / "river-watch"
    camera.mkdir(parents=True)
    Image.new("RGB", (100, 80), "white").save(camera / "frame.jpg")
    (camera / "sightings.json").write_text(json.dumps({
        "model": "training/katmai/current.pt",
        "thresholds": {"bear": 0.7, "bird": 0.4},
        "sightings": [{
            "source_file": "frame.jpg",
            "broad_label": "bear",
            "detector_confidence": 0.91,
            "box": [10, 10, 60, 60],
        }],
    }), encoding="utf-8")

    output = tmp_path / "annotated"
    result = annotate_root(root, output)

    annotated = output / "river-watch" / "frame_annotated.jpg"
    assert annotated.is_file()
    assert result["model"] == "training/katmai/current.pt"
    assert result["annotated_images"] == 1
    index = json.loads((output / "index.json").read_text(encoding="utf-8"))
    assert index["cameras"][0]["camera"] == "river-watch"
    assert index["cameras"][0]["thresholds"]["bear"] == 0.7


def test_removes_stale_annotations_from_previous_scan(tmp_path):
    root = tmp_path / "katmai"
    camera = root / "river-watch"
    camera.mkdir(parents=True)
    (camera / "sightings.json").write_text(json.dumps({"sightings": []}), encoding="utf-8")
    output = tmp_path / "annotated"
    old = output / "river-watch" / "old_annotated.jpg"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"stale")

    annotate_root(root, output)

    assert not old.exists()
