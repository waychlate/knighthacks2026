import json
from pathlib import Path
from types import SimpleNamespace

from animal_worker.katmai_live import (
    KatmaiLabelClassifier,
    LiveFrameProcessor,
    LiveSightingSink,
    enqueue_latest,
)


def metadata(camera="Brooks Falls Low Cam"):
    return {
        "camera": camera,
        "captured_at": "2026-10-11T12:34:56+00:00",
        "source_kind": "live",
    }


class FakeStore:
    def __init__(self):
        self.row = None

    def species_id(self, common, scientific):
        assert (common, scientific) == ("Brown bear", "Ursus arctos")
        return "species-id"

    def camera_id(self, name, location, park):
        assert name == "Brooks Falls Low Cam"
        assert location == "Brooks Falls Platform, Brooks Camp"
        assert park == "katmai"
        return "camera-id"

    def upload_snapshot(self, crop):
        assert crop == "bear-crop"
        return "https://example.test/bear.jpg"

    def insert_sighting(self, **row):
        self.row = row


def test_label_classifier_uses_safe_broad_taxa():
    classifier = KatmaiLabelClassifier()
    bear, bear_score = classifier.classify_for_label(None, "bear", 0.91)
    bird, bird_score = classifier.classify_for_label(None, "bird", 0.62)

    assert (bear.common_name, bear.scientific_name, bear_score) == ("Brown bear", "Ursus arctos", 0.91)
    assert (bird.common_name, bird.scientific_name, bird_score) == ("Bird (unidentified)", "Aves", 0.62)
    assert classifier.classify_for_label(None, "cow", 0.9) is None


def test_live_processor_writes_audit_and_publishes_capture_time(tmp_path):
    detection = SimpleNamespace(
        crop="bear-crop", label="bear", score=0.91, box=(10, 20, 100, 120),
    )
    detector = SimpleNamespace(detect=lambda frame: [detection])
    store = FakeStore()
    output = tmp_path / "live_sightings.jsonl"
    processor = LiveFrameProcessor(detector, LiveSightingSink(output, store=store))

    assert processor.process("frame", metadata(), Path("frame.jpg")) == 1

    audit = json.loads(output.read_text(encoding="utf-8"))
    assert audit["published"] is True
    assert audit["common_name"] == "Brown bear"
    assert audit["source_kind"] == "live"
    assert store.row == {
        "species_id": "species-id",
        "camera_id": "camera-id",
        "confidence": 0.91,
        "snapshot_url": "https://example.test/bear.jpg",
        "source_kind": "live",
        "seen_at": "2026-10-11T12:34:56+00:00",
    }


def test_live_processor_deduplicates_same_camera_and_species(tmp_path):
    detection = SimpleNamespace(crop="bird", label="bird", score=0.8, box=(1, 2, 3, 4))
    detector = SimpleNamespace(detect=lambda frame: [detection])
    output = tmp_path / "live_sightings.jsonl"
    processor = LiveFrameProcessor(detector, LiveSightingSink(output), cooldown=120)

    first = metadata("River Watch Cam")
    second = {**first, "captured_at": "2026-10-11T12:35:30+00:00"}
    assert processor.process("frame", first, Path("one.jpg")) == 1
    assert processor.process("frame", second, Path("two.jpg")) == 0
    assert len(output.read_text(encoding="utf-8").splitlines()) == 1


def test_full_queue_discards_oldest_frame():
    import queue

    work = queue.Queue(maxsize=1)
    work.put("old")
    messages = []
    enqueue_latest(work, "new", log_message=messages.append)

    assert work.get_nowait() == "new"
    assert messages == ["Detector is behind; dropped the oldest queued frame"]
