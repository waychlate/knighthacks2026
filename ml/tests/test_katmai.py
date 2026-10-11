import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import predict
from evaluate import prepare
from models import temporal_split, to_frame
from parks import get_park
from synthetic import generate

NOW = datetime(2026, 10, 10, 14, 30, tzinfo=timezone.utc)


def test_katmai_predictions_have_only_brown_bears_and_selected_cameras():
    rows = predict.build_predictions(NOW, park="katmai")
    assert rows
    assert rows == predict.build_predictions(NOW, park="katmai")
    camera_names = {camera[0] for camera in get_park("katmai").cameras}
    for row in rows:
        assert row["scientific_name"] == "Ursus arctos"
        assert row["species"] == "Brown bear"
        assert row["camera"] in camera_names
        assert 0.2 <= row["probability"] <= 1
        timestamp = datetime.fromisoformat(row["predicted_for"])
        assert timestamp.utcoffset() == timedelta(0)
        assert NOW < timestamp <= NOW + timedelta(hours=24)


@pytest.mark.parametrize("utc_hour,local_hour", [(14, 6), (7, 23)])
def test_katmai_uses_alaska_local_hours(utc_hour, local_hour):
    frame = to_frame([dict(seen_at=f"2026-10-10T{utc_hour:02d}:00:00+00:00")],
                     get_park("katmai").timezone)
    assert frame.iloc[0]["hour"] == local_hour


def test_katmai_training_history_ends_before_prediction_day():
    config = get_park("katmai")
    end = NOW.astimezone(config.timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    rows = generate(end, profiles=config.profiles, cameras=config.cameras, park_tz=config.timezone)
    assert rows and all(datetime.fromisoformat(row["seen_at"]) < end for row in rows)
    train, test = temporal_split(prepare(park="katmai"))
    assert train["date"].max() < test["date"].min()
    assert set(train["species"]) == {"Ursus arctos"}


def test_local_only_writes_json_without_database_or_frontend_changes(tmp_path, monkeypatch):
    output = tmp_path / "predictions.json"
    sample = tmp_path / "frontend-sample.json"
    sample.write_text("unchanged")
    monkeypatch.setattr(predict, "SAMPLE", sample)
    monkeypatch.setenv("SUPABASE_URL", "https://example.invalid")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fake-test-key")
    def forbidden(*args, **kwargs):
        pytest.fail("local-only mode must not call Supabase")
    monkeypatch.setattr(predict, "write_supabase", forbidden)
    monkeypatch.setattr(sys, "argv", ["predict.py", "--park", "katmai", "--local-only",
                                    "--no-sample", "--output", str(output)])
    predict.main()
    data = json.loads(output.read_text())
    assert data["synthetic"] is True
    assert "SYNTHETIC" in data["note"]
    assert data["park"] == "katmai"
    assert data["timezone"] == "America/Anchorage"
    assert data["source_url"] == "https://www.nps.gov/katm/learn/photosmultimedia/webcams.htm"
    assert data["predictions"]
    assert sample.read_text() == "unchanged"


def test_katmai_species_file_loads_without_model_dependencies():
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "worker"))
    from animal_worker.classifier import load_species
    species = load_species(get_park("katmai").species_file)
    names = {s.scientific_name for s in species}
    assert "Ursus arctos" in names
    assert "Ursus arctos horribilis" not in names
    assert len(species) == len(names)
