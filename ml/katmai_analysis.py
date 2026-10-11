"""Summarize Katmai camera detections and the NPS species inventory.

This is descriptive analysis, not a population estimate or a forecast. Camera
rates use frames as survey effort so a folder with more captures does not look
more active merely because it was sampled longer.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CAPTURES = ROOT / "worker" / "sample_videos" / "katmai"
DEFAULT_INVENTORY = ROOT / "worker" / "reference" / "katmai" / "npspecies_full.csv"
DEFAULT_OUTPUT = ROOT / "ml" / "out"
DEFAULT_GBIF = DEFAULT_OUTPUT / "katmai_brown_bear_gbif.json"


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> list[float]:
    """Return a 95% Wilson interval as percentages."""
    if trials <= 0:
        return [0.0, 0.0]
    p = successes / trials
    denominator = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * trials)) / trials) / denominator
    return [round(100 * max(0.0, center - margin), 2), round(100 * min(1.0, center + margin), 2)]


def load_frames(captures_root: Path) -> list[dict]:
    rows = []
    for manifest in sorted(Path(captures_root).rglob("frames.jsonl")):
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            row["_survey"] = str(manifest.parent.relative_to(captures_root)) or "."
            row["_frame_key"] = f"{row['_survey']}/{row.get('file', '')}"
            rows.append(row)
    return rows


def load_sightings(captures_root: Path) -> list[dict]:
    rows = []
    for path in sorted(Path(captures_root).rglob("sightings.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        survey = str(path.parent.relative_to(captures_root)) or "."
        for row in data.get("sightings", []):
            item = dict(row)
            item["_survey"] = survey
            item["_frame_key"] = f"{survey}/{item.get('source_file', '')}"
            rows.append(item)
    return rows


def summarize_camera(camera: str, frames: list[dict], sightings: list[dict]) -> dict:
    frame_keys = {row["_frame_key"] for row in frames}
    times = [time for row in frames if (time := parse_time(row.get("captured_at")))]
    detected = {row["_frame_key"] for row in sightings if row["_frame_key"] in frame_keys}
    labels = sorted({str(row.get("broad_label") or "unknown") for row in sightings})
    by_label = {}
    for label in labels:
        label_frames = {
            row["_frame_key"] for row in sightings
            if row["_frame_key"] in frame_keys and (row.get("broad_label") or "unknown") == label
        }
        by_label[label] = {
            "detections": sum((row.get("broad_label") or "unknown") == label for row in sightings),
            "frames": len(label_frames),
            "frames_per_100": round(100 * len(label_frames) / len(frame_keys), 2) if frame_keys else 0.0,
            "interval_95_percent": wilson_interval(len(label_frames), len(frame_keys)),
        }
    return {
        "camera": camera,
        "frames": len(frame_keys),
        "frames_with_detection": len(detected),
        "detection_frames_per_100": round(100 * len(detected) / len(frame_keys), 2) if frame_keys else 0.0,
        "interval_95_percent": wilson_interval(len(detected), len(frame_keys)),
        "detection_boxes": len(sightings),
        "by_label": by_label,
        "first_capture_utc": min(times).isoformat() if times else None,
        "last_capture_utc": max(times).isoformat() if times else None,
        "collection_span_hours": round((max(times) - min(times)).total_seconds() / 3600, 2) if len(times) > 1 else 0.0,
        "source_kinds": dict(sorted(Counter(row.get("source_kind") or "unknown" for row in frames).items())),
        "known_observation_times": sum(bool(row.get("observation_time")) for row in frames),
    }


def summarize_cameras(frames: list[dict], sightings: list[dict]) -> dict:
    by_camera_frames = defaultdict(list)
    for row in frames:
        by_camera_frames[row.get("camera") or "Unknown camera"].append(row)
    by_frame = {row["_frame_key"]: row.get("camera") or "Unknown camera" for row in frames}
    by_camera_sightings = defaultdict(list)
    unmatched = 0
    for row in sightings:
        camera = by_frame.get(row["_frame_key"])
        if camera is None:
            unmatched += 1
            camera = row.get("camera") or "Unknown camera"
        by_camera_sightings[camera].append(row)
    cameras = [
        summarize_camera(camera, camera_frames, by_camera_sightings.get(camera, []))
        for camera, camera_frames in sorted(by_camera_frames.items())
    ]
    return {
        "frames": sum(item["frames"] for item in cameras),
        "detection_boxes": sum(item["detection_boxes"] for item in cameras),
        "unmatched_sightings": unmatched,
        "cameras": cameras,
    }


def summarize_inventory(path: Path) -> dict:
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        all_rows = list(csv.DictReader(handle))
    present = [
        row for row in all_rows
        if row.get("Record Status", "").strip().lower() == "approved"
        and row.get("Occurrence", "").strip().lower() == "present"
    ]
    return {
        "source": str(path),
        "inventory_rows": len(all_rows),
        "approved_present_species": len(present),
        "by_category": dict(sorted(Counter(row.get("Category") or "Unknown" for row in present).items())),
        "by_nativeness": dict(sorted(Counter(row.get("Nativeness") or "Unknown" for row in present).items())),
        "by_abundance": dict(sorted(Counter(row.get("Abundance") or "Unreported" for row in present).items())),
    }


def summarize_public_observations(path: Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    unique = {}
    for row in data.get("records", []):
        if row.get("key") is not None:
            unique.setdefault(str(row["key"]), row)
    records = list(unique.values())
    dated = [row for row in records if row.get("year") and row.get("month")]
    years = Counter(int(row["year"]) for row in dated)
    months = Counter(int(row["month"]) for row in dated)
    uncertainties = [
        float(row["coordinateUncertaintyInMeters"])
        for row in records if row.get("coordinateUncertaintyInMeters") is not None
    ]
    return {
        "source": data.get("source"),
        "source_url": data.get("source_url"),
        "retrieved_at": data.get("retrieved_at"),
        "region": data.get("region"),
        "taxon_match": data.get("taxon_match"),
        "records": len(records),
        "dated_records": len(dated),
        "first_year": min(years) if years else None,
        "last_year": max(years) if years else None,
        "by_year": {str(year): years[year] for year in sorted(years)},
        "by_month": {str(month): months.get(month, 0) for month in range(1, 13)},
        "basis_of_record": dict(sorted(Counter(row.get("basisOfRecord") or "Unknown" for row in records).items())),
        "licenses": dict(sorted(Counter(row.get("license") or "Unreported" for row in records).items())),
        "datasets": len({row.get("datasetKey") for row in records if row.get("datasetKey")}),
        "median_coordinate_uncertainty_m": round(median(uncertainties), 1) if uncertainties else None,
        "truncated": bool(data.get("truncated")),
    }


def build_report(captures_root: Path, inventory_path: Path, gbif_path: Path | None = None) -> dict:
    frames = load_frames(captures_root)
    sightings = load_sightings(captures_root)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_type": "descriptive_camera_effort_species_inventory_and_public_occurrences",
        "camera_survey": summarize_cameras(frames, sightings),
        "nps_inventory": summarize_inventory(inventory_path),
        "limitations": [
            "Detection rates describe sampled frames, not animal abundance or population size.",
            "Consecutive frames are correlated and may show the same animal repeatedly.",
            "The sighting cooldown can merge repeated detections and lower observed rates.",
            "Capture time is not observation time when a live page is replaying highlights.",
            "One short collection window cannot support seasonal or hour-of-day forecasts.",
            "NPS inventory presence does not mean a species is visible from these cameras.",
            "GBIF record counts reflect observer effort and publication bias, not animal abundance.",
            "The GBIF regional envelope is not the legal boundary of Katmai National Park and Preserve.",
        ],
    }
    if gbif_path and Path(gbif_path).exists():
        report["public_observations"] = summarize_public_observations(gbif_path)
    return report


def markdown_report(report: dict) -> str:
    survey = report["camera_survey"]
    inventory = report["nps_inventory"]
    lines = [
        "# Katmai descriptive analysis",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Camera survey",
        "",
        f"The survey contains **{survey['frames']:,} frames** and **{survey['detection_boxes']:,} detection boxes**.",
        "Rates below are frames containing at least one accepted detection per 100 captured frames.",
        "",
        "| Camera | Frames | Detection frames / 100 | 95% interval | Bears / 100 | Birds / 100 | Span (hours) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for camera in survey["cameras"]:
        bear = camera["by_label"].get("bear", {}).get("frames_per_100", 0.0)
        bird = camera["by_label"].get("bird", {}).get("frames_per_100", 0.0)
        low, high = camera["interval_95_percent"]
        lines.append(
            f"| {camera['camera']} | {camera['frames']} | {camera['detection_frames_per_100']:.2f} "
            f"| {low:.2f}-{high:.2f} | {bear:.2f} | {bird:.2f} | {camera['collection_span_hours']:.2f} |"
        )
    lines += [
        "",
        "## NPS species inventory",
        "",
        f"The reference contains **{inventory['approved_present_species']:,} approved, present species** "
        f"from {inventory['inventory_rows']:,} inventory rows.",
        "",
        "| Category | Species |",
        "|---|---:|",
    ]
    lines += [f"| {name} | {count} |" for name, count in inventory["by_category"].items()]
    public = report.get("public_observations")
    if public:
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        lines += [
            "",
            "## Public brown-bear observations",
            "",
            f"GBIF contributed **{public['records']:,} unique records** from "
            f"**{public['first_year']}-{public['last_year']}** inside the configured Katmai regional envelope.",
            "These are opportunistic records; monthly counts also reflect visitor access, observer effort, and reporting.",
            "",
            "| Month | Records | Share |",
            "|---|---:|---:|",
        ]
        total = public["dated_records"] or 1
        for month, name in enumerate(month_names, 1):
            count = public["by_month"][str(month)]
            lines.append(f"| {name} | {count} | {100 * count / total:.1f}% |")
    lines += ["", "## Limits", ""]
    lines += [f"- {item}" for item in report["limitations"]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captures", type=Path, default=DEFAULT_CAPTURES)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--gbif", type=Path, default=DEFAULT_GBIF,
                        help="optional public occurrence JSON from fetch_gbif.py")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    report = build_report(args.captures, args.inventory, args.gbif)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "katmai_analysis.json"
    markdown_path = args.output_dir / "katmai_analysis.md"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    print(f"wrote {json_path}")
    print(f"wrote {markdown_path}")


if __name__ == "__main__":
    main()
