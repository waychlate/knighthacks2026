"""Frame capture. Works with a video file, webcam index, RTSP/HLS/HTTP URL."""

from __future__ import annotations

import subprocess
import time
from collections.abc import Iterator

from .still_poller import fetch_still


def frames(source: str, fps: float = 1.0) -> Iterator[tuple[float, "np.ndarray"]]:
    """Yield (timestamp, BGR frame) roughly `fps` times per second.

    For files we skip frames by position so processing is not tied to wall-clock
    speed; for live sources we simply drop frames until the next sample is due.
    """
    import cv2

    cap = cv2.VideoCapture(int(source) if source.isdigit() else source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {source}")

    native_fps = cap.get(cv2.CAP_PROP_FPS) or 0
    is_file = cap.get(cv2.CAP_PROP_FRAME_COUNT) > 0
    step = max(1, round(native_fps / fps)) if (is_file and native_fps) else 1
    next_due = 0.0
    index = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            index += 1
            now = time.time()
            if is_file:
                if index % step:
                    continue
            elif now < next_due:
                continue
            next_due = now + 1.0 / fps
            yield now, frame
    finally:
        cap.release()


def _decode(data: bytes):
    import cv2
    import numpy as np

    return cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)


def image_frames(url, every=60.0, fetch=fetch_still, decode=_decode, sleep=time.sleep, clock=time.time):
    """Poll a still-image URL and yield (timestamp, BGR frame) for each new image.

    Polls no faster than every 30 s. Unchanged images (same ETag) are skipped; any
    fetch error propagates and stops the worker rather than retrying in a tight loop.
    """
    every = max(every, 30.0)
    etag = None
    while True:
        data, etag = fetch(url, etag)
        if data:
            yield clock(), decode(data)
        sleep(every)


DIRECT_SUFFIXES = (".m3u8", ".mpd", ".mp4", ".webm", ".ts")


def resolve_stream(url, run=subprocess.run):
    """Direct media URL for a stream page (YouTube etc.) via yt-dlp; direct media URLs pass through."""
    if url.lower().split("?")[0].endswith(DIRECT_SUFFIXES):
        return url
    out = run(["yt-dlp", "--no-playlist", "-f", "best[height<=720]/best", "-g", url],
              capture_output=True, text=True, timeout=90)
    lines = out.stdout.split()
    if out.returncode or not lines:
        raise RuntimeError(f"yt-dlp could not resolve {url}: {out.stderr.strip()[-300:]}")
    return lines[0]


def grab_frame(media_url, run=subprocess.run):
    """One JPEG frame from a media URL or file, via ffmpeg."""
    out = run(["ffmpeg", "-loglevel", "error", "-i", media_url, "-frames:v", "1", "-f", "image2pipe", "-vcodec", "mjpeg", "-"],
              capture_output=True, timeout=90)
    if out.returncode or not out.stdout:
        raise RuntimeError(f"ffmpeg could not read a frame: {out.stderr.decode(errors='replace').strip()[-300:]}")
    return out.stdout


def stream_frames(url, every=60.0, resolve=resolve_stream, grab=grab_frame, decode=_decode, sleep=time.sleep, clock=time.time):
    """Sample one frame from a live stream (YouTube/HLS page URL) every `every` seconds, never faster than 30 s.

    The direct stream URL expires, so on a failed grab we resolve again once; a second failure
    propagates and stops the worker rather than retrying in a tight loop.
    """
    every = max(every, 30.0)
    media = None
    while True:
        try:
            media = media or resolve(url)
            data = grab(media)
        except Exception:
            media = resolve(url)
            data = grab(media)
        yield clock(), decode(data)
        sleep(every)
