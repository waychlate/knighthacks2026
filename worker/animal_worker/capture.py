"""Frame capture. Works with a video file, webcam index, RTSP/HLS/HTTP URL."""

from __future__ import annotations

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
