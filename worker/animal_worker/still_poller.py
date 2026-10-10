"""Poll a still-image webcam URL and save each new frame to disk.

Used to record our own replay footage from the NPS Yellowstone "North Entrance -
Electric Peak" cam (a JPEG refreshed every 30-60 s). The same fetch_still() is meant to
back the worker's live image-URL source later.

    python -m animal_worker.still_poller --out sample_videos/yellowstone --every 60

Image credit: National Park Service. Stops on the first error rather than retrying.
"""
import argparse
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

URL = "https://www.nps.gov/webcams-yell/mammoth_electric.jpg"
USER_AGENT = "animal-logger-hackathon (laureate841@gmail.com)"


def fetch_still(url, etag=None, timeout=20):
    """Return (jpeg_bytes, etag), or (None, etag) if unchanged since `etag`."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    if etag:
        req.add_header("If-None-Match", etag)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(), resp.headers.get("ETag")
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return None, etag
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--url", default=URL)
    p.add_argument("--out", default="sample_videos/yellowstone")
    p.add_argument("--every", type=int, default=60, help="seconds between polls (min 30)")
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    every = max(args.every, 30)  # be gentle: the cam only refreshes every 30-60 s anyway

    etag = None
    while True:
        data, etag = fetch_still(args.url, etag)
        if data:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            (out / f"{ts}.jpg").write_bytes(data)
            print(f"saved {ts}.jpg ({len(data)} bytes)", flush=True)
        time.sleep(every)


if __name__ == "__main__":
    main()
