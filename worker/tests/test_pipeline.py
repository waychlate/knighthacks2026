from types import SimpleNamespace

import pytest

from animal_worker.capture import image_frames
from animal_worker.dedupe import Deduper
from animal_worker.main import StoreSink, is_image_url, process_frame

ELK = SimpleNamespace(common_name="Elk", scientific_name="Cervus canadensis")
BISON = SimpleNamespace(common_name="American bison", scientific_name="Bison bison")


class FakeDetector:
    def __init__(self, n=1):
        self.n = n

    def detect(self, frame):
        return [SimpleNamespace(crop=f"crop{i}") for i in range(self.n)]


class FakeClassifier:
    def __init__(self, *results):
        self.results = list(results)

    def classify(self, crop):
        return self.results.pop(0)


class FakeSink:
    def __init__(self):
        self.rows = []

    def record(self, species, conf, crop, camera):
        self.rows.append((species.common_name, conf, camera))


def run(frame_times, detector, classifier, cooldown=60):
    sink, deduper = FakeSink(), Deduper(cooldown)
    for t in frame_times:
        process_frame(None, t, "cam", detector, classifier, deduper, sink)
    return sink.rows


def test_logs_a_sighting():
    assert run([0], FakeDetector(), FakeClassifier((ELK, 0.9))) == [("Elk", 0.9, "cam")]


def test_no_detections_logs_nothing():
    assert run([0], FakeDetector(0), FakeClassifier()) == []


def test_below_threshold_classification_is_skipped():
    assert run([0], FakeDetector(), FakeClassifier(None)) == []


def test_cooldown_dedupes_same_species():
    rows = run([0, 30, 200], FakeDetector(), FakeClassifier((ELK, 0.9), (ELK, 0.9), (ELK, 0.8)))
    assert [r[1] for r in rows] == [0.9, 0.8]


def test_two_animals_in_one_frame():
    rows = run([0], FakeDetector(2), FakeClassifier((ELK, 0.9), (BISON, 0.8)))
    assert [r[0] for r in rows] == ["Elk", "American bison"]


def test_is_image_url():
    assert is_image_url("https://example.com/cam.jpg?x=1")
    assert not is_image_url("https://example.com/stream.m3u8")
    assert not is_image_url("sample_videos/clip.mp4")


def test_store_sink_tags_source_kind_and_park():
    calls = {}

    class FakeStore:
        def species_id(self, *a):
            return "sp"

        def camera_id(self, name, location, park):
            calls["cam"] = (name, location, park)
            return "cam-id"

        def upload_snapshot(self, crop):
            return "url"

        def insert_sighting(self, **kw):
            calls["row"] = kw

    StoreSink(FakeStore(), "Gardiner", "yellowstone", "live").record(ELK, 0.9, "crop", "Electric Peak")
    assert calls["row"]["source_kind"] == "live"
    assert calls["cam"] == ("Electric Peak", "Gardiner", "yellowstone")


def test_image_frames_skips_unchanged_and_enforces_min_interval():
    responses = [(b"a", "e1"), (None, "e1"), (b"b", "e2")]
    seen_etags, sleeps = [], []

    def fetch(url, etag):
        seen_etags.append(etag)
        return responses.pop(0)

    gen = image_frames("u", every=5, fetch=fetch, decode=lambda d: d.decode(), sleep=sleeps.append, clock=lambda: 1.0)
    assert [next(gen), next(gen)] == [(1.0, "a"), (1.0, "b")]
    assert seen_etags == [None, "e1", "e1"]
    assert set(sleeps) == {30.0}


def test_image_frames_error_propagates():
    def fetch(url, etag):
        raise OSError("boom")

    with pytest.raises(OSError):
        next(image_frames("u", fetch=fetch, sleep=lambda s: None))
