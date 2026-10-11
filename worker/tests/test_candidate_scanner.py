import json
from types import SimpleNamespace

import numpy as np

from animal_worker.candidate_scanner import scan_camera


def test_scan_camera_records_every_detection(monkeypatch, tmp_path):
    camera = tmp_path / "cam"
    camera.mkdir()
    for name in ("a.jpg", "b.jpg"):
        (camera / name).write_bytes(b"image")
    monkeypatch.setitem(__import__("sys").modules, "cv2", SimpleNamespace(imread=lambda _path: np.zeros((10, 10, 3))))
    detection = SimpleNamespace(label="bear", score=0.8, box=(1, 2, 8, 9))
    result = scan_camera(camera, "training_candidates.json", SimpleNamespace(detect=lambda _frame: [detection]))
    saved = json.loads((camera / "training_candidates.json").read_text())
    assert result["frames_scanned"] == 2
    assert len(saved["sightings"]) == 2
    assert saved["sightings"][0]["broad_label"] == "bear"
