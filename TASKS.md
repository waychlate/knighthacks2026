# TASKS

Ordered backlog for unattended runs (see "Unattended / overnight mode" in CLAUDE.md). Work top to bottom. Mark a task `[x]` only when every acceptance check passed; otherwise leave it and log the blocker in `PROGRESS.md`.

## 1. Make the worker testable without models
- [ ] Refactor `worker/animal_worker/main.py` so the per-frame logic is a function, e.g. `process_frame(frame, ts, detector, classifier, deduper, sink)`, taking injected dependencies instead of constructing them.
- [ ] Add pytest tests using fake detector/classifier/sink objects: logs a sighting, respects the dedupe cooldown, skips below-threshold classifications, and handles frames with no detections.
- Accept: `python -m pytest` passes from `/worker` with no torch/ultralytics installed (heavy imports stay lazy).

## 2. Verify the real pipeline (best effort)
- [ ] Create a `.venv`, install `worker/requirements.txt` (CPU torch), and download YOLO + BioCLIP weights.
- [ ] Download 2-3 small freely licensed (CC0/public domain) images or short clips of animals from the species in `worker/species.json` into the gitignored `worker/sample_videos/`.
- [ ] Run `python -m animal_worker.main --source <clip> --dry-run` and confirm at least one correct `SIGHTING` line. Tune BioCLIP prompts / `--min-confidence` if needed, and record the results (what worked, what did not, rough speed on this machine) in `PROGRESS.md`.
- Accept: documented result in `PROGRESS.md`. If weights or test media can't be downloaded, mark blocked and move on.

## 3. Demo seed data
- [ ] Add `supabase/seed.sql`: the species from `worker/species.json`, 3 cameras, and ~500 sightings over the past 14 days with realistic time-of-day patterns per species (e.g. deer at dawn/dusk, birds mid-morning). Clearly comment that it is **synthetic**.
- Accept: the file is valid SQL in the same schema as `supabase/schema.sql` (no tool needed to execute it; review carefully), and the README says how to load it.

## 4. ML: sighting predictions (`/ml`)
- [ ] Scaffold `/ml` (`requirements.txt`, README, tests): load sightings from a CSV export or generate synthetic data matching the seed pattern.
- [ ] Baseline model: per species (and camera), estimate probability by hour of day and day of week; predict the most likely upcoming time windows. Keep it simple (pandas + scikit-learn or plain smoothed counts).
- [ ] Evaluate on held-out days and record the metric in `ml/README.md` (e.g. how often the top predicted hour is within +/-1 hour of a real sighting). Report honestly; synthetic data will look better than real data.
- [ ] `ml/predict.py` writes `predictions` rows (see the schema) to a JSON file by default, and to Supabase only if keys are set in `.env`.
- Accept: `python -m pytest` passes in `/ml`, and `python ml/predict.py` produces output with no keys present.

## 5. Web: analytics page
- [ ] Add an Analytics page (`#/analytics`, nav link) with Recharts: sightings by hour of day, by species, and by camera, computed from the loaded sightings. Works on mock data.
- [ ] Put the aggregation in pure functions in `web/src/lib/` with vitest unit tests.
- Accept: `npm run lint`, `npm run build`, and `npx vitest run` pass; a headless Chromium check of `#/analytics` shows the charts with no console errors.

## 6. Web: polish and resilience
- [ ] Show an error banner when a Supabase request fails (instead of silently showing an empty list).
- [ ] Verify the layout at 375px width (headless Chromium screenshot); fix overflow or cramped cards.
- [ ] Basic accessibility: labels, focus styles, `aria-current`, sensible alt text.
- Accept: lint and build pass; screenshots at 375px and 900px look right.

## 7. Docs
- [ ] README: Vercel deploy steps (root dir `web`, env vars), demo script (3 minutes: what to click, what to say, which hackathon track each part targets), and a short architecture overview.
- Accept: a teammate could follow the README from a clean clone.
