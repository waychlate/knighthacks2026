"""Named Katmai camera configuration shared by the collection commands."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "katmai_cameras.json"


@dataclass(frozen=True)
class KatmaiCamera:
    id: str
    name: str
    location: str
    youtube_url: str
    nps_page: str
    description: str


def load_katmai_cameras(path: Path = CONFIG_PATH) -> dict[str, KatmaiCamera]:
    data = json.loads(path.read_text(encoding="utf-8"))
    cameras = [KatmaiCamera(**row) for row in data["cameras"]]
    return {camera.id: camera for camera in cameras}


KATMAI_CAMERAS = load_katmai_cameras()
DEFAULT_KATMAI_CAMERA = "brooks-falls-low"
