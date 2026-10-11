"""Resolve a public YouTube live broadcast and save sampled frames locally."""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

@dataclass(frozen=True)
class StreamInfo:
    source_url: str
    url: str = field(repr=False)  # expiring signed media URL; never log or persist
    title: str
    video_id: str
    live_status: str
    format_id: str = ""


def is_youtube_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {
        "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
    }


def _js_runtimes() -> dict:
    """Use an already-installed runtime; do not install global tools."""
    for name in ("deno", "node", "bun"):
        path = shutil.which(name)
        if path:
            return {name: {"path": path}}
    bun = Path.home() / ".bun" / "bin" / "bun.exe"
    return {"bun": {"path": str(bun)}} if bun.is_file() else {}


class _QuietLogger:
    # Extractor diagnostics can include signed media URLs. Report safe errors below.
    def debug(self, message):
        pass

    def warning(self, message):
        pass

    def error(self, message):
        pass


def resolve_youtube(url: str, ydl_factory=None) -> StreamInfo:
    if not is_youtube_url(url):
        raise ValueError("Expected a youtube.com or youtu.be URL")
    if ydl_factory is None:
        try:
            from yt_dlp import YoutubeDL
        except ImportError:
            raise RuntimeError(
                'YouTube support is missing. Install worker/requirements-youtube.txt '
                'into the worker virtual environment.'
            ) from None
        ydl_factory = YoutubeDL
    options = {
        # One HLS video rendition. No audio/video merging or entire-video download.
        "format": "best*[protocol^=m3u8][vcodec!=none][height<=720]/best*[protocol^=m3u8][vcodec!=none]",
        "noplaylist": True,
        "skip_download": True,
        "live_from_start": False,
        "quiet": True,
        "no_warnings": True,
        "logger": _QuietLogger(),
        "socket_timeout": 20,
        "retries": 0,
        "extractor_retries": 0,
    }
    runtimes = _js_runtimes()
    if runtimes:
        options["js_runtimes"] = runtimes
    try:
        with ydl_factory(options) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception:
        raise RuntimeError(
            "Could not resolve the YouTube stream. Check that it is publicly available "
            "and live, and update yt-dlp if needed. No frames were downloaded."
        ) from None
    if not info or info.get("live_status") != "is_live":
        raise RuntimeError("This video is not currently reported live; refusing to label a replay as live.")
    media_url = info.get("url")
    if (not media_url or urlparse(media_url).scheme not in {"http", "https"}
            or info.get("vcodec") == "none"
            or not str(info.get("protocol", "")).startswith("m3u8")):
        raise RuntimeError("YouTube did not provide a usable HLS video stream.")
    return StreamInfo(url, media_url, info.get("title") or "YouTube live stream",
                      str(info.get("id", "")), "is_live", str(info.get("format_id", "")))


def open_video(url: str):
    # Native FFmpeg errors may expose signed URLs; provide our own clear error.
    os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"
    os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
    import cv2

    if hasattr(cv2, "setLogLevel"):
        cv2.setLogLevel(0)
    try:
        return cv2.VideoCapture(url, cv2.CAP_FFMPEG, [
            cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 20000,
            cv2.CAP_PROP_READ_TIMEOUT_MSEC, 20000,
        ])
    except cv2.error:
        raise RuntimeError("OpenCV could not open the resolved stream.") from None


def write_jpeg(path: Path, frame) -> bool:
    import cv2

    try:
        return cv2.imwrite(str(path), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    except cv2.error:
        return False


def collect_frames(stream: StreamInfo, out: Path, *, park="katmai",
                   camera="Brooks Falls Low", every=60, max_frames=None,
                   capture_factory=None, write_frame=None, clock=time.monotonic,
                   utc_now=lambda: datetime.now(timezone.utc), log=print,
                   stop_event=None) -> int:
    """Drain the stream continuously; save the first frame then every >=30 seconds.

    captured_at is receipt time, not a verified camera observation time. A live
    broadcast can itself show older footage. Stop on stream/write errors.
    """
    if max_frames is not None and max_frames < 1:
        raise ValueError("max_frames must be at least 1")
    if every <= 0:
        raise ValueError("every must be positive")
    every = max(every, 30)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    capture_factory = capture_factory or open_video
    write_frame = write_frame or write_jpeg
    cap = capture_factory(stream.url)
    count, next_due = 0, None
    try:
        if not cap.isOpened():
            raise RuntimeError("Could not open the resolved video stream. No frames saved.")
        while True:
            if stop_event is not None and stop_event.is_set():
                return count
            try:
                ok, frame = cap.read()
            except Exception:
                raise RuntimeError("Video stream read failed; collector stopped.") from None
            if not ok or frame is None:
                raise RuntimeError("Video stream ended or timed out; collector stopped. Saved frames remain on disk.")
            now = clock()
            if next_due is not None and now < next_due:
                continue
            captured = utc_now().astimezone(timezone.utc)
            name = captured.strftime("%Y%m%dT%H%M%S.%fZ") + ".jpg"
            path = out / name
            if not write_frame(path, frame):
                raise OSError("Could not save the captured frame")
            metadata = dict(
                file=name, park=park, camera=camera, captured_at=captured.isoformat(),
                observation_time=None, source_url=stream.source_url,
                video_id=stream.video_id, title=stream.title, format_id=stream.format_id,
                live_status=stream.live_status,
                source_kind="live" if stream.live_status == "is_live" else "replay",
                note="Captured broadcast frame; capture time is not verified observation time.",
            )
            with (out / "frames.jsonl").open("a", encoding="utf-8") as manifest:
                manifest.write(json.dumps(metadata) + "\n")
            count += 1
            log(f"saved {path}")
            if max_frames is not None and count >= max_frames:
                return count
            next_due = now + every
    finally:
        cap.release()
