# CLAUDE.md

Guidance for Claude Code when working in this repository (KnightHacks 2026 hackathon project).

## Project overview

**Animal Logger**: a wildlife sighting log for parks. Cameras placed in a park detect and identify animals; a web app/website shows a feed of recent sightings.

A visitor opens the app and sees a live log of recently seen animals. Each entry shows:

- **Species** (what animal was seen)
- **Camera** (which camera saw it, ideally with its location in the park)
- **Timestamp** (when it was seen)

### Stretch goal: sighting predictions

Store sightings in a database, analyze them, and train an ML model to find patterns in when and where species appear. Surface this to users as predictions, e.g. "Predicting a [bird species] around 2:30 PM."

## Current status

Update this section whenever it changes.

- **Done:**
  - **Worker:** capture (files, video, image URLs) -> YOLO -> BioCLIP -> dedupe -> Supabase, tested with fakes (14 tests). Ran on public-domain bison clips (CUDA); `worker/species.json` is the Yellowstone list.
  - **Web:** 3D globe landing page (MapLibre GL JS globe, Esri satellite imagery + AWS Terrarium 3D terrain, both fetched at runtime so it needs internet; park markers (green map pins; pings are circles, orange in a park, grey elsewhere) appear on zoom with a hover/tap card, and zooming in over a park opens its overview panel at the bottom; Yellowstone live still, Katmai with three explore.org live-video cams), user pings ("Drop ping" at your location, rounded to ~500 m, 24 h expiry, clustered on the globe, 1 per 5 min per device; sample pings show in Demo mode only), a PWA manifest with a placeholder icon (no service worker) leading to `#/park/:slug/{sightings,cameras,predictions,chat,analytics}`; old `#/cameras` and `#/analytics` redirect. Also: feed, cameras and camera pages with the Demo/Live toggle and bubble, per-park chat, comments, analytics page, error banner, and a prediction card (sample predictions from `/ml`, with a "tomorrow" chip). Lint, build, 17 vitest tests and a headless-Chromium check pass.
  - **Supabase SQL:** `schema.sql` (with `source_kind`, `cameras.park`), `social.sql`, and a synthetic `seed.sql`.
  - **`/ml`:** synthetic generator, three models, temporal-split evaluation, `predict.py` (10 tests). All on SYNTHETIC data; the simple hourly profile beat gradient boosting.
  - **Katmai local ML:** optional `--park katmai` predictions, `--local-only` output, and `worker/species_katmai.json`. A reviewed two-class Katmai detector identifies bears and birds; its local, gitignored weights are `worker/training/katmai/current.pt`. Waterfall hard negatives removed the known Brooks Falls Low false positive while retaining the reference bear at 0.93 confidence. A separate 147-image holdout collected afterward produced 100 detections across 84 frames; all six Brooks Falls Low detections were visually confirmed bears. Species-level BioCLIP labels remain experimental. `ml/katmai_analysis.py` combines frame-adjusted camera detection rates and 95% intervals with the NPS species inventory, while explicitly avoiding population or forecast claims from the short collection. See `ml/KATMAI.md`. ML suite has 18 tests.
  - **Katmai collector:** three named NPS-listed YouTube feeds are configured in `config/katmai_cameras.json`: Brooks Falls Low, Brooks Falls, and River Watch. `katmai_multi_poller` collects all three concurrently into separate folders; `still_poller --park katmai --camera-id ...` collects one. Both save JPEGs and UTC metadata locally. The folder scanner performs tiled detection, supports custom weights and optional BioCLIP bird identification, and writes local sightings. Review, dataset export, training, and clean annotation tools are included. Nothing publishes to Supabase without an explicit database run. Worker suite has 63 tests.
  - Both overnight branches are merged into `main`.
- **Not verified:**
  - Globe, terrain and pings on a real GPU and on a phone (only headless swiftshader and a mouse were tried; touch tap card and the PWA install untested). `supabase/pings.sql` has not been run against a real project.
  - Nothing has run against a real Supabase project (schema, seed, social tables, worker writes, realtime chat, `predict.py` write path).
  - The worker has not seen daylight frames from the live Electric Peak cam; YOLO may miss small distant animals. Species ID on hard clips (bison calves) is about 59% right.
  - Demo video playback in a real browser (only the `src` was checked).
- **Not started:** Vercel deploy; other parks; real accounts and moderation beyond the `is_hidden` flag.
- **Decided (2026-10-10):** live source is the NPS Yellowstone "North Entrance - Electric Peak" still. Demo uses recorded clips; the web app has a Demo/Live toggle. Social (per-park chat, comments on sightings) is added anonymously. Databricks is skipped.
- **Work split (24 h to go):** three people, no Claude Code for the two teammates. `TEAM.md` has the roles, branch rule and clock; guides are `docs/team/ml.md` (tiled detection, `ml/`, `worker/`), `docs/team/frontend.md` (`web/`, QA, screenshots) and `docs/team/integrator.md` (Supabase, Vercel, merges, demo). Everyone works on their own branch and never pushes straight to `main`. Finished task lists are in `docs/archive/`; run logs are in `docs/PROGRESS.md`.

### Stream source

Chosen: the NPS Yellowstone "North Entrance - Electric Peak" webcam, a JPEG at `https://www.nps.gov/webcams-yell/mammoth_electric.jpg` refreshed every 30-60 s. The user viewed the cam and the NPS disclaimer on 2026-10-10 and approved it. Credit NPS when showing its images. Poll no faster than every 30 s and send a descriptive User-Agent (see `worker/animal_worker/still_poller.py`).

**Katmai (updated 2026-10-10):** the three NPS/explore.org Brooks Falls cameras
are live video. Their names and current NPS-embedded YouTube links are stored in
`config/katmai_cameras.json`. The user starts
`python -m animal_worker.katmai_multi_poller --every 60` by hand to record the
feeds locally in separate camera folders. The web app shows the Katmai feeds in
Live mode. Outside bear season, the feeds may show highlights rather than current
observations. Nothing has been written to Supabase from a Katmai stream. Details,
test results, and capture provenance are in `ml/KATMAI.md`; older source research
is in `docs/archive/HANDOFF.md`.

**Unattended runs must not fetch the live URL or any other live stream, scrape any site, or contact anyone.** The user starts the still collector by hand to record frames into the gitignored `worker/sample_videos/yellowstone/`; unattended runs may read those frames. Develop and test against local files, a local test server, and mock data.

## Hackathon tracks

We are targeting these KnightHacks 2026 tracks. Keep them in mind when making design decisions.

- **Best First Time**: we are first-time hackers, so a complete, working, demoable project matters more than ambition. Favor simple, finished slices.
- **Best AI Hack**: the core of the project is AI: computer vision detection plus species identification, with the prediction model as the stretch.
- **Best Use of a Hugging Face Model**: run at least one Hugging Face model in the pipeline and be able to show it in the demo. YOLO weights and BioCLIP are both hosted on the Hugging Face Hub, so BioCLIP is the better primary species classifier for this track (use the vision LLM only as a fallback or comparison).
- **Best Use of Databricks (maybe)**: optional. Only pursue it if time allows; a possible fit is running the analytics and prediction work (`/ml`) on Databricks. Don't let it block the core app.

## Priorities

This is a hackathon project, so build in this order and keep each stage demoable:

1. **Sighting log (MVP)**: data model, an API to create and list sightings, and a UI feed showing species, camera, and timestamp.
2. **Detection pipeline**: camera image/video in, species label out (pretrained classifier or detector; do not train from scratch). Stub with fake or seeded data until this works.
3. **Analytics**: charts or summaries of sightings over time (by species, camera, hour of day).
4. **Prediction**: model trained on logged sightings, with predictions displayed in the UI.

Prefer a working end-to-end slice over polishing any single layer. Seed data and mock cameras are fine for demos.

## Data model (draft)

- `Camera`: id, name, location (lat/lng or label), status
- `Species`: id, common name, scientific name, optional image
- `Sighting`: id, species_id, camera_id, timestamp (UTC), confidence, optional image/clip URL
- `Prediction`: id, species_id, camera_id (nullable = anywhere), predicted_for (UTC), probability. Written by the ML job, read by the frontend.
- `Sighting.source_kind`: `live` or `replay` (default `replay`). `Camera.park`: park slug, default `yellowstone`.
- Pings (`supabase/pings.sql`): `pings` (lat, lng rounded to ~500 m by a trigger, optional species_name, note up to 140 chars, `is_hidden`). User-reported, never written into `sightings`; `/ml` ignores them. "In a park" is decided client-side from `radiusKm` in `web/src/lib/parks.js`, which also holds each park's species list (`species`, unverified, from model knowledge; Yellowstone mirrors `worker/species.json`). The ping picker offers only the species of the park you are in, or free text outside every park. The worker has no Katmai list yet.
- Social (`supabase/social.sql`): `comments` and `chat_messages` (one chat room per park, anonymous display names, 280-char limit, `is_hidden` moderation flag). They are never written into `sightings`, and `/ml` reads only camera-detected sightings.

Store timestamps in UTC and convert to the park's local time only for display. Sightings should be append-only; the prediction work depends on clean history.

## Tech stack

```
camera/stream --> worker (Python) --> Supabase (Postgres + Storage + Realtime) <-- Vite app on Vercel
```

| Piece | Choice |
|---|---|
| Detector worker (`/worker`) | Python, OpenCV/ffmpeg for frame capture, YOLO (Ultralytics) for animal detection |
| Species ID | Crop each detection, then classify with BioCLIP (Hugging Face, zero-shot against the park's candidate species list). Optionally fall back to a vision LLM API for low-confidence crops |
| Database / storage / live updates | Supabase (Postgres, Storage for snapshots, Realtime for the live feed) |
| Frontend (`/web`) | React + Vite + Tailwind, `@supabase/supabase-js`, Recharts for analytics |
| Frontend hosting | Vercel (any static host would work) |
| Prediction (`/ml`, stretch) | pandas + scikit-learn |

There is no custom API server. The worker writes sightings straight to Supabase and the frontend reads them. Add a small FastAPI service only if we need custom logic later (e.g. serving predictions).

The worker is a long-running process and cannot run on Vercel. Run it on a laptop for the demo, or on an always-on host (Railway, Fly.io, a VPS).

### Worker notes

- Sample about 1-2 frames per second (or use motion detection first); do not run YOLO on every frame.
- Dedupe: merge detections of the same species on the same camera within a cooldown window (default 60s) into one `Sighting`.
- Save a cropped snapshot to Supabase Storage with each sighting.
- Develop against local video files or a mock sighting generator (see "Stream source" above).

### Supabase notes

- The schema lives in `supabase/schema.sql` so everyone shares one source of truth.
- Keys go in `.env` (never committed). The worker uses the service-role key; the frontend only ever gets the public anon key. Enable row-level security with public read-only access on `sightings`.

## Commands

- `/web` (React + Vite): `npm install`, `npm run dev`, `npm run build`, `npm run lint`. With no Supabase keys in `.env` it runs on mock data.
- `/worker` (Python 3.10+): `pip install -r requirements.txt`, then from `/worker`:
  `python -m animal_worker.main --source <file|url|webcam index> --camera "Name" [--dry-run]`; for a live stream add `--stream --park katmai --every 60` (needs yt-dlp and ffmpeg)
  Tests: `python -m pytest` (from `/worker`).
- `/ml` (Python, synthetic data only): from `/ml`, `pip install -r requirements.txt`, `python evaluate.py`, `python predict.py`, `python make_seed.py`, `python -m pytest`. See `ml/README.md`.
- Setup: `bash scripts/setup-supabase-vercel.sh` (Supabase project, SQL files, keys, Vercel). `npm test` in `/web` runs vitest.
- Database: run `supabase/schema.sql`, then `supabase/social.sql`, then `supabase/pings.sql`, then `supabase/katmai-cams.sql` (and optionally the synthetic `supabase/seed.sql`) in the Supabase SQL editor.

## Conventions

- Keep changes small and focused; commit often with clear messages.
- Don't commit secrets, API keys, or large media/model files. Use `.env` (gitignored) and provide a `.env.example`.
- Keep detection, API, UI, and ML code in separate directories so teammates can work in parallel without conflicts.
- Identify the data contract (the `Sighting` shape) early and keep it consistent across all layers.
- Write a short README section for anything a teammate needs to run or demo.
- Add tests for the data layer and any prediction logic; UI tests are optional given hackathon time.

## Working agreements for Claude

- Check this file, `TEAM.md`, and the README before making structural decisions; update this file when the stack, commands, data model, or status change.
- When the user is present: ask before adding heavy dependencies or paid/external services.
- Develop on a feature branch, never `main`; don't open a PR unless asked.

## Unattended / overnight mode

Applies when the user is away (for example `claude -p` or a long unattended session on their laptop). Nobody can answer questions, so decide, log, and keep going.

**How to work**
1. Read this file, then the task file the user names (a `TASKS-*.md`; finished ones are in `docs/archive/`) and `docs/PROGRESS.md`. Work through the task file top to bottom, skipping tasks already marked done.
2. For each task: implement it, run the verification in its acceptance criteria, fix failures, then commit. One commit per task (or finer), with a clear message.
3. After each task, append to `docs/PROGRESS.md`: what was done, what was verified and how, anything skipped or uncertain. Be factual: never mark a task done unless its checks actually passed.
4. If a task is blocked (missing key, unavailable network, unclear requirement), spend at most a few attempts on it, write the blocker and what you tried in `docs/PROGRESS.md`, and move to the next task. Don't thrash.
5. Stop when all tasks are done or blocked. Finish with a summary at the top of `docs/PROGRESS.md` listing done, blocked, and what the user should check first.

**Decide, don't ask.** Pick the simplest option that fits the stack above, note the decision in `docs/PROGRESS.md`, and continue. Prefer a working, demoable slice over polish.

**Verification is required.** Before committing, run what applies: `npm run lint` and `npm run build` in `/web`; `python -m pytest` in `/worker` (and `/ml` once it exists). Never skip, disable, or delete a failing test to get green. For UI changes, also load the page in headless Chromium (Playwright) and check for console errors.

**Allowed without asking**
- Editing and creating files in this repo; installing project dependencies into a local virtualenv (`.venv`) or `web/node_modules`.
- Dependencies already in the stack, plus: `recharts`, `vitest`, `@testing-library/react`, `playwright` (dev only), and `torch` (CUDA build, falling back to CPU).
- Installing Python 3.12 with `uv python install 3.12` for the repo-local `worker/.venv` (the system Python 3.14 may lack wheels); approved by the user on 2026-10-10.
- Downloading Hugging Face model weights (YOLO, BioCLIP) into the default cache.
- Downloading a few small, clearly freely licensed (CC0/public domain) test images or clips for local testing. Keep them out of git (`worker/sample_videos/` is gitignored) and note the source in `docs/PROGRESS.md`.
- `git add`, `git commit`, and `git push` to the current feature branch.

**Never**
- Touch `.env` or any file with secrets; print or commit keys; hard-code credentials. Everything must work with no keys (mock data, `--dry-run`).
- Connect to live camera streams, scrape websites, or send emails/messages. (See "Stream source".)
- Call paid or metered APIs (including vision LLM APIs), or create accounts or deployments (Vercel, Supabase, Databricks).
- Push to `main`, force-push, rewrite history, or delete branches.
- Run destructive commands (`rm -rf` outside build artifacts you created, `git reset --hard`, dropping databases), or install global packages or modify anything outside this repo directory.
- Present synthetic or mock data as real. Anything generated must be labeled as synthetic in code, UI, and docs.

## Git attribution

Do not add `Co-Authored-By` lines (or any Claude attribution) to commit messages or PR descriptions. The user is the sole author.
