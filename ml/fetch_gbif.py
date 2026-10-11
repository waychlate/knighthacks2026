"""Download a reproducible GBIF occurrence sample for Katmai-region analysis."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "ml" / "out" / "katmai_brown_bear_gbif.json"
API = "https://api.gbif.org/v1"
USER_AGENT = "AnimalLogger-KnightHacks/1.0"

# A transparent regional envelope around the NPS-published Katmai centroid.
# It is deliberately described as a region, not the legal park boundary.
REGION = {
    "name": "Katmai regional envelope",
    "nps_centroid": {"latitude": 58.62235668, "longitude": -155.0126574},
    "bounds": {"south": 57.5, "west": -157.0, "north": 59.7, "east": -153.0},
    "geometry_wkt": "POLYGON((-157 57.5,-153 57.5,-153 59.7,-157 59.7,-157 57.5))",
    "note": "Rectangular research envelope; records are not guaranteed to be inside the legal park boundary.",
}

FIELDS = [
    "key", "scientificName", "eventDate", "year", "month", "day",
    "decimalLatitude", "decimalLongitude", "coordinateUncertaintyInMeters",
    "basisOfRecord", "occurrenceStatus", "datasetKey", "datasetTitle",
    "publishingOrgKey", "license", "issues",
]


def request_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_occurrences(
    scientific_name: str = "Ursus arctos",
    start_year: int = 2000,
    end_year: int | None = None,
    max_records: int = 1000,
    fetch=request_json,
) -> dict:
    end_year = end_year or datetime.now(timezone.utc).year
    match_url = f"{API}/species/match?{urlencode({'name': scientific_name})}"
    match = fetch(match_url)
    taxon_key = match.get("usageKey")
    if not taxon_key:
        raise RuntimeError(f"GBIF could not match species name {scientific_name!r}")

    base_filters = {
        "taxon_key": taxon_key,
        "has_coordinate": "true",
        "has_geospatial_issue": "false",
        "occurrence_status": "present",
        "geometry": REGION["geometry_wkt"],
        "year": f"{start_year},{end_year}",
    }
    records = []
    total_available = 0
    offset = 0
    while offset < max_records:
        page_size = min(300, max_records - offset)
        params = {**base_filters, "limit": page_size, "offset": offset}
        page = fetch(f"{API}/occurrence/search?{urlencode(params)}")
        total_available = int(page.get("count", 0))
        results = page.get("results", [])
        records.extend({field: row.get(field) for field in FIELDS} for row in results)
        offset += len(results)
        if not results or page.get("endOfRecords") or offset >= total_available:
            break

    # The API key is a stable occurrence identifier; preserve first-seen order.
    unique = {}
    for row in records:
        unique.setdefault(str(row["key"]), row)
    query_url = f"{API}/occurrence/search?{urlencode(base_filters)}"
    return {
        "source": "GBIF occurrence search API",
        "source_url": query_url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "scientific_name_requested": scientific_name,
        "taxon_match": {
            "usageKey": taxon_key,
            "scientificName": match.get("scientificName"),
            "rank": match.get("rank"),
            "status": match.get("status"),
        },
        "region": REGION,
        "filters": base_filters,
        "total_available": total_available,
        "records_downloaded": len(unique),
        "truncated": len(unique) < total_available,
        "records": list(unique.values()),
        "use_note": (
            "Opportunistic public occurrence records. Counts reflect observer effort, access, "
            "reporting, and data publication as well as animal presence."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--species", default="Ursus arctos")
    parser.add_argument("--start-year", type=int, default=2000)
    parser.add_argument("--end-year", type=int, default=datetime.now(timezone.utc).year)
    parser.add_argument("--max-records", type=int, default=1000)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    data = fetch_occurrences(args.species, args.start_year, args.end_year, args.max_records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {data['records_downloaded']} GBIF records to {args.output}")
    if data["truncated"]:
        print(f"warning: query has {data['total_available']} records; increase --max-records to fetch all")


if __name__ == "__main__":
    main()
