import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from katmai_visualize import build_insights, plot_public_observations


def sample_report():
    return {
        "generated_at": "2026-10-11T00:00:00+00:00",
        "camera_survey": {
            "frames": 20,
            "detection_boxes": 4,
            "cameras": [
                {"camera": "A", "detection_frames_per_100": 10.0, "interval_95_percent": [5.0, 20.0], "by_label": {}},
                {"camera": "B", "detection_frames_per_100": 25.0, "interval_95_percent": [15.0, 38.0], "by_label": {}},
            ],
        },
        "public_observations": {
            "records": 12,
            "dated_records": 12,
            "by_month": {str(month): (8 if month == 8 else 4 if month == 7 else 0) for month in range(1, 13)},
            "source_url": "https://api.gbif.org/v1/occurrence/search",
        },
        "daily_features": {
            "daily_rows": 100,
            "observation_day_weather": {
                "mean_temperature_c": 9.2,
                "mean_daylight_hours": 16.0,
                "mean_precipitation_mm_day": 3.9,
                "mean_relative_humidity_percent": 85.6,
            },
        },
        "limitations": ["Not a population estimate."],
    }


def test_build_insights_selects_highest_camera_and_peak_month():
    insights = build_insights(sample_report())
    assert insights["insights"][0]["value"] == "B"
    assert insights["insights"][1]["value"] == "Aug"
    assert insights["summary"]["public_bear_records"] == 12
    assert len(insights["charts"]) == 3
    assert all(item["caveat"] for item in insights["insights"])


def test_observation_chart_is_valid_svg(tmp_path):
    output = tmp_path / "chart.svg"
    plot_public_observations(sample_report(), output)
    text = output.read_text(encoding="utf-8")
    assert "<svg" in text
    assert "observer access" in text
