"""Download NASA POWER daily weather for the Katmai analysis point."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "ml" / "out" / "katmai_weather_nasa_power.json"
API = "https://power.larc.nasa.gov/api/temporal/daily/point"
USER_AGENT = "AnimalLogger-KnightHacks/1.0"
LATITUDE = 58.62235668
LONGITUDE = -155.0126574
PARAMETERS = {
    "T2M": "temperature_c",
    "T2M_MAX": "temperature_max_c",
    "T2M_MIN": "temperature_min_c",
    "PRECTOTCORR": "precipitation_mm",
    "RH2M": "relative_humidity_percent",
    "WS2M": "wind_speed_m_s",
}


def request_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=120) as response:
        return json.load(response)


def fetch_weather(start: date, end: date, fetch=request_json) -> dict:
    params = {
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "longitude": LONGITUDE,
        "latitude": LATITUDE,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
        "time-standard": "UTC",
    }
    source_url = f"{API}?{urlencode(params)}"
    data = fetch(source_url)
    header = data.get("header", {})
    fill_value = float(header.get("fill_value", -999.0))
    parameters = data.get("properties", {}).get("parameter", {})
    dates = sorted({day for values in parameters.values() for day in values})
    records = []
    for day in dates:
        row = {"date": datetime.strptime(day, "%Y%m%d").date().isoformat()}
        for api_name, output_name in PARAMETERS.items():
            value = parameters.get(api_name, {}).get(day)
            row[output_name] = None if value is None or float(value) == fill_value else float(value)
        records.append(row)
    return {
        "source": "NASA POWER Daily API",
        "source_url": source_url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "location": {
            "name": "NPS-published Katmai coordinate",
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "note": "Single gridded point; conditions vary across the park and camera sites.",
        },
        "time_standard": header.get("time_standard", "UTC"),
        "sources": header.get("sources", []),
        "parameters": PARAMETERS,
        "start": start.isoformat(),
        "end_requested": end.isoformat(),
        "records_downloaded": len(records),
        "records": records,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, default=date(2001, 1, 1))
    parser.add_argument("--end", type=date.fromisoformat, default=datetime.now(timezone.utc).date())
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    data = fetch_weather(args.start, args.end)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {data['records_downloaded']} NASA POWER daily records to {args.output}")


if __name__ == "__main__":
    main()
