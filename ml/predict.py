"""Train on SYNTHETIC history and predict the next 24 hours of sightings.

    python ml/predict.py [--threshold 0.2] [--no-sample]

Writes ml/out/predictions.json (all predictions above the threshold) and
web/public/predictions.sample.json (a few, with offsets relative to "now" for the demo).
Uses the smoothed hourly profile: it matched or beat gradient boosting in evaluate.py and is
easy to explain. Writes to Supabase only when SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are
set in the environment; it never needs them.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from models import HourlyModel, make_grid, to_frame
from synthetic import CAMERAS, PARK_TZ, PROFILES, ROOT, generate

CAM_NAMES = [c[0] for c in CAMERAS]
CAM_LOC = {c[0]: c[1] for c in CAMERAS}
SPECIES = list(PROFILES)
OUT = Path(__file__).parent / "out" / "predictions.json"
SAMPLE = ROOT / "web" / "public" / "predictions.sample.json"
NOTE = "SYNTHETIC sample predictions from ml/predict.py trained on made-up data; not real forecasts."


def common_names() -> dict[str, str]:
    data = json.loads((ROOT / "worker" / "species.json").read_text())["species"]
    return {s["scientific_name"]: s["common_name"] for s in data}


def build_predictions(now: datetime, threshold: float = 0.2, days: int = 42, seed: int = 42) -> list[dict]:
    """Predictions for the 24 whole-hour slots after `now` (UTC), probability >= threshold, sorted by time."""
    now = now.astimezone(timezone.utc)
    # Train on complete local days only (drop today, which is partial).
    today_local = now.astimezone(PARK_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    hist_end = today_local.astimezone(timezone.utc)
    sightings = to_frame(generate(hist_end, days, seed))
    dates = pd.date_range(sightings["date"].min(), sightings["date"].max(), freq="D")
    model = HourlyModel().fit(make_grid(sightings, SPECIES, CAM_NAMES, dates))

    first = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    slots = [first + timedelta(hours=i) for i in range(24)]
    grid = pd.DataFrame(
        [(sp, cam, s.astimezone(PARK_TZ).hour, s) for s in slots for sp in SPECIES for cam in CAM_NAMES],
        columns=["species", "camera", "hour", "slot"],
    )
    grid["p"] = model.predict(grid)
    names = common_names()
    rows = [
        dict(
            species=names[r.species], scientific_name=r.species, camera=r.camera,
            predicted_for=r.slot.isoformat(), probability=round(float(r.p), 3),
        )
        for r in grid[grid["p"] >= threshold].itertuples()
    ]
    return sorted(rows, key=lambda r: (r["predicted_for"], -r["probability"]))


def sample_for_web(rows: list[dict], now: datetime, n: int = 6) -> dict:
    """Best slot per species (across cameras), top n by probability, shaped like a joined `predictions` row."""
    best = {}
    for r in rows:
        k = r["scientific_name"]
        if k not in best or r["probability"] > best[k]["probability"]:
            best[k] = r
    top = sorted(best.values(), key=lambda r: -r["probability"])[:n]
    top.sort(key=lambda r: r["predicted_for"])
    out = []
    for i, r in enumerate(top):
        at = datetime.fromisoformat(r["predicted_for"]) + timedelta(minutes=30)  # middle of the hour slot
        out.append(dict(
            id=f"sample-{i + 1}",
            offset_minutes=int((at - now).total_seconds() // 60),
            probability=r["probability"],
            species=dict(common_name=r["species"], scientific_name=r["scientific_name"]),
            camera=dict(name=r["camera"], location=CAM_LOC[r["camera"]]),
        ))
    return dict(synthetic=True, note=NOTE, generated_at=now.isoformat(), predictions=out)


def write_supabase(rows: list[dict]) -> bool:
    """Insert predictions if keys are in the environment. Not exercised by the tests (needs a real project)."""
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not (url and key):
        return False
    from supabase import create_client  # in worker/requirements.txt, not ml/

    c = create_client(url, key)
    sp = {r["scientific_name"]: r["id"] for r in c.table("species").select("id,scientific_name").execute().data}
    cam = {r["name"]: r["id"] for r in c.table("cameras").select("id,name").execute().data}
    c.table("predictions").insert([
        dict(species_id=sp[r["scientific_name"]], camera_id=cam[r["camera"]], predicted_for=r["predicted_for"], probability=r["probability"])
        for r in rows if r["scientific_name"] in sp and r["camera"] in cam
    ]).execute()
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--threshold", type=float, default=0.2)
    p.add_argument("--no-sample", action="store_true", help="do not write web/public/predictions.sample.json")
    a = p.parse_args()
    now = datetime.now(timezone.utc)
    rows = build_predictions(now, a.threshold)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dict(synthetic=True, note=NOTE, generated_at=now.isoformat(), predictions=rows), indent=2))
    print(f"wrote {len(rows)} SYNTHETIC predictions to {OUT}")
    if not a.no_sample:
        SAMPLE.parent.mkdir(parents=True, exist_ok=True)
        # a lower bar than --threshold, so the demo card shows several species rather than only the surest one
        SAMPLE.write_text(json.dumps(sample_for_web(build_predictions(now, 0.05), now), indent=2))
        print(f"wrote sample to {SAMPLE}")
    print("wrote to Supabase" if write_supabase(rows) else "no Supabase keys in the environment; skipped the database")


if __name__ == "__main__":
    main()
