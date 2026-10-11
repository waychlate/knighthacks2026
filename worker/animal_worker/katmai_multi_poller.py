"""Collect all configured Katmai YouTube cameras concurrently."""

from __future__ import annotations

import argparse
import threading
from concurrent.futures import FIRST_EXCEPTION, ThreadPoolExecutor, wait
from pathlib import Path

from .katmai_cameras import KATMAI_CAMERAS
from .youtube_poller import collect_frames, resolve_youtube


def run_cameras(cameras, out: Path, *, every=60, max_frames=None,
                resolver=resolve_youtube, collector=collect_frames, log=print,
                on_frame=None):
    """Run one collector per camera and stop all when interrupted or one fails."""
    stop_event = threading.Event()

    def run(camera):
        stream = resolver(camera.youtube_url)
        log(f"[{camera.name}] connected ({stream.video_id})")
        count = collector(
            stream,
            out / camera.id,
            park="katmai",
            camera=camera.name,
            every=every,
            max_frames=max_frames,
            stop_event=stop_event,
            on_frame=on_frame,
            log=lambda message: log(f"[{camera.name}] {message}"),
        )
        return camera.id, count

    executor = ThreadPoolExecutor(max_workers=len(cameras))
    futures = [executor.submit(run, camera) for camera in cameras]
    results = {}
    try:
        while futures:
            done, pending = wait(futures, timeout=0.5, return_when=FIRST_EXCEPTION)
            for future in done:
                camera_id, count = future.result()
                results[camera_id] = count
            if not pending:
                return results
            futures = list(pending)
    except BaseException:
        stop_event.set()
        raise
    finally:
        stop_event.set()
        executor.shutdown(wait=True, cancel_futures=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="sample_videos/katmai", help="parent output folder")
    parser.add_argument("--every", type=int, default=60, help="seconds between saved frames (min 30)")
    parser.add_argument("--max-frames", type=int, help="frames per camera; default runs until Ctrl+C")
    args = parser.parse_args(argv)
    if args.every <= 0 or (args.max_frames is not None and args.max_frames < 1):
        parser.error("--every and --max-frames must be positive")
    cameras = list(KATMAI_CAMERAS.values())
    print("Starting: " + ", ".join(camera.name for camera in cameras), flush=True)
    try:
        run_cameras(cameras, Path(args.out), every=args.every, max_frames=args.max_frames,
                    log=lambda line: print(line, flush=True))
    except KeyboardInterrupt:
        print("All Katmai collectors stopped.", flush=True)
    except (RuntimeError, OSError, ValueError) as exc:
        parser.exit(1, f"Katmai collectors stopped: {exc}\n")


if __name__ == "__main__":
    main()
