"""Collect frames from a still-image webcam or a YouTube live broadcast.

Used to record our own replay footage from the NPS Yellowstone "North Entrance -
Electric Peak" cam (a JPEG refreshed every 30-60 s). The same fetch_still() is meant to
back the worker's live image-URL source later.

    python -m animal_worker.still_poller --out sample_videos/yellowstone --every 60
    python -m animal_worker.still_poller --park katmai --every 60

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


def main(argv=None):
    from .katmai_cameras import DEFAULT_KATMAI_CAMERA, KATMAI_CAMERAS

    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--park", choices=["yellowstone", "katmai"], default="yellowstone")
    p.add_argument("--url", help="still-image URL or YouTube watch URL (default depends on --park)")
    p.add_argument("--out", help="output directory (default: sample_videos/<park>)")
    p.add_argument("--camera-id", choices=sorted(KATMAI_CAMERAS), default=DEFAULT_KATMAI_CAMERA,
                   help="named Katmai camera (used when --park katmai)")
    p.add_argument("--camera", help="override camera label in frame metadata")
    p.add_argument("--list-cameras", action="store_true", help="print configured Katmai cameras and exit")
    p.add_argument("--every", type=int, default=60, help="seconds between polls (min 30)")
    p.add_argument("--max-frames", type=int, help="stop after saving this many frames (default: until Ctrl+C)")
    args = p.parse_args(argv)
    if args.list_cameras:
        for camera in KATMAI_CAMERAS.values():
            print(f"{camera.id}: {camera.name} - {camera.youtube_url}")
        return
    if args.every <= 0 or (args.max_frames is not None and args.max_frames < 1):
        p.error("--every and --max-frames must be positive")
    from .youtube_poller import collect_frames, is_youtube_url, resolve_youtube

    selected = KATMAI_CAMERAS[args.camera_id]
    url = args.url or (selected.youtube_url if args.park == "katmai" else URL)
    camera_name = args.camera or (selected.name if args.park == "katmai" else "Electric Peak Cam")
    default_out = (f"sample_videos/katmai/{selected.id}"
                   if args.park == "katmai" else "sample_videos/yellowstone")
    out = Path(args.out or default_out)
    if is_youtube_url(url):
        try:
            stream = resolve_youtube(url)
            print(f"Collecting {stream.title} ({stream.video_id}); save every {max(args.every, 30)} s", flush=True)
            collect_frames(stream, out, park=args.park, camera=camera_name,
                           every=args.every, max_frames=args.max_frames,
                           log=lambda line: print(line, flush=True))
        except KeyboardInterrupt:
            print("Collector stopped.", flush=True)
        except (RuntimeError, OSError, ValueError) as exc:
            p.exit(1, f"Collector stopped: {exc}\n")
        return
    out.mkdir(parents=True, exist_ok=True)
    every = max(args.every, 30)  # be gentle: the cam only refreshes every 30-60 s anyway

    etag = None
    saved = 0
    while True:
        data, etag = fetch_still(url, etag)
        if data:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            (out / f"{ts}.jpg").write_bytes(data)
            print(f"saved {ts}.jpg ({len(data)} bytes)", flush=True)
            saved += 1
            if args.max_frames is not None and saved >= args.max_frames:
                return
        time.sleep(every)


if __name__ == "__main__":
    main()
