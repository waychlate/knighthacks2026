"""Generate demo-ready Katmai charts and frontend insights JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "ml" / "out" / "katmai_analysis.json"
DEFAULT_OUTPUT = ROOT / "web" / "public" / "katmai" / "insights"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

COLORS = {
    "bear": "#8B5A2B",
    "bird": "#2C7A7B",
    "orange": "#D97706",
    "blue": "#2563EB",
    "green": "#15803D",
    "grid": "#D1D5DB",
    "text": "#1F2937",
}


def _pyplot():
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams["svg.fonttype"] = "none"
    from matplotlib import pyplot as plt

    return plt


def _finish(fig, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg", bbox_inches="tight", metadata={"Date": None})
    _pyplot().close(fig)
    # Matplotlib emits spaces before newlines in SVG path data. Normalize the
    # generated text so repository whitespace checks remain clean.
    text = path.read_text(encoding="utf-8")
    path.write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n", encoding="utf-8")


def plot_public_observations(report: dict, path: Path):
    plt = _pyplot()
    values = [report["public_observations"]["by_month"][str(month)] for month in range(1, 13)]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    bars = ax.bar(MONTHS, values, color=COLORS["orange"], width=0.72)
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_title("Public brown-bear observation records by month", loc="left", weight="bold", fontsize=15)
    ax.set_ylabel("GBIF records")
    ax.grid(axis="y", color=COLORS["grid"], alpha=0.7, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(
        0.01, 0.01,
        "Historical records reflect observer access and reporting as well as bear presence; they are not population counts.",
        fontsize=9, color=COLORS["text"],
    )
    fig.subplots_adjust(bottom=0.16)
    _finish(fig, path)


def plot_weather_daylight(report: dict, path: Path):
    plt = _pyplot()
    monthly = report["daily_features"]["by_month"]
    temperatures = [monthly[str(month)]["mean_temperature_c"] for month in range(1, 13)]
    daylight = [monthly[str(month)]["mean_daylight_hours"] for month in range(1, 13)]
    x = list(range(12))
    fig, temperature_axis = plt.subplots(figsize=(10, 5.2))
    daylight_axis = temperature_axis.twinx()
    temperature_axis.plot(x, temperatures, marker="o", linewidth=2.5, color=COLORS["blue"], label="Mean temperature")
    daylight_axis.plot(x, daylight, marker="s", linewidth=2.5, color=COLORS["green"], label="Mean daylight")
    temperature_axis.set_xticks(x, MONTHS)
    temperature_axis.set_ylabel("Mean temperature (°C)", color=COLORS["blue"])
    daylight_axis.set_ylabel("Mean daylight (hours)", color=COLORS["green"])
    temperature_axis.tick_params(axis="y", colors=COLORS["blue"])
    daylight_axis.tick_params(axis="y", colors=COLORS["green"])
    temperature_axis.axhline(0, color=COLORS["grid"], linewidth=1)
    temperature_axis.grid(axis="x", color=COLORS["grid"], alpha=0.45)
    temperature_axis.set_title("Katmai seasonal weather and daylight", loc="left", weight="bold", fontsize=15)
    temperature_axis.spines["top"].set_visible(False)
    daylight_axis.spines["top"].set_visible(False)
    fig.legend(loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.01))
    fig.subplots_adjust(bottom=0.17)
    _finish(fig, path)


def plot_camera_rates(report: dict, path: Path):
    plt = _pyplot()
    cameras = report["camera_survey"]["cameras"]
    labels = [row["camera"] for row in cameras]
    y = list(range(len(cameras)))
    height = 0.34
    fig, ax = plt.subplots(figsize=(10, 5.6))
    for offset, label, color in [(-height / 2, "bear", COLORS["bear"]), (height / 2, "bird", COLORS["bird"])]:
        values, lower, upper = [], [], []
        for camera in cameras:
            item = camera["by_label"].get(label, {"frames_per_100": 0.0, "interval_95_percent": [0.0, 0.0]})
            value = item["frames_per_100"]
            low, high = item["interval_95_percent"]
            values.append(value)
            lower.append(max(0, value - low))
            upper.append(max(0, high - value))
        positions = [position + offset for position in y]
        ax.barh(positions, values, height=height, color=color, label=label.title())
        ax.errorbar(values, positions, xerr=[lower, upper], fmt="none", ecolor=COLORS["text"], capsize=3, linewidth=1)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Frames with detection per 100 captured frames (95% interval)")
    ax.set_title("Accepted Katmai detections by camera", loc="left", weight="bold", fontsize=15)
    ax.grid(axis="x", color=COLORS["grid"], alpha=0.7, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.text(0.01, 0.01, "Short local collection; rates describe sampled frames and do not estimate animal abundance.", fontsize=9)
    fig.subplots_adjust(left=0.22, bottom=0.17)
    _finish(fig, path)


def build_insights(report: dict) -> dict:
    cameras = report["camera_survey"]["cameras"]
    highest_camera = max(cameras, key=lambda row: row["detection_frames_per_100"])
    public = report["public_observations"]
    peak_month_number = max(range(1, 13), key=lambda month: public["by_month"][str(month)])
    peak_count = public["by_month"][str(peak_month_number)]
    dated = public["dated_records"] or 1
    features = report["daily_features"]
    observation_weather = features["observation_day_weather"]
    return {
        "generated_at": report["generated_at"],
        "park": "katmai",
        "kind": "historical_descriptive_insights",
        "headline": "Katmai camera and historical observation patterns",
        "summary": {
            "camera_frames": report["camera_survey"]["frames"],
            "accepted_detection_boxes": report["camera_survey"]["detection_boxes"],
            "public_bear_records": public["records"],
            "weather_days": features["daily_rows"],
        },
        "insights": [
            {
                "id": "highest-camera-rate",
                "title": "Highest camera detection rate",
                "value": highest_camera["camera"],
                "detail": (
                    f"{highest_camera['detection_frames_per_100']:.2f} of every 100 sampled frames had an accepted "
                    f"detection (95% interval {highest_camera['interval_95_percent'][0]:.2f}-"
                    f"{highest_camera['interval_95_percent'][1]:.2f})."
                ),
                "caveat": "This short collection does not estimate animal abundance.",
            },
            {
                "id": "peak-public-month",
                "title": "Peak public observation month",
                "value": MONTHS[peak_month_number - 1],
                "detail": f"{peak_count} GBIF records, or {100 * peak_count / dated:.1f}% of records with a month.",
                "caveat": "GBIF counts reflect visitor access, observer effort, and reporting as well as bear presence.",
            },
            {
                "id": "historical-observation-conditions",
                "title": "Conditions on historical observation days",
                "value": f"{observation_weather['mean_temperature_c']:.1f}°C",
                "detail": (
                    f"Observation days averaged {observation_weather['mean_daylight_hours']:.1f} daylight hours, "
                    f"{observation_weather['mean_precipitation_mm_day']:.1f} mm precipitation, and "
                    f"{observation_weather['mean_relative_humidity_percent']:.1f}% relative humidity."
                ),
                "caveat": "These are associations in opportunistic records, not causes or forecast probabilities.",
            },
        ],
        "charts": [
            {"id": "public-observations", "title": "Public observations by month", "src": "/katmai/insights/bear_observations_by_month.svg"},
            {"id": "weather-daylight", "title": "Weather and daylight by month", "src": "/katmai/insights/weather_daylight_by_month.svg"},
            {"id": "camera-rates", "title": "Detection rates by camera", "src": "/katmai/insights/camera_detection_rates.svg"},
        ],
        "sources": [
            {"name": "GBIF occurrence search API", "url": public["source_url"]},
            {"name": "NASA POWER Daily API", "url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/"},
            {"name": "NPS Katmai species inventory", "url": "https://irma.nps.gov/NPSpecies/"},
        ],
        "limitations": report["limitations"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    report = json.loads(args.report.read_text(encoding="utf-8"))
    required = ["camera_survey", "public_observations", "daily_features"]
    missing = [name for name in required if name not in report]
    if missing:
        parser.error(f"report is missing sections: {', '.join(missing)}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plot_public_observations(report, args.output_dir / "bear_observations_by_month.svg")
    plot_weather_daylight(report, args.output_dir / "weather_daylight_by_month.svg")
    plot_camera_rates(report, args.output_dir / "camera_detection_rates.svg")
    insights = build_insights(report)
    output = args.output_dir / "insights.json"
    output.write_text(json.dumps(insights, indent=2) + "\n", encoding="utf-8")
    print(f"wrote 3 charts and {output}")


if __name__ == "__main__":
    main()
