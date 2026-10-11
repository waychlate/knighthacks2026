import shutil
import subprocess
from datetime import date
from types import SimpleNamespace

import pytest

from animal_worker.capture import grab_frame, resolve_stream, stream_frames
from animal_worker.main import default_source_kind, in_bear_season, species_file_for


def fake_run(stdout="", code=0, stderr=""):
    calls = []

    def run(cmd, **kw):
        calls.append(cmd)
        return SimpleNamespace(stdout=stdout, returncode=code, stderr=stderr)

    run.calls = calls
    return run


def test_direct_media_url_skips_yt_dlp():
    run = fake_run()
    assert resolve_stream("https://x.test/live/index.m3u8?token=1", run=run) == "https://x.test/live/index.m3u8?token=1"
    assert run.calls == []


def test_page_url_is_resolved_with_yt_dlp():
    run = fake_run(stdout="https://cdn.test/direct.m3u8\n")
    assert resolve_stream("https://www.youtube.com/live/abc", run=run) == "https://cdn.test/direct.m3u8"
    assert run.calls[0][0] == "yt-dlp"


def test_yt_dlp_failure_raises_with_reason():
    with pytest.raises(RuntimeError, match="not available"):
        resolve_stream("https://www.youtube.com/live/abc", run=fake_run(code=1, stderr="This live stream recording is not available."))


def test_stream_frames_enforces_min_interval_and_resolves_once():
    sleeps, resolved = [], []

    def resolve(u):
        resolved.append(u)
        return "direct"

    it = stream_frames("page", every=5, resolve=resolve, grab=lambda m: b"jpg", decode=lambda d: "frame", sleep=sleeps.append, clock=lambda: 1.0)
    assert [next(it), next(it)] == [(1.0, "frame"), (1.0, "frame")]
    assert sleeps == [30.0] and resolved == ["page"]


def test_stream_frames_reresolves_once_then_gives_up():
    resolved = []
    state = {"n": 0}

    def grab(m):
        state["n"] += 1
        if m == "stale":
            raise RuntimeError("expired")
        return b"jpg"

    def resolve(u):
        resolved.append(u)
        return "stale" if len(resolved) == 1 else "fresh"

    it = stream_frames("page", resolve=resolve, grab=grab, decode=lambda d: "frame", sleep=lambda s: None, clock=lambda: 2.0)
    assert next(it) == (2.0, "frame") and resolved == ["page", "page"]

    def always_bad(m):
        raise RuntimeError("down")

    with pytest.raises(RuntimeError):
        next(stream_frames("page", resolve=lambda u: "x", grab=always_bad, sleep=lambda s: None))


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_grab_frame_reads_a_jpeg_with_real_ffmpeg(tmp_path):
    clip = tmp_path / "t.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=64x48:rate=5", "-t", "1", str(clip)], check=True)
    assert grab_frame(str(clip)).startswith(b"\xff\xd8")  # JPEG magic bytes


def test_bear_season_edges():
    assert in_bear_season(date(2026, 6, 15)) and in_bear_season(date(2026, 10, 31))
    assert not in_bear_season(date(2026, 6, 14)) and not in_bear_season(date(2026, 11, 1))


def test_default_source_kind():
    in_season, off = date(2026, 10, 10), date(2026, 12, 1)
    assert default_source_kind(True, False, "yellowstone", off) == "live"      # NPS still
    assert default_source_kind(False, True, "katmai", in_season) == "live"
    assert default_source_kind(False, True, "katmai", off) == "replay"          # old highlights
    assert default_source_kind(False, False, "katmai", in_season) == "replay"   # files


def test_species_file_follows_the_park():
    assert species_file_for("katmai").endswith("species-katmai.json")
    assert species_file_for("yellowstone").endswith("species.json")
    assert species_file_for("katmai", "mine.json") == "mine.json"
