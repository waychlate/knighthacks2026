import json
import sys
from datetime import date
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from katmai_features import build_features, daylight_hours, occurrence_date


def test_daylight_is_longer_in_katmai_summer_than_winter():
    assert daylight_hours(date(2024, 6, 21)) > 18
    assert daylight_hours(date(2024, 12, 21)) < 7


def test_occurrence_date_falls_back_to_date_parts():
    assert occurrence_date({"eventDate": "2024-07-04T12:00:00", "year": 2020}) == date(2024, 7, 4)
    assert occurrence_date({"year": 2023, "month": 8, "day": 9}) == date(2023, 8, 9)
    assert occurrence_date({"year": 2023, "month": 8}) is None


def test_build_features_joins_weather_and_occurrence_counts(tmp_path):
    weather = tmp_path / "weather.json"
    gbif = tmp_path / "gbif.json"
    weather.write_text(json.dumps({
        "source": "NASA POWER Daily API",
        "source_url": "https://power.example",
        "location": {"latitude": 58.6, "longitude": -155.0},
        "records": [
            {"date": "2024-07-01", "temperature_c": 10.0, "precipitation_mm": 1.0},
            {"date": "2024-07-02", "temperature_c": 11.0, "precipitation_mm": 0.0},
        ],
    }), encoding="utf-8")
    gbif.write_text(json.dumps({
        "source": "GBIF occurrence search API",
        "source_url": "https://gbif.example",
        "records": [
            {"key": 1, "eventDate": "2024-07-01T10:00:00"},
            {"key": 2, "year": 2024, "month": 7, "day": 1},
            {"key": 3, "year": 2024, "month": 7},
        ],
    }), encoding="utf-8")
    rows, metadata = build_features(weather, gbif)
    assert rows[0]["gbif_bear_records"] == 2
    assert rows[0]["gbif_observation_day"] == 1
    assert rows[1]["gbif_bear_records"] == 0
    assert metadata["gbif_records_with_exact_date"] == 2
    assert metadata["gbif_records_matched_to_weather"] == 2
    assert metadata["gbif_observation_days"] == 1
