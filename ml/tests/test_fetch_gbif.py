import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fetch_gbif import fetch_occurrences


def test_fetch_occurrences_pages_deduplicates_and_records_filters():
    calls = []

    def fake_fetch(url):
        calls.append(url)
        if "/species/match" in url:
            return {"usageKey": 42, "scientificName": "Ursus arctos", "rank": "SPECIES", "status": "ACCEPTED"}
        query = parse_qs(urlparse(url).query)
        offset = int(query["offset"][0])
        if offset == 0:
            return {"count": 3, "endOfRecords": False, "results": [
                {"key": 1, "year": 2024, "month": 6},
                {"key": 2, "year": 2024, "month": 7},
            ]}
        return {"count": 3, "endOfRecords": True, "results": [
            {"key": 2, "year": 2024, "month": 7},
            {"key": 3, "year": 2024, "month": 8},
        ]}

    result = fetch_occurrences(start_year=2020, end_year=2024, max_records=10, fetch=fake_fetch)
    assert result["taxon_match"]["usageKey"] == 42
    assert result["total_available"] == 3
    assert result["records_downloaded"] == 3
    assert result["truncated"] is False
    occurrence_query = parse_qs(urlparse(calls[1]).query)
    assert occurrence_query["year"] == ["2020,2024"]
    assert occurrence_query["has_geospatial_issue"] == ["false"]
    assert occurrence_query["geometry"][0].startswith("POLYGON")
