"""Download public iNaturalist observations (mammals + birds) around each park into ml/data/inat/<park>.csv.

    python ml/inat.py [--park yellowstone] [--max-pages 40]

REAL public observations, made by people (not by our cameras). They are never written into `sightings`.
Only research-grade, species-level observations with a plausible time of day are kept (2005 on, not exactly midnight). `local_hour` is the observer's local clock hour.
Bias: observers are tourists, so daytime, roads and trails are over-represented. Polite use of the free API:
one request per second plus a descriptive User-Agent.
"""

import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.inaturalist.org/v1/observations"
UA = "AnimalLogger-KnightHacks2026/0.1 (student hackathon project)"
OUT = Path(__file__).parent / "data" / "inat"

# slug -> (lat, lng, radius km). Centres match web/src/lib/parks.js for the existing parks.
PARKS = {
    "yellowstone": (44.6, -110.5, 60),
    "katmai": (58.5, -155.0, 60),
    "yosemite": (37.85, -119.55, 60),
    "everglades": (25.4, -80.9, 60),
    "grand-canyon": (36.1, -112.1, 60),
    "great-smoky-mountains": (35.6, -83.5, 60),
    "denali": (63.1, -151.2, 60),
}
FIELDS = ["park", "observation_id", "scientific_name", "common_name", "iconic_taxon",
          "observed_at", "local_hour", "lat", "lng", "positional_accuracy"]


def keep(observed_at: str) -> bool:
    """Drop placeholder timestamps: before 2005 (1969-12-31 epoch artefacts etc.) or exactly local midnight (usually a missing time)."""
    return observed_at[:4] >= "2005" and observed_at[11:19] != "00:00:00"


def row(park: str, o: dict) -> dict | None:
    """One CSV row from an API observation, or None if it has no time of day or no species-level taxon."""
    taxon = o.get("taxon") or {}
    if not o.get("time_observed_at") or taxon.get("rank") not in ("species", "subspecies"):
        return None
    if not keep(o["time_observed_at"]):
        return None
    lat, lng = o["location"].split(",")
    return dict(
        park=park, observation_id=o["id"], scientific_name=taxon["name"],
        common_name=taxon.get("preferred_common_name") or "", iconic_taxon=taxon.get("iconic_taxon_name", ""),
        observed_at=o["time_observed_at"], local_hour=o["observed_on_details"]["hour"],
        lat=lat, lng=lng, positional_accuracy=o.get("positional_accuracy") or "",
    )


def fetch(park: str, max_pages: int) -> list[dict]:
    lat, lng, radius = PARKS[park]
    rows, id_below = [], None
    for _ in range(max_pages):
        q = dict(lat=lat, lng=lng, radius=radius, quality_grade="research", iconic_taxa="Mammalia,Aves",
                 per_page=200, order_by="id", order="desc", geoprivacy="open")
        if id_below:
            q["id_below"] = id_below
        req = urllib.request.Request(f"{API}?{urllib.parse.urlencode(q)}", headers={"User-Agent": UA})
        results = json.load(urllib.request.urlopen(req, timeout=30))["results"]
        if not results:
            break
        rows += [r for r in (row(park, o) for o in results) if r]
        id_below = results[-1]["id"]
        time.sleep(1.1)
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--park", choices=list(PARKS), help="one park (default: all)")
    p.add_argument("--max-pages", type=int, default=40, help="200 observations per page")
    a = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for park in [a.park] if a.park else PARKS:
        rows = fetch(park, a.max_pages)
        with open(OUT / f"{park}.csv", "w", newline="") as f:
            w = csv.DictWriter(f, FIELDS)
            w.writeheader()
            w.writerows(rows)
        print(f"{park}: {len(rows)} observations with a time of day")


if __name__ == "__main__":
    main()
