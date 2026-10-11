# Katmai: three-camera local ML test

Park slug: `katmai`. Timezone: `America/Anchorage`. Initial prediction species:
**Brown bear (`Ursus arctos`)**. This is a SYNTHETIC demonstration, not a model
trained on observations from the selected camera.

## Selected cameras

The initial user-selected camera was Brooks Falls Low:
https://www.youtube.com/watch?v=EwTH5yY7Mks

On 2026-10-10, the collector resolved the title as **LIVE Brooks Falls Brown Bears
Low | explore.org**, with YouTube reporting `live_status=is_live`. A bounded
one-frame collection succeeded at 17:46:38 UTC. This verifies broadcast access;
it does not independently verify when the scene was recorded. Brooks Falls and
River Watch were added from the current NPS webcam pages on the same date. The
three names, locations, NPS pages, and YouTube URLs are stored in
`config/katmai_cameras.json`.

### Collect the YouTube cameras (PowerShell)

From `worker/`, install the optional resolver once after the normal requirements:

```powershell
uv pip install --python .\.venv\Scripts\python.exe --link-mode=copy -r requirements-youtube.txt
```

It uses yt-dlp and an existing Deno, Node, or Bun runtime (this laptop uses Bun).
List the cameras and then collect all three concurrently:

```powershell
.\.venv\Scripts\python.exe -m animal_worker.still_poller --park katmai --list-cameras
.\.venv\Scripts\python.exe -m animal_worker.katmai_multi_poller --every 60
```

Press Ctrl+C to stop all three. For one frame from each camera, add
`--max-frames 1`. Each camera has its own folder below `sample_videos/katmai/`.
To collect only River Watch, for example:

```powershell
.\.venv\Scripts\python.exe -m animal_worker.still_poller --park katmai --camera-id river-watch --every 60
```

The collector keeps decoding between saves to avoid a backlog; it consumes
network/video continuously even though it saves only one image per interval.
The minimum save interval is 30 seconds. It stops on errors rather than retrying
indefinitely. A stopped/expired broadcast requires restarting the command to
resolve a new stream URL. It refuses videos YouTube does not report as live.

`frames.jsonl` beside each camera's images records the public source URL, title, park,
camera, video ID, format, and UTC capture time. Observation time remains unknown;
the stream can have latency or show rebroadcast footage. Signed media URLs are
neither logged nor stored. Files in this folder are gitignored. This command
collects images; it does not classify species, update predictions, or write to
Supabase. The direct worker source still expects a media file/URL, so passing a
YouTube watch URL to `animal_worker.main` is not supported by this change.

Verification: 63 worker tests passed, including fake-stream tests for interval
sampling, metadata, clean shutdown, and no calls to a live camera during tests.
The separate one-frame integration test saved and visually verified a 1280x720
JPEG from the selected broadcast.

NPS camera directory: https://www.nps.gov/katm/learn/photosmultimedia/webcams.htm
(read 2026-10-10). It lists these cameras:

| Camera | NPS page |
|---|---|
| Brooks Falls | https://www.nps.gov/katm/learn/photosmultimedia/brown-bear-salmon-cam-brooks-falls.htm |
| Brooks Falls Low | https://www.nps.gov/katm/learn/photosmultimedia/brooks-falls-low-camera.htm |
| Riffles | https://www.nps.gov/katm/learn/photosmultimedia/riffles-bearcam.htm |
| River Watch | https://www.nps.gov/katm/learn/photosmultimedia/river-watch-cam.htm |
| Dumpling Mountain | https://www.nps.gov/katm/learn/photosmultimedia/dumpling-mountain-cam.htm |
| Naknek River | https://www.nps.gov/katm/learn/photosmultimedia/naknek-river-cam.htm |

NPS says bearcam season is typically late June through early October, with
highlights in the off-season. A viewing page is not evidence of a live observation.

The detection worker uses OpenCV on video files/direct media URLs. For detection tests, use a local clip you
have permission to process and pass the separate Katmai species file:

```powershell
# From worker/, after installing worker dependencies:
.\.venv\Scripts\python.exe -m animal_worker.main --source sample_videos/katmai/test.mp4 --camera "Brooks Falls Low" --park katmai --species-file species_katmai.json --dry-run
```

This example path is a placeholder; provide your own permitted local clip. The
worker virtual environment is separate from `ml/.venv`.

### Downloaded bear detection smoke-test clip

A public-domain NPS clip is available locally at
`worker/sample_videos/nps/yellowstone-grizzly-early-spring.mp4` (50 seconds,
14,186,221 bytes, downloaded 2026-10-10). Source and credit: [Grizzly Bear
(early spring), NPS/Neal Herbert](https://www.nps.gov/media/video/view.htm?id=DCE37092-155D-451F-67F448AC5DE819B0).

It is from **Yellowstone**, not Katmai. Test it with the Katmai candidate list
while keeping the source park and camera label accurate. From `worker/`:

```powershell
.\.venv\Scripts\python.exe -m animal_worker.main --source sample_videos/nps/yellowstone-grizzly-early-spring.mp4 --camera "NPS Yellowstone Bear Test (replay)" --park yellowstone --species-file species_katmai.json --fps 0.2 --min-confidence 0.8 --dry-run
```

This samples roughly one frame every five seconds for a quick CPU test. BioCLIP
downloads pretrained weights on first use. `--dry-run` prints detections without
database writes. Recorded detections are not synthetic, but they also are not
current live sightings or Katmai training data.

Verified on this Windows laptop with CPU PyTorch on 2026-10-10: the initial
0.5 threshold logged Brown bear at 94% and Coyote at 51%. A frame at 10 seconds
was visually inspected and shows a bear. Repeating at threshold 0.8 completed
successfully and logged only Brown bear at 94%. This is a one-clip smoke test,
not an accuracy estimate, and the model score is not calibrated accuracy.
The stricter threshold can suppress correct low-scoring detections too.
The second run took roughly 13 seconds including model load and used cached
BioCLIP weights. No database writes occurred.

## User-provided Katmai screenshot test (2026-10-10)

Input: `worker/sample_videos/katmai/user-screenshot-2026-10-10-133420.png`,
supplied by the user from the selected YouTube camera. A bear is visible in the
foreground. The saved image was processed locally; stream live status and the
actual observation timestamp were not independently verified.

- YOLO correctly labeled the foreground animal `bear`, score 0.938712,
  box `(430, 751, 820, 1040)` in the 1908 x 1081 image.
- BioCLIP with `species_katmai.json` incorrectly chose `Coyote` at 0.999614.
  The 0.8 threshold did not reject this error. These scores are not calibrated
  accuracy, and thresholding alone does not solve species confusion.
- Raw results and the review are saved in the gitignored
  `worker/sample_videos/katmai/screenshot-test-result.json`. No database writes.
- The worker now preserves YOLO's broad class label and restricts BioCLIP to a
  compatible group. A YOLO `bear` result at Katmai maps to brown bear instead of
  being allowed to become a coyote. This still needs evaluation on more labeled
  positive and negative images.

## Local prediction commands (PowerShell)

From `knighthacks2026/ml` with the existing ML environment:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe evaluate.py --park katmai
.\.venv\Scripts\python.exe predict.py --park katmai --local-only --no-sample
```

Output: `ml/out/predictions.json` (gitignored). `--local-only` skips database
access even if credentials are present; `--no-sample` avoids writing the shared
frontend sample file. No credentials are needed.

The JSON retains `synthetic`, `note`, `generated_at`, and `predictions`, and adds
`park`, `timezone`, and the selected `source_url`. Each prediction contains
`species`, `scientific_name`, `camera`, UTC `predicted_for`, and `probability`.
All timestamps are UTC; training hours are computed in the park timezone.

## Species and model assumptions

The full user-provided NPSpecies KATM export is stored at
`worker/reference/katmai/npspecies_full.csv`. It has 1,050 rows; the local
approved/present summary contains 762 species, including 35 mammals. This is an
inventory reference and is not used directly as the classifier candidate list.

`worker/species_katmai.json` remains a curated BioCLIP list: six mammals plus a
small set of approved/present gull, eagle, raven, merganser, and duck candidates
for the Brooks Falls test camera. Park occurrence does not mean
these species are likely at Brooks Falls Low. NPS confirms brown bears as `Ursus arctos`:
https://www.nps.gov/katm/learn/nature/coastal-brown-bears.htm

Saved frames can be scanned without Supabase from `worker/`:

```powershell
.\.venv\Scripts\python.exe -m animal_worker.folder_scanner --input sample_videos/katmai
```

The scanner uses overlapping 512-pixel tiles and a lower threshold only for
small birds. Other animal classes retain a stricter threshold to reduce water
and foliage false positives. It writes a gitignored local `sightings.json`.
Birds remain `Bird (unidentified)` by default; exact bird naming can be tried
with `--identify-bird-species`, but is experimental. Scores are not calibrated
accuracy.

The supplied example prediction JSON is stored at
`ml/reference/predictions.example.json`, explicitly labeled synthetic and
reference-only. Current local predictions remain in the gitignored
`ml/out/predictions.json` until Supabase works.

Prediction initially covers only brown bear. `ml/parks.py` deliberately invents
a midday profile and 10 events per day to exercise the pipeline. Those settings
are NOT measured animal behaviour. The original Yellowstone configuration is
still the default; Katmai is selected explicitly with `--park katmai`.

## Backend handoff

- Create a Katmai camera with `park='katmai'`, an agreed name, and its database UUID.
- Ensure the species row uses `scientific_name='Ursus arctos'`, not a separate
  Yellowstone grizzly label.
- Keep observation timestamps in UTC. Real training needs actual observation
  times and monitoring periods, rather than upload times from replayed clips.
- Agree on a synthetic-data marker before publishing synthetic forecasts to the
  database: the current `predictions` table does not store the JSON's synthetic flag.
- Local rows use names. Database writes resolve them to UUIDs and filter cameras
  to the selected park. Do not enable writes until the mappings are verified.
- The seed generator still produces Yellowstone seed SQL; do not use it to seed
  Katmai without a separate coordinated change.

Add measured sighting histories after the three-camera collection and detection tests work.

## Public historical occurrence analysis

`fetch_gbif.py` queries the official GBIF occurrence API for coordinate-bearing
`Ursus arctos` records from 2000 onward within a documented rectangular Katmai
regional envelope. The envelope is centered around the NPS-published Katmai
coordinates and is not the legal park boundary. The downloaded JSON is written
to the gitignored `ml/out/katmai_brown_bear_gbif.json` with the exact filters,
taxon match, retrieval time, record licenses, dataset keys, and source URL.

From `ml/`:

```powershell
.\.venv\Scripts\python.exe fetch_gbif.py
.\.venv\Scripts\python.exe fetch_weather.py
.\.venv\Scripts\python.exe katmai_features.py
.\.venv\Scripts\python.exe katmai_analysis.py
```

The 2026-10-10 run downloaded 738 unique records dated from 2001 through 2026.
The resulting report keeps their monthly distribution separate from the camera
detection rates. GBIF data is opportunistic: record counts reflect access,
observer effort, reporting, and publication as well as animal presence. They
must not be interpreted as population estimates or calibrated probabilities.
The generated JSON and Markdown reports remain local in `ml/out/`.

NASA POWER daily point data adds temperature, daily minimum and maximum
temperature, precipitation, relative humidity, and wind speed at the
NPS-published Katmai coordinate. `katmai_features.py` calculates approximate
daylight from latitude and day of year, then creates one row per day with the
weather values and exact-date GBIF record count. The 2026-10-10 run produced
9,415 rows from 2001-01-01 through 2026-10-11 and matched 731 GBIF records across
280 observation days. NASA POWER is gridded data for one point rather than a
camera weather station, and a date without a GBIF record is not a confirmed
absence. The feature table is suitable for exploration, but not for training a
calibrated bear-presence model without standardized survey-effort or absence data.

## Reviewed detector experiment (2026-10-10)

The three cameras supplied 402 captured frames. A no-cooldown candidate scan
produced 733 boxes, all of which were reviewed. The final manifest accepts 495
boxes (300 bear and 195 bird) and rejects 238 false detections. The exported YOLO
dataset contains 217 training, 61 validation, and 40 held-out test images,
including scenery-only negatives.

The selected model is
`worker/training/katmai/runs/bear-bird-v3-waterfall-negatives/weights/best.pt`,
with a copy at `worker/training/katmai/current.pt`. It adds five Brooks Falls Low
waterfall frames as hard negatives. On the held-out test set, bear precision was
0.699, recall 0.548, mAP50 0.589, and mAP50-95 0.413. Bird precision was 0.739,
recall 0.228, mAP50 0.281, and mAP50-95 0.101. The known Brooks Falls Low bear
scores 0.93, while all five waterfall test frames produce no detections even at
a 0.10 threshold. Local scans use `--bear-confidence 0.40` and
`--bird-confidence 0.40`. Bird detection remains experimental and needs examples
from more times, weather, distances, and camera views.
