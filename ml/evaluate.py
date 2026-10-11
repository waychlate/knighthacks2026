"""Compare the three models on SYNTHETIC data with a temporal split and a recovery check.

    python ml/evaluate.py [--park katmai] [--days 42] [--seeds 5]

The metrics table is pasted into ml/README.md. Synthetic data makes these numbers optimistic.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from models import all_models, learned_profile, make_grid, metrics, temporal_split, to_frame
from synthetic import generate, hourly_profile
from parks import PARKS, get_park

# Evaluation ends at a fixed park-local midnight for reproducibility.


def prepare(days: int = 42, seed: int = 7, end: datetime | None = None,
            park: str = "yellowstone") -> pd.DataFrame:
    config = get_park(park)
    end = end or datetime(2026, 10, 10, tzinfo=config.timezone).astimezone(timezone.utc)
    s = to_frame(generate(end, days, seed, profiles=config.profiles,
                          cameras=config.cameras, park_tz=config.timezone), config.timezone)
    dates = pd.date_range(s["date"].min(), s["date"].max(), freq="D")
    return make_grid(s, list(config.profiles), [c[0] for c in config.cameras], dates)


def run(days: int = 42, seed: int = 7, park: str = "yellowstone"):
    config = get_park(park)
    grid = prepare(days, seed, park=park)
    train, test = temporal_split(grid, 3)
    results, recovery = [], {}
    for m in all_models():
        m.fit(train)
        p = m.predict(test)
        results.append({"model": m.name, **metrics(test, p)})
        errs = [0.5 * np.abs(learned_profile(test, p, sp) - hourly_profile(sp, config.profiles)).sum()
                for sp in config.profiles]
        recovery[m.name] = float(np.mean(errs))
    return train, test, pd.DataFrame(results), recovery


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--days", type=int, default=42)
    a.add_argument("--park", choices=list(PARKS), default="yellowstone")
    a.add_argument("--seeds", type=int, default=5, help="average over this many generator seeds")
    a = a.parse_args()
    frames = []
    for seed in range(1, a.seeds + 1):
        train, test, res, rec = run(a.days, seed, a.park)
        frames.append(res.assign(profile_error=res["model"].map(rec)))
    allr = pd.concat(frames)
    print(f"SYNTHETIC {a.park} data, {a.days} days per run, mean +/- sd over {a.seeds} generator seeds; "
          f"train {train['date'].min().date()}..{train['date'].max().date()}, test {test['date'].min().date()}..{test['date'].max().date()} "
          f"({len(test)} test rows, ~{test['y'].mean():.3f} positive rate)\n")
    print("| model | Brier (lower better) | log loss (lower better) | hit rate +/-1 h | profile error vs truth (TV distance) |")
    print("|---|---|---|---|---|")
    for name, g in allr.groupby("model", sort=False):
        f = lambda c, d=3: f"{g[c].mean():.{d}f} +/- {g[c].std():.{d}f}"
        print(f"| {name} | {f('brier', 4)} | {f('log_loss', 4)} | {f('hit_rate', 2)} | {f('profile_error')} |")


if __name__ == "__main__":
    main()
