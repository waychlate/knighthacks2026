"""SYNTHETIC sighting generator. Everything this produces is fake, made up for the demo.

Each species has a known time-of-day profile (peaks in park-local hours), a camera
preference and a weekday/weekend effect. The profiles are deliberately exposed so the
models in this folder can be checked against the truth they should recover.

Real sightings come from the worker, not from here. Never present this data as real.
"""

from __future__ import annotations

import csv
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

PARK_TZ = ZoneInfo("America/Denver")  # Yellowstone
ROOT = Path(__file__).resolve().parents[1]

# (name, location, is_real). Only Electric Peak is a real camera; the others are demo-only.
CAMERAS = [
    ("Electric Peak Cam", "North Entrance, Gardiner", True),
    ("Lamar Valley Demo Cam", "Lamar Valley (demo camera)", False),
    ("Hayden Valley Demo Cam", "Hayden Valley (demo camera)", False),
]

# species -> daily sightings per unit camera weight, time-of-day peaks as (local hour, sd hours, weight),
# camera weights, and a weekend multiplier (shy animals are seen less when the park is busy).
PROFILES: dict[str, dict] = {
    "Cervus canadensis": dict(rate=2.5, peaks=[(6.5, 1.2, 0.5), (18.5, 1.5, 0.5)], cams=[1.0, 0.4, 0.8], weekend=1.0),
    "Bison bison": dict(rate=3.0, peaks=[(10.0, 2.5, 0.5), (15.5, 2.5, 0.5)], cams=[0.6, 1.0, 1.0], weekend=1.0),
    "Antilocapra americana": dict(rate=1.6, peaks=[(8.0, 1.5, 0.5), (17.0, 1.5, 0.5)], cams=[1.0, 0.3, 0.2], weekend=1.0),
    "Odocoileus hemionus": dict(rate=1.4, peaks=[(6.0, 1.0, 0.5), (19.0, 1.2, 0.5)], cams=[0.9, 0.2, 0.3], weekend=0.9),
    "Canis latrans": dict(rate=0.9, peaks=[(5.5, 1.0, 0.5), (20.0, 1.2, 0.5)], cams=[0.3, 1.0, 0.5], weekend=0.8),
    "Canis lupus": dict(rate=0.5, peaks=[(6.0, 0.8, 0.5), (19.5, 1.0, 0.5)], cams=[0.0, 1.0, 0.3], weekend=0.7),
    "Ursus arctos horribilis": dict(rate=0.5, peaks=[(7.0, 1.2, 0.5), (18.0, 1.5, 0.5)], cams=[0.1, 0.8, 1.0], weekend=0.7),
    "Ursus americanus": dict(rate=0.4, peaks=[(8.0, 1.5, 0.5), (17.5, 1.5, 0.5)], cams=[0.5, 0.3, 0.2], weekend=0.7),
    "Ovis canadensis": dict(rate=0.6, peaks=[(11.0, 2.0, 1.0)], cams=[0.2, 0.2, 0.0], weekend=1.0),
    "Alces alces": dict(rate=0.5, peaks=[(6.5, 1.2, 0.5), (19.0, 1.2, 0.5)], cams=[0.0, 0.3, 1.0], weekend=0.8),
    "Haliaeetus leucocephalus": dict(rate=0.8, peaks=[(10.0, 2.5, 1.0)], cams=[0.4, 0.4, 0.8], weekend=1.0),
    "Cygnus buccinator": dict(rate=0.6, peaks=[(9.0, 2.0, 1.0)], cams=[0.0, 0.1, 1.0], weekend=1.0),
    "Antigone canadensis": dict(rate=0.7, peaks=[(7.5, 1.5, 1.0)], cams=[0.1, 0.2, 1.0], weekend=1.0),
    "Vulpes vulpes": dict(rate=0.4, peaks=[(5.0, 1.0, 0.5), (20.5, 1.2, 0.5)], cams=[0.4, 0.4, 0.2], weekend=0.8),
}


def hourly_profile(scientific_name: str, profiles: dict | None = None) -> np.ndarray:
    """True probability (sums to 1) that a sighting of this species falls in each local hour 0-23."""
    hours = np.arange(24) + 0.5
    dens = np.zeros(24)
    for mu, sd, w in (PROFILES if profiles is None else profiles)[scientific_name]["peaks"]:
        d = np.minimum(np.abs(hours - mu), 24 - np.abs(hours - mu))  # circular distance
        dens += w * np.exp(-0.5 * (d / sd) ** 2)
    return dens / dens.sum()


def generate(end: datetime, days: int = 14, seed: int = 42, *,
             profiles: dict | None = None, cameras: list | None = None,
             park_tz: ZoneInfo = PARK_TZ) -> list[dict]:
    """Return synthetic sightings for the `days` days before `end` (UTC), sorted by time.

    Same (end, days, seed) always gives the same rows. Rows are dicts with
    species (scientific name), camera, seen_at (UTC ISO 8601) and confidence.
    """
    rng = np.random.default_rng(seed)
    end = end.astimezone(timezone.utc)
    profiles = PROFILES if profiles is None else profiles
    cameras = CAMERAS if cameras is None else cameras
    first_day = (end - timedelta(days=days)).astimezone(park_tz).date()
    rows = []
    for sci, prof in profiles.items():
        hp = hourly_profile(sci, profiles)
        for ci, (cam, _loc, _real) in enumerate(cameras):
            for d in range(days + 1):
                day = first_day + timedelta(days=d)
                mult = prof["weekend"] if day.weekday() >= 5 else 1.0
                for _ in range(rng.poisson(prof["rate"] * prof["cams"][ci] * mult)):
                    hour = int(rng.choice(24, p=hp))
                    local = datetime(day.year, day.month, day.day, hour, int(rng.integers(60)), int(rng.integers(60)), tzinfo=park_tz)
                    seen = local.astimezone(timezone.utc)
                    if end - timedelta(days=days) <= seen < end:
                        conf = float(np.clip(rng.beta(8, 2), 0.5, 0.99))
                        rows.append(dict(species=sci, camera=cam, seen_at=seen.isoformat(), confidence=round(conf, 3)))
    rows.sort(key=lambda r: (r["seen_at"], r["species"], r["camera"]))
    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        f.write("# SYNTHETIC DATA: generated by ml/synthetic.py, not real sightings\n")
        w = csv.DictWriter(f, fieldnames=["species", "camera", "seen_at", "confidence"])
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    out = Path(__file__).parent / "out" / "synthetic_sightings.csv"
    data = generate(now)
    write_csv(data, out)
    print(f"wrote {len(data)} SYNTHETIC sightings to {out}")
    assert math.isclose(sum(hourly_profile("Cervus canadensis")), 1.0)
