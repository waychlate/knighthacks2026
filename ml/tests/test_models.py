import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluate import prepare  # noqa: E402
from models import all_models, hit_rate, temporal_split  # noqa: E402
from predict import build_predictions, sample_for_web  # noqa: E402

NOW = datetime(2026, 10, 10, 14, 30, tzinfo=timezone.utc)


def test_temporal_split_has_no_leakage():
    grid = prepare(days=20, seed=3)
    train, test = temporal_split(grid, 3)
    assert train["date"].max() < test["date"].min()
    assert test["date"].nunique() == 3
    assert len(train) + len(test) == len(grid)


def test_probabilities_are_in_unit_interval():
    grid = prepare(days=20, seed=3)
    train, test = temporal_split(grid, 3)
    for m in all_models():
        p = m.fit(train).predict(test)
        assert p.shape == (len(test),) and np.all((p >= 0) & (p <= 1)), m.name


def test_hourly_model_beats_naive_on_hit_rate():
    train, test = temporal_split(prepare(days=42, seed=1), 3)
    naive, hourly = all_models()[:2]
    assert hit_rate(test, hourly.fit(train).predict(test)) > hit_rate(test, naive.fit(train).predict(test))


def test_predictions_schema_and_window():
    rows = build_predictions(NOW, threshold=0.2)
    assert rows
    for r in rows:
        assert set(r) == {"species", "scientific_name", "camera", "predicted_for", "probability"}
        t = datetime.fromisoformat(r["predicted_for"])
        assert t.utcoffset() == timedelta(0) and NOW < t <= NOW + timedelta(hours=24)
        assert 0.2 <= r["probability"] <= 1
    assert build_predictions(NOW, 0.2) == rows  # deterministic


def test_sample_for_web_is_labeled_synthetic_and_relative():
    s = sample_for_web(build_predictions(NOW, 0.05), NOW)
    assert s["synthetic"] is True and "SYNTHETIC" in s["note"]
    assert 3 <= len(s["predictions"]) <= 6
    assert len({p["species"]["scientific_name"] for p in s["predictions"]}) == len(s["predictions"])
    for p in s["predictions"]:
        assert 0 <= p["offset_minutes"] <= 24 * 60 and 0 <= p["probability"] <= 1
        assert p["species"]["common_name"] and p["camera"]["name"]
