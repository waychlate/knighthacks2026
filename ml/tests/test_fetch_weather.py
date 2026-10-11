import sys
from datetime import date
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fetch_weather import fetch_weather


def test_fetch_weather_normalizes_power_response_and_fill_values():
    def fake_fetch(url):
        assert "time-standard=UTC" in url
        return {
            "header": {"fill_value": -999.0, "time_standard": "UTC", "sources": ["MERRA2"]},
            "properties": {"parameter": {
                "T2M": {"20240101": -2.5, "20240102": -999.0},
                "PRECTOTCORR": {"20240101": 1.2, "20240102": 0.0},
            }},
        }

    result = fetch_weather(date(2024, 1, 1), date(2024, 1, 2), fetch=fake_fetch)
    assert result["records_downloaded"] == 2
    assert result["records"][0]["temperature_c"] == -2.5
    assert result["records"][1]["temperature_c"] is None
    assert result["records"][0]["precipitation_mm"] == 1.2
    assert result["time_standard"] == "UTC"
