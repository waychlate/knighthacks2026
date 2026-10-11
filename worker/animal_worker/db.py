"""Supabase writes: ensure camera/species rows exist, upload snapshot, insert sighting."""

from __future__ import annotations

import io
import os
import uuid
from datetime import datetime, timezone


class SightingStore:
    def __init__(self):
        from supabase import create_client

        self.client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
        self._camera_ids: dict[str, str] = {}
        self._species_ids: dict[str, str] = {}

    def camera_id(self, name: str, location: str | None = None, park: str = "yellowstone") -> str:
        if name not in self._camera_ids:
            row = self.client.table("cameras").upsert({"name": name, "location": location, "park": park}, on_conflict="name").execute()
            self._camera_ids[name] = row.data[0]["id"]
        return self._camera_ids[name]

    def species_id(self, common_name: str, scientific_name: str) -> str:
        if scientific_name not in self._species_ids:
            row = (
                self.client.table("species")
                .upsert({"common_name": common_name, "scientific_name": scientific_name}, on_conflict="scientific_name")
                .execute()
            )
            self._species_ids[scientific_name] = row.data[0]["id"]
        return self._species_ids[scientific_name]

    def upload_snapshot(self, crop) -> str:
        buf = io.BytesIO()
        crop.save(buf, format="JPEG", quality=85)
        path = f"{datetime.now(timezone.utc):%Y/%m/%d}/{uuid.uuid4().hex}.jpg"
        bucket = self.client.storage.from_("snapshots")
        bucket.upload(path, buf.getvalue(), {"content-type": "image/jpeg"})
        return bucket.get_public_url(path)

    def insert_sighting(self, *, species_id: str, camera_id: str, confidence: float,
                        snapshot_url: str | None, source_kind: str = "replay",
                        seen_at: str | None = None):
        payload = {
            "species_id": species_id,
            "camera_id": camera_id,
            "confidence": round(confidence, 3),
            "snapshot_url": snapshot_url,
            "source_kind": source_kind,
        }
        if seen_at is not None:
            payload["seen_at"] = seen_at
        self.client.table("sightings").insert(payload).execute()
