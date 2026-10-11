"""Park settings for local SYNTHETIC forecasts. URLs are references, never fetched here."""

import json
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from synthetic import CAMERAS, PARK_TZ, PROFILES, ROOT


def _katmai_cameras():
    path = ROOT / "config" / "katmai_cameras.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return [(row["name"], row["location"], True) for row in data["cameras"]]


@dataclass(frozen=True)
class ParkConfig:
    slug: str
    timezone: ZoneInfo
    cameras: list
    profiles: dict
    species_file: Path
    source_url: str | None = None


PARKS = {
    "yellowstone": ParkConfig("yellowstone", PARK_TZ, CAMERAS, PROFILES,
                             ROOT / "worker" / "species.json"),
    "katmai": ParkConfig(
        slug="katmai",
        timezone=ZoneInfo("America/Anchorage"),
        cameras=_katmai_cameras(),
        # Arbitrary demo assumptions, NOT measured brown-bear behaviour.
        # Prediction starts with one species; the detector has a broader shortlist.
        profiles={"Ursus arctos": dict(rate=10.0, peaks=[(12.0, 3.0, 1.0)],
                                      cams=[1.0, 1.0, 0.8], weekend=1.0)},
        species_file=ROOT / "worker" / "species_katmai.json",
        source_url="https://www.nps.gov/katm/learn/photosmultimedia/webcams.htm",
    ),
}


def get_park(slug: str = "yellowstone") -> ParkConfig:
    return PARKS[slug]
