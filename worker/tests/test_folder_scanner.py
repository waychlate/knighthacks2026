import json
from types import SimpleNamespace

import numpy as np

from animal_worker.classifier import Species
from animal_worker.detector import ANIMAL_CLASS_IDS, AnimalDetector, Detection, _animal_class_ids, _iou
from animal_worker.folder_scanner import FolderClassifier, LocalSink, capture_timestamp, load_manifest
from animal_worker.main import process_frame
from animal_worker.dedupe import Deduper


def test_iou_and_nms_remove_overlapping_same_class():
    crop = object()
    strong = Detection(crop, (0, 0, 100, 100), 0.9, 21, "bear")
    duplicate = Detection(crop, (10, 10, 100, 100), 0.7, 21, "bear")
    bird = Detection(crop, (10, 10, 100, 100), 0.8, 14, "bird")
    assert _iou(strong.box, duplicate.box) > 0.5
    assert AnimalDetector._nms([duplicate, strong, bird]) == [strong, bird]


def test_tile_regions_cover_edges_without_duplicate_starts():
    detector = AnimalDetector.__new__(AnimalDetector)
    detector.tile_size = 512
    detector.overlap = 0.2
    regions = detector._tile_regions(1000, 720)
    assert (0, 0, 512, 512) in regions
    assert (488, 208, 1000, 720) in regions
    assert len(regions) == len(set(regions))


def test_class_threshold_can_be_lower_for_birds():
    detector = AnimalDetector.__new__(AnimalDetector)
    detector.min_score = 0.4
    detector.class_min_scores = {"bird": 0.15}
    assert min([detector.min_score, *detector.class_min_scores.values()]) == 0.15


def test_generic_and_custom_models_select_the_right_class_ids():
    coco = {14: "bird", 17: "horse", 19: "cow", 21: "bear"}
    assert _animal_class_ids(coco) == ANIMAL_CLASS_IDS
    assert _animal_class_ids({0: "bear", 1: "bird"}) == [0, 1]


def test_folder_classifier_keeps_bird_species_unidentified_by_default():
    underlying = SimpleNamespace(
        classify=lambda crop: None,
        classify_for_label=lambda crop, label, score: (
            Species("Common merganser", "Mergus merganser", "bird"), 0.99
        ),
    )
    result = FolderClassifier(underlying).classify_for_label("crop", "bird", 0.6)
    assert result[0].common_name == "Bird (unidentified)"
    assert result[1] == 0.6


def test_folder_classifier_can_enable_experimental_bird_species():
    expected = Species("Common merganser", "Mergus merganser", "bird"), 0.99
    underlying = SimpleNamespace(
        classify=lambda crop: None,
        classify_for_label=lambda crop, label, score: expected,
    )
    assert FolderClassifier(underlying, True).classify_for_label("crop", "bird", 0.6) == expected


def test_process_frame_uses_label_aware_classifier():
    detection = SimpleNamespace(crop="crop", label="bear", score=0.91, box=(1, 2, 3, 4))
    detector = SimpleNamespace(detect=lambda frame: [detection])

    class Classifier:
        def classify_for_label(self, crop, label, score):
            assert (crop, label, score) == ("crop", "bear", 0.91)
            return Species("Brown bear", "Ursus arctos", "bear"), score

    class Sink:
        def __init__(self):
            self.saved = None

        def record_detection(self, species, confidence, det, camera, timestamp):
            self.saved = (species.common_name, confidence, det.label, camera, timestamp)

    sink = Sink()
    assert process_frame(None, 10, "cam", detector, Classifier(), Deduper(60), sink) == 1
    assert sink.saved == ("Brown bear", 0.91, "bear", "cam", 10)


def test_manifest_timestamp_and_local_sink(tmp_path):
    manifest = tmp_path / "frames.jsonl"
    manifest.write_text(json.dumps({"file": "a.jpg", "captured_at": "2026-10-10T18:00:00+00:00", "source_kind": "live"}) + "\n")
    image = tmp_path / "a.jpg"
    image.write_bytes(b"x")
    metadata = load_manifest(tmp_path)
    timestamp, iso = capture_timestamp(image, metadata["a.jpg"])
    assert timestamp == 1791655200.0
    assert iso == "2026-10-10T18:00:00+00:00"

    sink = LocalSink("katmai", metadata)
    sink.current_file = "a.jpg"
    sink.current_captured_at = iso
    detection = SimpleNamespace(label="bird", score=0.8, box=(1, 2, 3, 4))
    sink.record_detection(Species("Mew gull", "Larus canus", "bird"), 0.7, detection, "cam", timestamp)
    assert sink.rows[0]["broad_label"] == "bird"
    assert sink.rows[0]["source_kind"] == "live"
