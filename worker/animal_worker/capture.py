"""Frame capture. Works with a video file, webcam index, RTSP/HLS/HTTP URL."""

from __future__ import annotations

import time
from collections.abc import Iterator


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
