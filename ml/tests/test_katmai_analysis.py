import csv
import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from katmai_analysis import (
    build_report,
    markdown_report,
    summarize_daily_features,
    summarize_public_observations,
    wilson_interval,
)


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_report_adjusts_detections_for_frame_effort(tmp_path):
    captures = tmp_path / "captures"
    camera = captures / "river"
    camera.mkdir(parents=True)
    write_jsonl(camera / "frames.jsonl", [
        {"file": f"{i}.jpg", "camera": "River", "captured_at": f"2026-10-10T12:0{i}:00Z", "source_kind": "live"}
        for i in range(4)
    ])
    (camera / "sightings.json").write_text(json.dumps({"sightings": [
        {"source_file": "0.jpg", "camera": "River", "broad_label": "bear"},
        {"source_file": "0.jpg", "camera": "River", "broad_label": "bear"},
        {"source_file": "1.jpg", "camera": "River", "broad_label": "bird"},
    ]}), encoding="utf-8")

    inventory = tmp_path / "species.csv"
    with inventory.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Category", "Occurrence", "Record Status", "Nativeness", "Abundance"])
        writer.writeheader()
        writer.writerow({"Category": "Mammal", "Occurrence": "Present", "Record Status": "Approved", "Nativeness": "Native", "Abundance": "Common"})
        writer.writerow({"Category": "Bird", "Occurrence": "Present", "Record Status": "Approved", "Nativeness": "Native", "Abundance": "Unknown"})
        writer.writerow({"Category": "Bird", "Occurrence": "Not Present", "Record Status": "Approved"})

    report = build_report(captures, inventory)
    result = report["camera_survey"]["cameras"][0]
    assert result["frames"] == 4
    assert result["detection_boxes"] == 3
    assert result["frames_with_detection"] == 2
    assert result["detection_frames_per_100"] == 50.0
    assert result["by_label"]["bear"]["frames"] == 1
    assert report["nps_inventory"]["approved_present_species"] == 2
    assert report["nps_inventory"]["by_category"] == {"Bird": 1, "Mammal": 1}
    assert "population" in markdown_report(report).lower()


def test_wilson_interval_handles_empty_and_small_samples():
    assert wilson_interval(0, 0) == [0.0, 0.0]
    low, high = wilson_interval(1, 10)
    assert 0 < low < 10 < high < 100


def test_public_observations_are_summarized_without_population_claims(tmp_path):
    source = tmp_path / "gbif.json"
    source.write_text(json.dumps({
        "source": "GBIF occurrence search API",
        "source_url": "https://api.gbif.org/v1/occurrence/search",
        "retrieved_at": "2026-10-10T00:00:00+00:00",
        "region": {"name": "Katmai regional envelope"},
        "taxon_match": {"scientificName": "Ursus arctos"},
        "truncated": False,
        "records": [
            {"key": 1, "year": 2024, "month": 7, "basisOfRecord": "HUMAN_OBSERVATION", "datasetKey": "a", "license": "CC_BY_4_0", "coordinateUncertaintyInMeters": 20},
            {"key": 2, "year": 2025, "month": 7, "basisOfRecord": "HUMAN_OBSERVATION", "datasetKey": "b", "license": "CC_BY_4_0", "coordinateUncertaintyInMeters": 40},
            {"key": 2, "year": 2025, "month": 7},
        ],
    }), encoding="utf-8")
    summary = summarize_public_observations(source)
    assert summary["records"] == 2
    assert summary["by_month"]["7"] == 2
    assert summary["first_year"] == 2024
    assert summary["last_year"] == 2025
    assert summary["median_coordinate_uncertainty_m"] == 30.0


def test_daily_features_summarize_weather_and_observation_days(tmp_path):
    source = tmp_path / "features.csv"
    source.write_text(
        "date,year,month,temperature_c,precipitation_mm,relative_humidity_percent,daylight_hours,gbif_bear_records,gbif_observation_day\n"
        "2024-07-01,2024,7,10,2,80,18.5,2,1\n"
        "2024-07-02,2024,7,12,0,70,18.4,0,0\n"
        "2024-08-01,2024,8,8,4,90,15.5,1,1\n",
        encoding="utf-8",
    )
    summary = summarize_daily_features(source)
    assert summary["daily_rows"] == 3
    assert summary["gbif_records_matched"] == 3
    assert summary["gbif_observation_days"] == 2
    assert summary["by_month"]["7"]["mean_temperature_c"] == 11.0
    assert summary["by_month"]["7"]["mean_precipitation_mm_day"] == 1.0
    assert summary["observation_day_weather"]["mean_temperature_c"] == 9.0
