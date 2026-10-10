from animal_worker.dedupe import Deduper


def test_first_sighting_is_logged():
    assert Deduper(60).should_log("cam", "deer", 0)


def test_repeat_within_cooldown_is_skipped():
    d = Deduper(60)
    assert d.should_log("cam", "deer", 0)
    assert not d.should_log("cam", "deer", 30)


def test_animal_staying_in_frame_extends_cooldown():
    d = Deduper(60)
    assert d.should_log("cam", "deer", 0)
    for t in range(10, 300, 10):  # visible the whole time, never gone for >60s
        assert not d.should_log("cam", "deer", t)


def test_logged_again_after_cooldown():
    d = Deduper(60)
    assert d.should_log("cam", "deer", 0)
    assert d.should_log("cam", "deer", 100)


def test_different_species_or_camera_independent():
    d = Deduper(60)
    assert d.should_log("cam1", "deer", 0)
    assert d.should_log("cam1", "bear", 1)
    assert d.should_log("cam2", "deer", 2)
