"""YouTube collection checks that never contact a camera or load ML models."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from animal_worker.youtube_poller import StreamInfo, collect_frames, is_youtube_url, resolve_youtube


WATCH_URL = "https://www.youtube.com/watch?v=EwTH5yY7Mks"
MEDIA_URL = "https://media.example.test/live.m3u8?signature=private-token"
START = datetime(2026, 10, 10, 17, 34, 20, tzinfo=timezone.utc)


def stream(live_status="is_live"):
    return StreamInfo(
        source_url=WATCH_URL,
        url=MEDIA_URL,
        title="Katmai test stream",
        video_id="EwTH5yY7Mks",
        live_status=live_status,
    )


class FakeCapture:
    """Each decoded frame advances elapsed time without sleeping."""

    def __init__(self, times, opened=True):
        self.times = iter(times)
        self.opened = opened
        self.elapsed = 0
        self.reads = 0
        self.released = False
        self.urls = []
        self.saved = []

    def factory(self, url):
        self.urls.append(url)
        return self

    def isOpened(self):
        return self.opened

    def read(self):
        self.reads += 1
        try:
            self.elapsed = next(self.times)
        except StopIteration:
            return False, None
        return True, f"frame-at-{self.elapsed}"

    def release(self):
        self.released = True

    def write(self, path, frame):
        self.saved.append((path, frame))
        path.write_text(frame, encoding="utf-8")
        return True

    def clock(self):
        return self.elapsed

    def utc_now(self):
        return START + timedelta(seconds=self.elapsed)


def collect(cap, out, **kwargs):
    return collect_frames(
        kwargs.pop("stream", stream()),
        out,
        capture_factory=cap.factory,
        write_frame=kwargs.pop("write_frame", cap.write),
        clock=cap.clock,
        utc_now=cap.utc_now,
        log=lambda *args, **kw: None,
        **kwargs,
    )


def metadata(out):
    return [json.loads(line) for line in (out / "frames.jsonl").read_text(encoding="utf-8").splitlines()]


@pytest.mark.parametrize("url", [
    WATCH_URL,
    "https://youtube.com/watch?v=EwTH5yY7Mks",
    "https://m.youtube.com/watch?v=EwTH5yY7Mks",
    "https://youtu.be/EwTH5yY7Mks",
])
def test_recognizes_youtube_hosts(url):
    assert is_youtube_url(url)


@pytest.mark.parametrize("url", [
    "https://youtube.com.evil.example/watch?v=EwTH5yY7Mks",
    "https://notyoutube.com/watch?v=EwTH5yY7Mks",
    "https://example.test/?url=https://youtube.com/watch?v=EwTH5yY7Mks",
    "file:///youtube.com/watch?v=EwTH5yY7Mks",
    "sample_videos/katmai/bear.mp4",
])
def test_rejects_other_hosts_and_local_sources(url):
    assert not is_youtube_url(url)


class FakeDownloader:
    def __init__(self, info):
        self.info = info
        self.options = None
        self.request = None
        self.exited = False

    def factory(self, options):
        self.options = options
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.exited = True

    def extract_info(self, url, download):
        self.request = (url, download)
        return self.info


def live_info(**changes):
    return {
        "url": MEDIA_URL,
        "title": "Katmai test stream",
        "id": "EwTH5yY7Mks",
        "live_status": "is_live",
        "protocol": "m3u8_native",
        "vcodec": "avc1",
        **changes,
    }


def test_resolver_preserves_watch_url_and_resolves_live_media_without_downloading():
    downloader = FakeDownloader(live_info())
    result = resolve_youtube(WATCH_URL, ydl_factory=downloader.factory)

    assert result == stream()
    assert downloader.request == (WATCH_URL, False)
    assert downloader.exited


@pytest.mark.parametrize("status", ["not_live", "was_live", "post_live", "is_upcoming", None])
def test_resolver_rejects_offline_archived_and_upcoming_video(status):
    downloader = FakeDownloader(live_info(live_status=status))
    with pytest.raises((ValueError, RuntimeError)):
        resolve_youtube(WATCH_URL, ydl_factory=downloader.factory)
    assert downloader.exited


@pytest.mark.parametrize("url", [None, ""])
def test_resolver_requires_a_playable_media_url(url):
    downloader = FakeDownloader(live_info(url=url))
    with pytest.raises((ValueError, RuntimeError)):
        resolve_youtube(WATCH_URL, ydl_factory=downloader.factory)


@pytest.mark.parametrize("changes", [
    {"url": "file:///private/frame.mp4"},
    {"protocol": "https"},
    {"vcodec": "none"},
])
def test_resolver_rejects_non_hls_and_audio_only_formats(changes):
    downloader = FakeDownloader(live_info(**changes))
    with pytest.raises((ValueError, RuntimeError)):
        resolve_youtube(WATCH_URL, ydl_factory=downloader.factory)


def test_collection_drains_intermediate_frames_and_saves_current_frames(tmp_path):
    cap = FakeCapture([0, 1, 59, 60])
    out = tmp_path / "katmai"

    assert collect(cap, out, every=60, max_frames=2) == 2
    assert cap.urls == [MEDIA_URL]
    assert cap.reads == 4
    assert cap.released
    assert [frame for _, frame in cap.saved] == ["frame-at-0", "frame-at-60"]
    assert len(list(out.glob("*.jpg"))) == 2
    assert all(path.suffix == ".jpg" for path, _ in cap.saved)

    rows = metadata(out)
    assert len(rows) == 2
    assert [datetime.fromisoformat(row["captured_at"]) for row in rows] == [START, START + timedelta(seconds=60)]
    for row in rows:
        assert row["park"] == "katmai"
        assert row["camera"] == "Brooks Falls Low"
        assert row["source_url"] == WATCH_URL
        assert row["source_kind"] == "live"
        assert row["observation_time"] is None
    assert MEDIA_URL not in (out / "frames.jsonl").read_text(encoding="utf-8")
    assert "private-token" not in (out / "frames.jsonl").read_text(encoding="utf-8")


def test_collection_enforces_thirty_second_minimum(tmp_path):
    cap = FakeCapture([0, 1, 29, 30])
    assert collect(cap, tmp_path, every=1, max_frames=2) == 2
    assert [frame for _, frame in cap.saved] == ["frame-at-0", "frame-at-30"]


def test_slow_frames_reset_interval_instead_of_catching_up(tmp_path):
    cap = FakeCapture([0, 70, 120, 130])
    assert collect(cap, tmp_path, every=60, max_frames=3) == 3
    assert [frame for _, frame in cap.saved] == ["frame-at-0", "frame-at-70", "frame-at-130"]


def test_collection_preserves_camera_park_and_replay_label(tmp_path):
    cap = FakeCapture([0])
    assert collect(cap, tmp_path, stream=stream("was_live"), park="other-park", camera="Archive camera", max_frames=1) == 1
    row = metadata(tmp_path)[0]
    assert row["park"] == "other-park"
    assert row["camera"] == "Archive camera"
    assert row["source_kind"] == "replay"
    assert row["observation_time"] is None


@pytest.mark.parametrize("max_frames", [0, -1])
def test_invalid_frame_limit_rejected_before_opening_capture(tmp_path, max_frames):
    cap = FakeCapture([0])
    with pytest.raises(ValueError):
        collect(cap, tmp_path, max_frames=max_frames)
    assert cap.urls == []


def test_unopenable_capture_raises_and_releases(tmp_path):
    cap = FakeCapture([], opened=False)
    with pytest.raises(RuntimeError):
        collect(cap, tmp_path, max_frames=1)
    assert cap.released


def test_read_failure_raises_instead_of_silently_reporting_success(tmp_path):
    cap = FakeCapture([0])
    with pytest.raises(RuntimeError):
        collect(cap, tmp_path, max_frames=2)
    assert cap.released
    assert len(metadata(tmp_path)) == 1


def test_write_failure_raises_and_releases(tmp_path):
    cap = FakeCapture([0])
    with pytest.raises(OSError):
        collect(cap, tmp_path, max_frames=1, write_frame=lambda path, frame: False)
    assert cap.released


@pytest.mark.parametrize("url_args", [[], ["--url", WATCH_URL]])
def test_katmai_cli_routes_youtube_source_to_collector(tmp_path, monkeypatch, url_args):
    from animal_worker import still_poller, youtube_poller

    monkeypatch.chdir(tmp_path)
    calls = {}

    def resolve(url):
        calls["url"] = url
        return stream()

    def collect_cli(info, out, **kwargs):
        calls.update(info=info, out=out, options=kwargs)
        return 2

    def no_still_fetch(*args, **kwargs):
        pytest.fail("A YouTube watch URL must not be fetched as a JPEG")

    monkeypatch.setattr(youtube_poller, "resolve_youtube", resolve)
    monkeypatch.setattr(youtube_poller, "collect_frames", collect_cli)
    monkeypatch.setattr(still_poller, "fetch_still", no_still_fetch)
    still_poller.main(["--park", "katmai", "--every", "60", "--max-frames", "2", *url_args])

    assert calls["url"] == WATCH_URL
    assert calls["info"] == stream()
    assert calls["out"].as_posix() == "sample_videos/katmai/brooks-falls-low"
    assert calls["options"]["park"] == "katmai"
    assert calls["options"]["camera"] == "Brooks Falls Low"
    assert calls["options"]["every"] == 60
    assert calls["options"]["max_frames"] == 2


def test_named_katmai_camera_routes_to_its_url_and_folder(tmp_path, monkeypatch):
    from animal_worker import still_poller, youtube_poller
    from animal_worker.katmai_cameras import KATMAI_CAMERAS

    monkeypatch.chdir(tmp_path)
    calls = {}

    def resolve(url):
        calls["url"] = url
        return stream()

    def collect_cli(info, out, **kwargs):
        calls.update(out=out, options=kwargs)
        return 1

    monkeypatch.setattr(youtube_poller, "resolve_youtube", resolve)
    monkeypatch.setattr(youtube_poller, "collect_frames", collect_cli)
    still_poller.main(["--park", "katmai", "--camera-id", "river-watch", "--max-frames", "1"])

    selected = KATMAI_CAMERAS["river-watch"]
    assert calls["url"] == selected.youtube_url
    assert calls["out"].as_posix() == "sample_videos/katmai/river-watch"
    assert calls["options"]["camera"] == "River Watch"


def test_default_yellowstone_cli_still_saves_jpeg(tmp_path, monkeypatch):
    from animal_worker import still_poller, youtube_poller

    monkeypatch.chdir(tmp_path)
    calls = []

    def fetch(url, etag):
        calls.append((url, etag))
        return b"test-jpeg", "etag-1"

    def no_youtube(*args, **kwargs):
        pytest.fail("The Yellowstone default must keep using the JPEG poller")

    monkeypatch.setattr(still_poller, "fetch_still", fetch)
    monkeypatch.setattr(youtube_poller, "resolve_youtube", no_youtube)
    still_poller.main(["--max-frames", "1"])

    assert calls == [(still_poller.URL, None)]
    images = list((tmp_path / "sample_videos" / "yellowstone").glob("*.jpg"))
    assert len(images) == 1
    assert images[0].read_bytes() == b"test-jpeg"
