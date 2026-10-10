import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from make_seed import build_sql  # noqa: E402
from synthetic import CAMERAS, PROFILES, ROOT, generate, hourly_profile  # noqa: E402

END = datetime(2026, 10, 10, 12, tzinfo=timezone.utc)


def test_generator_is_deterministic():
    assert generate(END, 14, 42) == generate(END, 14, 42)
    assert generate(END, 14, 42) != generate(END, 14, 43)


def test_rows_are_in_window_utc_and_valid():
    rows = generate(END, 14, 42)
    assert len(rows) > 200
    cams = {c[0] for c in CAMERAS}
    for r in rows:
        t = datetime.fromisoformat(r["seen_at"])
        assert t.utcoffset() == timedelta(0)
        assert END - timedelta(days=14) <= t < END
        assert 0.5 <= r["confidence"] <= 0.99
        assert r["species"] in PROFILES and r["camera"] in cams


def test_species_match_worker_list():
    listed = {s["scientific_name"] for s in json.loads((ROOT / "worker" / "species.json").read_text())["species"]}
    assert set(PROFILES) == listed


def test_elk_peaks_at_dawn_and_dusk():
    rows = [r for r in generate(END, 60, 1) if r["species"] == "Cervus canadensis"]
    local_hours = np.array([(datetime.fromisoformat(r["seen_at"]) - timedelta(hours=6)).hour for r in rows])  # MDT
    dawn_dusk = np.isin(local_hours, [5, 6, 7, 17, 18, 19]).mean()
    assert dawn_dusk > 0.6
    assert abs(hourly_profile("Cervus canadensis").sum() - 1) < 1e-9


def test_seed_sql_is_labeled_synthetic_and_escaped():
    sql = build_sql(generate(END, 2, 42), [{"common_name": "O'Brien's Bison", "scientific_name": "Bison bison"}])
    assert "SYNTHETIC" in sql.splitlines()[0]
    assert "'O''Brien''s Bison'" in sql
    assert "source_kind" in sql and "'replay'" in sql
