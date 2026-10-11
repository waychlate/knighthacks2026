"""Build daily Katmai weather, daylight, and public-observation features."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ml" / "out"
DEFAULT_GBIF = OUT / "katmai_brown_bear_gbif.json"
DEFAULT_WEATHER = OUT / "katmai_weather_nasa_power.json"
DEFAULT_FEATURES = OUT / "katmai_daily_features.csv"
DEFAULT_METADATA = OUT / "katmai_daily_features.meta.json"
LATITUDE = 58.62235668


def daylight_hours(day: date, latitude: float = LATITUDE) -> float:
    """Approximate sunrise-to-sunset hours from latitude and day of year."""
    day_of_year = day.timetuple().tm_yday
    declination = 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)
    latitude_radians = math.radians(latitude)
    cosine = -math.tan(latitude_radians) * math.tan(declination)
    if cosine <= -1:
        return 24.0
    if cosine >= 1:
        return 0.0
    return 24 * math.acos(cosine) / math.pi


def occurrence_date(row: dict) -> date | None:
    event_date = row.get("eventDate")
    if event_date:
        try:
            return date.fromisoformat(str(event_date)[:10])
        except ValueError:
            pass
    try:
        return date(int(row["year"]), int(row["month"]), int(row["day"]))
    except (KeyError, TypeError, ValueError):
        return None


def build_features(weather_path: Path, gbif_path: Path) -> tuple[list[dict], dict]:
    weather = json.loads(Path(weather_path).read_text(encoding="utf-8"))
    gbif = json.loads(Path(gbif_path).read_text(encoding="utf-8"))
    occurrences = Counter(
        observed.isoformat()
        for row in gbif.get("records", [])
        if (observed := occurrence_date(row)) is not None
    )
    rows = []
    for record in weather.get("records", []):
        day = date.fromisoformat(record["date"])
        rows.append({
            **record,
            "year": day.year,
            "month": day.month,
            "day_of_year": day.timetuple().tm_yday,
            "daylight_hours": round(daylight_hours(day), 3),
            "gbif_bear_records": occurrences.get(record["date"], 0),
            "gbif_observation_day": int(occurrences.get(record["date"], 0) > 0),
        })
    matched = sum(row["gbif_bear_records"] for row in rows)
    metadata = {
        "weather_source": weather.get("source"),
        "weather_source_url": weather.get("source_url"),
        "gbif_source": gbif.get("source"),
        "gbif_source_url": gbif.get("source_url"),
        "location": weather.get("location"),
        "daily_rows": len(rows),
        "gbif_records_with_exact_date": sum(occurrences.values()),
        "gbif_records_matched_to_weather": matched,
        "gbif_observation_days": sum(row["gbif_observation_day"] for row in rows),
        "note": (
            "GBIF counts are opportunistic observation records, not standardized survey effort. "
            "NASA POWER is gridded point data, not an on-camera weather station."
        ),
    }
    return rows, metadata


def write_features(rows: list[dict], metadata: dict, output: Path, metadata_output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else ["date"]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    metadata_output.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weather", type=Path, default=DEFAULT_WEATHER)
    parser.add_argument("--gbif", type=Path, default=DEFAULT_GBIF)
    parser.add_argument("--output", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--metadata-output", type=Path, default=DEFAULT_METADATA)
    args = parser.parse_args(argv)
    rows, metadata = build_features(args.weather, args.gbif)
    write_features(rows, metadata, args.output, args.metadata_output)
    print(f"wrote {len(rows)} daily feature rows to {args.output}")
    print(f"matched {metadata['gbif_records_matched_to_weather']} GBIF records across {metadata['gbif_observation_days']} days")


if __name__ == "__main__":
    main()
