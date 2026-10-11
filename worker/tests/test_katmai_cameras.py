from types import SimpleNamespace

from animal_worker.katmai_cameras import KATMAI_CAMERAS
from animal_worker.katmai_multi_poller import run_cameras


def test_three_unique_katmai_cameras_are_configured():
    assert set(KATMAI_CAMERAS) == {"brooks-falls-low", "brooks-falls", "river-watch"}
    assert len({camera.youtube_url for camera in KATMAI_CAMERAS.values()}) == 3
    assert all(camera.youtube_url.startswith("https://www.youtube.com/watch?v=")
               for camera in KATMAI_CAMERAS.values())


def test_multi_poller_keeps_camera_output_separate(tmp_path):
    calls = []

    def resolve(url):
        return SimpleNamespace(video_id=url.rsplit("=", 1)[-1])

    def collect(stream, out, **options):
        calls.append((stream.video_id, out, options))
        return 2

    results = run_cameras(
        list(KATMAI_CAMERAS.values()), tmp_path,
        max_frames=2, resolver=resolve, collector=collect, log=lambda message: None,
    )

    assert results == {camera_id: 2 for camera_id in KATMAI_CAMERAS}
    assert {path.name for _, path, _ in calls} == set(KATMAI_CAMERAS)
    assert {options["camera"] for _, _, options in calls} == {
        "Brooks Falls Low", "Brooks Falls", "River Watch",
    }
