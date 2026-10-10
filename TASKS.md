# TASKS (pipeline run)

Backlog for the **`overnight/pipeline`** branch. Follow "Unattended / overnight mode" in CLAUDE.md. Work top to bottom. Mark a task `[x]` only when every acceptance check passed; otherwise leave it and log the blocker in `PROGRESS.md`.

The web/social run has its own file, `TASKS-web.md`, on `overnight/web-social`. Do not do its tasks.

## Ownership

- **You own:** `/worker`, `/ml`, `supabase/schema.sql`, `supabase/seed.sql`, `PROGRESS.md`, and `web/public/predictions.sample.json` (output only).
- **Do not touch:** the rest of `/web`, `supabase/social.sql`, `TASKS-web.md`, `PROGRESS-web.md`.

## Shared data contract (both runs rely on this)

- `sightings.source_kind text not null default 'replay' check (source_kind in ('live','replay'))`. Anything the worker logs from a recorded clip or seed data is `replay`; only a worker reading the live still is `live`.
- `cameras.park text not null default 'yellowstone'` (park slug; the web app uses it for per-park chat rooms).
- Camera-detected `sightings` are the only input to `/ml`. User comments and chat live in separate tables (`supabase/social.sql`, web-owned) and never go into `sightings`.
- Everything synthetic is labeled synthetic in code, data, UI and docs.

## Context for this run

- Chosen live source: NPS Yellowstone "North Entrance - Electric Peak", a still image at `https://www.nps.gov/webcams-yell/mammoth_electric.jpg` refreshed every 30-60 s. **The unattended run must not fetch that URL** (or any live URL). The user runs `worker/animal_worker/still_poller.py` by hand to collect frames into the gitignored `worker/sample_videos/yellowstone/`; you may read those frames.
- Species list for Yellowstone (edit `worker/species.json`): elk, American bison, pronghorn, mule deer, coyote, gray wolf, grizzly bear, black bear, bighorn sheep, moose, bald eagle, trumpeter swan, sandhill crane, red fox. Common and scientific names; this list is from model knowledge, not checked against NPSpecies.

## 1. Environment
- [ ] Create `worker/.venv` with Python 3.12 (`uv python install 3.12` then `uv venv --python 3.12 worker/.venv`; the system Python 3.14 likely lacks wheels). Install `worker/requirements.txt` with the CUDA build of torch, falling back to CPU if CUDA fails.
- [ ] Download YOLO and BioCLIP weights into the default cache.
- Accept: `python -c "import torch, ultralytics, open_clip; print(torch.cuda.is_available())"` runs inside the venv. Record versions and the CUDA result in `PROGRESS.md`.

## 2. Make the worker testable without models
- [ ] Refactor `worker/animal_worker/main.py` so the per-frame logic is a function, e.g. `process_frame(frame, ts, detector, classifier, deduper, sink)`, with injected dependencies. Heavy imports stay lazy.
- [ ] pytest tests with fake detector/classifier/sink: logs a sighting, respects the dedupe cooldown, skips below-threshold classifications, handles frames with no detections.
- Accept: `python -m pytest` passes from `/worker` without torch/ultralytics importable.

## 3. Image-URL source
- [ ] Add a source mode for an `http(s)` image URL that polls every N seconds (default 60, minimum 30), reusing `fetch_still` from `still_poller.py` (User-Agent, ETag, stop on error). Tag sightings from it `source_kind='live'`; sightings from files/video are `replay`. Add a `--source-kind` override.
- [ ] Test against a local file or a local `http.server`, never a real third-party URL.
- Accept: pytest covers the polling loop with a fake fetcher and the `source_kind` assignment.

## 4. Verify the real pipeline (best effort)
- [ ] Download a few public-domain test clips/images into `worker/sample_videos/`: the Yellowstone bison clips in the NPS video library (nps.gov/yell/learn/photosmultimedia/vl_bisoncalves.htm, check each link works and the license says public domain) and USGS/NPS public-domain stills. Never download from YouTube. Record URL and license of each in `PROGRESS.md`; skip any item without an explicit public-domain label.
- [ ] Run the worker with `--dry-run` on those clips and on whatever frames exist in `worker/sample_videos/yellowstone/`. Confirm at least one correct `SIGHTING`. Tune BioCLIP prompts and `--min-confidence`, then record what worked, what did not, and speed (GPU and, if cheap, CPU) in `PROGRESS.md`. Small distant animals on the cam frames may not be detected; say so.
- Accept: documented result in `PROGRESS.md`. If weights or media can't be downloaded, mark blocked and move on.

## 5. Schema and seed data
- [ ] Edit `supabase/schema.sql` for the data contract above (`source_kind`, `cameras.park`). Keep it re-runnable.
- [ ] Generate `supabase/seed.sql` from the ML synthetic generator (`/ml`, not hand-written): Yellowstone cameras (Electric Peak plus two or three demo-only cameras, all `park='yellowstone'`), the species list, and synthetic sightings with `source_kind='replay'`. Comment clearly that it is synthetic.
- Accept: valid SQL in the schema's shape (review carefully; no database needed); the README says how to load and regenerate it.

## 6. ML: sighting predictions (`/ml`) (do last; cut first if short on time)
Goal: given a (synthetic, for now) sighting history, predict when each species is likely to be seen, e.g. "Predicting an elk around 6:30 AM near Electric Peak Cam".

- [ ] Scaffold `/ml`: `requirements.txt` (pandas, numpy, scikit-learn, pytest), `README.md`, `tests/`. Build task 5's generator here first if not done.
- [ ] `ml/synthetic.py`: ~14 days of sightings for the species in `worker/species.json` and 3 cameras, each species with a known time-of-day profile (e.g. elk at dawn/dusk), camera preference, weekday/weekend effect and noise. Fixed seed. CSV in the `Sighting` shape (species, camera, `seen_at` UTC, confidence). Labeled **synthetic** everywhere.
- [ ] Framing: per (species, camera, hour slot), the probability of at least one sighting in that hour.
- [ ] Models: (a) naive per-(species, camera) rate; (b) smoothed historical rate by hour (and weekday); (c) a scikit-learn model (gradient boosting or logistic regression) with hour sin/cos, weekday, species, camera, recent activity. Simple and explainable.
- [ ] Evaluation: temporal split (train earlier days, test the last 3; never shuffle across time). Brier score or log loss per model, plus hit rate: how often the top predicted hour for a species falls within +/-1 h of a real sighting. Write the table into `ml/README.md`.
- [ ] Recovery check: compare each model's learned hourly profile with the true generating profile and report the error. Be honest in the README that synthetic results are optimistic. If the learned model does not beat the baseline, say so and keep the simpler one.
- [ ] `ml/predict.py`: train, predict the next 24 hours, keep predictions above a probability threshold, write `Prediction` rows (see `supabase/schema.sql`) to `ml/out/predictions.json`. Write to Supabase only if keys are set; never require them.
- [ ] Copy a sample to `web/public/predictions.sample.json`, clearly marked sample/synthetic, with timestamps relative to "now". The web run reads it; do not edit any other `/web` file.
- Accept: `python -m pytest` passes in `/ml` (generator determinism, no leakage in the time split, probabilities in [0,1], output schema); `python ml/predict.py` runs with no keys; the metrics table exists.

## 7. Docs
- [ ] README: how to run the worker on a clip, on the live still (`--source <image URL>`), how to run the collector, and how the seed and ML data are generated. Short enough for a teammate to follow from a clean clone.
