"""Data prep, three models and metrics for sighting predictions. Trained on SYNTHETIC data for now.

Framing: for each (species, camera, local date, local hour) predict the probability of at
least one sighting in that hour. Everything is in park-local time (so "dawn" is stable
across daylight saving) and converted to UTC only when predictions are written out.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, log_loss

from synthetic import PARK_TZ

FEATURES = ["hour_sin", "hour_cos", "weekday", "prev7", "species_code", "camera_code"]


def to_frame(rows: list[dict], park_tz=PARK_TZ) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    local = pd.to_datetime(df["seen_at"], utc=True).dt.tz_convert(park_tz)
    df["date"] = local.dt.tz_localize(None).dt.normalize()
    df["hour"] = local.dt.hour
    return df


def make_grid(sightings: pd.DataFrame, species: list[str], cameras: list[str], dates: pd.DatetimeIndex) -> pd.DataFrame:
    """One row per (date, species, camera, hour) with label y and features.

    prev7 = sightings of that species/camera in the 7 days *before* the date, so it is known
    when forecasting. Dates after the history reuse the latest known value.
    """
    idx = pd.MultiIndex.from_product([dates, species, cameras, range(24)], names=["date", "species", "camera", "hour"])
    hits = sightings.groupby(["date", "species", "camera", "hour"]).size()
    grid = pd.DataFrame(index=idx).reset_index()
    grid["y"] = (grid.set_index(["date", "species", "camera", "hour"]).index.map(hits).fillna(0).to_numpy() > 0).astype(int)

    daily = sightings.groupby(["date", "species", "camera"]).size().unstack(["species", "camera"], fill_value=0)
    days = pd.date_range(min(daily.index.min(), dates.min()) - pd.Timedelta(days=7), max(daily.index.max(), dates.max()), freq="D")
    prev7 = daily.reindex(days, fill_value=0)
    last_known = daily.index.max()
    prev7 = prev7.rolling(7, min_periods=1).sum().shift(1)
    prev7.loc[prev7.index > last_known] = np.nan
    prev7 = prev7.ffill().fillna(0).stack(["species", "camera"]).rename("prev7")
    grid = grid.merge(prev7.reset_index().rename(columns={"level_0": "date"}), on=["date", "species", "camera"], how="left")
    grid["prev7"] = grid["prev7"].fillna(0)

    grid["hour_sin"] = np.sin(2 * np.pi * (grid["hour"] + 0.5) / 24)
    grid["hour_cos"] = np.cos(2 * np.pi * (grid["hour"] + 0.5) / 24)
    grid["weekday"] = grid["date"].dt.weekday
    grid["species_code"] = grid["species"].map({s: i for i, s in enumerate(species)})
    grid["camera_code"] = grid["camera"].map({c: i for i, c in enumerate(cameras)})
    return grid


def temporal_split(grid: pd.DataFrame, test_days: int = 3):
    """Train on earlier days, test on the last `test_days`. Never shuffles across time."""
    cutoff = grid["date"].max() - pd.Timedelta(days=test_days - 1)
    return grid[grid["date"] < cutoff].copy(), grid[grid["date"] >= cutoff].copy()


class NaiveModel:
    """Overall rate per (species, camera), ignoring the hour."""

    name = "naive rate"

    def fit(self, g):
        self.rate = g.groupby(["species", "camera"])["y"].mean()
        return self

    def predict(self, g):
        return g.set_index(["species", "camera"]).index.map(self.rate).fillna(0).to_numpy(dtype=float)


class HourlyModel:
    """Smoothed historical rate by hour of day per (species, camera), shrunk toward the naive rate."""

    name = "hourly profile"

    def __init__(self, prior_days: float = 2.0):
        self.prior_days = prior_days

    def fit(self, g):
        self.naive = g.groupby(["species", "camera"])["y"].mean()
        self.n_days = g["date"].nunique()
        hourly = g.groupby(["species", "camera", "hour"])["y"].mean().unstack("hour", fill_value=0).reindex(columns=range(24), fill_value=0)
        padded = np.concatenate([hourly.to_numpy()[:, -1:], hourly.to_numpy(), hourly.to_numpy()[:, :1]], axis=1)  # circular
        smooth = 0.25 * padded[:, :-2] + 0.5 * padded[:, 1:-1] + 0.25 * padded[:, 2:]
        prior = self.naive.reindex(hourly.index).to_numpy()[:, None]
        n = self.n_days
        self.table = pd.DataFrame((smooth * n + self.prior_days * prior) / (n + self.prior_days), index=hourly.index, columns=range(24)).stack()
        return self

    def predict(self, g):
        keys = pd.MultiIndex.from_arrays([g["species"], g["camera"], g["hour"]])
        return self.table.reindex(keys).fillna(0).to_numpy(dtype=float)


class BoostedModel:
    """Gradient boosting on hour (sin/cos), weekday, 7-day recent activity, species and camera."""

    name = "gradient boosting"

    def fit(self, g):
        self.clf = HistGradientBoostingClassifier(
            max_depth=4, learning_rate=0.1, max_iter=150, categorical_features=[4, 5], random_state=0
        ).fit(g[FEATURES], g["y"])
        return self

    def predict(self, g):
        return self.clf.predict_proba(g[FEATURES])[:, 1]


def all_models():
    return [NaiveModel(), HourlyModel(), BoostedModel()]


def hit_rate(test: pd.DataFrame, p: np.ndarray, tol: int = 1) -> float:
    """Share of (species, camera) pairs with a real test sighting whose top predicted hour is within
    +/- `tol` hours (circular) of a real sighting hour. Ties go to the earliest hour."""
    t = test.assign(p=p)
    hits = total = 0
    for _, grp in t.groupby(["species", "camera"]):
        real = grp.loc[grp["y"] == 1, "hour"].unique()
        if len(real) == 0:
            continue
        top = grp.groupby("hour")["p"].mean().idxmax()
        d = np.abs(real - top)
        hits += int((np.minimum(d, 24 - d) <= tol).any())
        total += 1
    return hits / total if total else float("nan")


def metrics(test: pd.DataFrame, p: np.ndarray) -> dict:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {"brier": brier_score_loss(test["y"], p), "log_loss": log_loss(test["y"], p, labels=[0, 1]), "hit_rate": hit_rate(test, p)}


def learned_profile(g: pd.DataFrame, p: np.ndarray, species: str) -> np.ndarray:
    """The model's hour-of-day shape for a species (mean prediction per hour, normalised to sum 1)."""
    s = g.assign(p=p)[g["species"] == species].groupby("hour")["p"].mean().reindex(range(24), fill_value=0).to_numpy()
    return s / s.sum() if s.sum() > 0 else np.full(24, 1 / 24)
