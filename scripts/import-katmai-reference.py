"""Import user-provided Katmai reference data into stable local repo paths.

This does not contact Supabase or modify generated prediction output.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECIES_DIR = ROOT / "worker" / "reference" / "katmai"
PREDICTIONS_DIR = ROOT / "ml" / "reference"


def import_species(source: Path) -> tuple[int, int, int]:
    with source.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"Park Code", "Category", "Scientific Name", "Common Name",
                "Occurrence", "Record Status"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("The species CSV does not have the expected NPSpecies columns")
    if {row["Park Code"] for row in rows} != {"KATM"}:
        raise ValueError("The species CSV must contain only park code KATM")

    approved_present = [
        row for row in rows
        if row["Record Status"] == "Approved" and row["Occurrence"] == "Present"
    ]
    mammals = [row for row in approved_present if row["Category"] == "Mammal"]
    categories = dict(sorted(Counter(row["Category"] for row in approved_present).items()))

    SPECIES_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, SPECIES_DIR / "npspecies_full.csv")
    summary = {
        "source_filename": source.name,
        "park_code": "KATM",
        "park_slug": "katmai",
        "total_rows": len(rows),
        "filter": {"record_status": "Approved", "occurrence": "Present"},
        "approved_present_count": len(approved_present),
        "approved_present_by_category": categories,
        "approved_present_mammals": [
            {
                "common_name": row["Common Name"],
                "scientific_name": row["Scientific Name"],
                "abundance": row["Abundance"] or None,
                "nativeness": row["Nativeness"] or None,
            }
            for row in mammals
        ],
        "note": (
            "Reference inventory only. Park occurrence does not mean a species is "
            "likely or visible at the selected Brooks Falls Low camera."
        ),
    }
    (SPECIES_DIR / "approved_present_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    return len(rows), len(approved_present), len(mammals)


def import_predictions(source: Path) -> int:
    payload = json.loads(source.read_text(encoding="utf-8-sig"))
    required = {"synthetic", "note", "generated_at", "predictions"}
    if not required.issubset(payload) or not isinstance(payload["predictions"], list):
        raise ValueError("The prediction example does not have the expected JSON shape")
    if payload["synthetic"] is not True:
        raise ValueError("The supplied example must remain explicitly labeled synthetic")
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    payload["reference_only"] = True
    payload["reference_note"] = (
        "User-provided format example stored locally until Supabase is available. "
        "This file is not current output and must not be presented as a live forecast."
    )
    (PREDICTIONS_DIR / "predictions.example.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    return len(payload["predictions"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--species-csv", type=Path, required=True)
    parser.add_argument("--predictions-example", type=Path, required=True)
    args = parser.parse_args()
    total, present, mammals = import_species(args.species_csv)
    predictions = import_predictions(args.predictions_example)
    print(f"stored {total} NPSpecies rows ({present} approved/present; {mammals} mammals)")
    print(f"stored {predictions} synthetic example predictions")


if __name__ == "__main__":
    main()
