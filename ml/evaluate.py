"""Compare the three models on SYNTHETIC data with a temporal split and a recovery check.

    python ml/evaluate.py [--days 42] [--seed 7]

The metrics table is pasted into ml/README.md. Synthetic data makes these numbers optimistic.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from models import all_models, learned_profile, make_grid, metrics, temporal_split, to_frame
from synthetic import CAMERAS, PROFILES, generate, hourly_profile

CAM_NAMES = [c[0] for c in CAMERAS]
SPECIES = list(PROFILES)
# Fixed end so the README numbers are reproducible; predict.py uses the real "now".
EVAL_END = datetime(2026, 10, 10, 6, tzinfo=timezone.utc)  # local midnight in Denver, so every day is complete


def prepare(days: int = 42, seed: int = 7, end: datetime = EVAL_END) -> pd.DataFrame:
    s = to_frame(generate(end, days, seed))
    dates = pd.date_range(s["date"].min(), s["date"].max(), freq="D")
    return make_grid(s, SPECIES, CAM_NAMES, dates)


def run(days: int = 42, seed: int = 7):
    grid = prepare(days, seed)
    train, test = temporal_split(grid, 3)
    results, recovery = [], {}
    for m in all_models():
        m.fit(train)
        p = m.predict(test)
        results.append({"model": m.name, **metrics(test, p)})
        errs = [0.5 * np.abs(learned_profile(test, p, sp) - hourly_profile(sp)).sum() for sp in SPECIES]
        recovery[m.name] = float(np.mean(errs))
    return train, test, pd.DataFrame(results), recovery


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--days", type=int, default=42)
    a.add_argument("--seeds", type=int, default=5, help="average over this many generator seeds")
    a = a.parse_args()
    frames, recs = [], []
    for seed in range(1, a.seeds + 1):
        train, test, res, rec = run(a.days, seed)
        frames.append(res.assign(profile_error=res["model"].map(rec)))
    allr = pd.concat(frames)
    print(f"SYNTHETIC data, {a.days} days per run, mean +/- sd over {a.seeds} generator seeds; "
          f"train {train['date'].min().date()}..{train['date'].max().date()}, test {test['date'].min().date()}..{test['date'].max().date()} "
          f"({len(test)} test rows, ~{test['y'].mean():.3f} positive rate)\n")
    print("| model | Brier (lower better) | log loss (lower better) | hit rate +/-1 h | profile error vs truth (TV distance) |")
    print("|---|---|---|---|---|")
    for name, g in allr.groupby("model", sort=False):
        f = lambda c, d=3: f"{g[c].mean():.{d}f} +/- {g[c].std():.{d}f}"
        print(f"| {name} | {f('brier', 4)} | {f('log_loss', 4)} | {f('hit_rate', 2)} | {f('profile_error')} |")


if __name__ == "__main__":
    main()
