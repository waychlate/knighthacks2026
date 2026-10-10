"""Merge repeated detections into one sighting.

One deer standing in frame for five minutes must not create 300 log rows. A
(camera, species) pair is only logged again after `cooldown_s` seconds have
passed since it was last *seen* (not last logged), so an animal that stays in
frame keeps extending its own cooldown.
"""

from __future__ import annotations


class Deduper:
    def __init__(self, cooldown_s: float = 60.0):
        self.cooldown_s = cooldown_s
        self._last_seen: dict[tuple[str, str], float] = {}

    def should_log(self, camera: str, species: str, now: float) -> bool:
        key = (camera, species)
        last = self._last_seen.get(key)
        self._last_seen[key] = now
        return last is None or (now - last) > self.cooldown_s
