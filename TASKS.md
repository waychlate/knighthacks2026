# TASKS

Ordered backlog for unattended runs (see "Unattended / overnight mode" in CLAUDE.md). Work top to bottom. Mark a task `[x]` only when every acceptance check passed; otherwise leave it and log the blocker in `PROGRESS.md`.

Priority: the ML predictions are the most important deliverable (Best AI Hack track), so they come first. They need no network, keys, or model downloads, which also makes them the safest to run unattended.

## 1. ML: sighting predictions (`/ml`)

Goal: given a (synthetic, for now) sighting history, predict *when* each species is likely to be seen, e.g. "Predicting a Great Blue Heron around 5:00 AM near Pond Cam".

- [ ] Scaffold `/ml`: `requirements.txt` (pandas, numpy, scikit-learn, pytest), `README.md`, `tests/`.
- [ ] `ml/synthetic.py`: generate ~14 days of sightings for the species in `worker/species.json` and 3 cameras. Each species has a known time-of-day profile (e.g. deer at dawn/dusk, jays mid-morning, herons early morning), a camera preference, a weekday/weekend effect, and noise. Fixed random seed. Output CSV matching the `Sighting` shape (species, camera, `seen_at` in UTC, confidence). Label everything as **synthetic** in code, file headers, and the README.
- [ ] Framing: for each (species, camera, hour slot), predict the probability of at least one sighting in that hour.
- [ ] Models: (a) naive baseline = overall rate per (species, camera); (b) smoothed historical rate by hour of day (and weekday); (c) a scikit-learn model (e.g. gradient boosting or logistic regression) with features such as hour (sin/cos), weekday, species, camera, and recent activity. Keep it simple and explainable.
- [ ] Evaluation: **temporal** split (train on earlier days, test on the last 3 days; never shuffle across time). Report Brier score or log loss for each model, plus a hit-rate metric: how often the top predicted hour for a species falls within +/-1 hour of a real sighting. Write the table into `ml/README.md`.
- [ ] Recovery check: because the data is synthetic, compare each model's learned hourly profile against the true generating profile and report the error. Be honest in the README that results on synthetic data are optimistic and say what real data would change. If the learned model does not beat the naive baseline, say so and keep the simpler model.
- [ ] `ml/predict.py`: train on the data, predict the next 24 hours, keep the top predictions above a probability threshold, and write `Prediction` rows (see `supabase/schema.sql`: species, camera or null, `predicted_for` UTC, probability) to `ml/out/predictions.json`. Write to Supabase only if keys are set in `.env`; never require them.
- [ ] Also copy a sample of the output to `web/public/predictions.sample.json`, clearly marked as sample/synthetic, and update `web/src/lib/usePredictions.js` to use it for the mock fallback instead of the hard-coded predictions (keep the "sample predictions" badge). Shift the timestamps so they are relative to "now".
- Accept: `python -m pytest` passes in `/ml` (tests cover the generator's determinism, the time-based split having no leakage, probability outputs in [0, 1], and the output schema); `python ml/predict.py` runs with no keys and produces the JSON; the `ml/README.md` metrics table exists; `npm run lint` and `npm run build` pass in `/web`; headless Chromium shows the prediction card with sample data and no console errors.

## 2. Demo seed data
- [ ] Generate `supabase/seed.sql` **from the same synthetic generator** (a script in `/ml`, not hand-written) so the seed data and the model agree: the species from `worker/species.json`, 3 cameras, and the synthetic sightings. Comment clearly that it is synthetic.
- Accept: valid SQL in the same schema as `supabase/schema.sql` (review carefully; no database is required to execute it); the README says how to load it and how to regenerate it.

## 3. Make the worker testable without models
- [ ] Refactor `worker/animal_worker/main.py` so the per-frame logic is a function, e.g. `process_frame(frame, ts, detector, classifier, deduper, sink)`, taking injected dependencies instead of constructing them.
- [ ] Add pytest tests using fake detector/classifier/sink objects: logs a sighting, respects the dedupe cooldown, skips below-threshold classifications, and handles frames with no detections.
- Accept: `python -m pytest` passes from `/worker` with no torch/ultralytics installed (heavy imports stay lazy).

## 4. Verify the real pipeline (best effort)
- [ ] Create a `.venv`, install `worker/requirements.txt` (CPU torch), and download YOLO + BioCLIP weights.
- [ ] Download 2-3 small freely licensed (CC0/public domain) images or short clips of animals from the species in `worker/species.json` into the gitignored `worker/sample_videos/`.
- [ ] Run `python -m animal_worker.main --source <clip> --dry-run` and confirm at least one correct `SIGHTING` line. Tune BioCLIP prompts / `--min-confidence` if needed, and record the results (what worked, what did not, rough speed on this machine) in `PROGRESS.md`.
- Accept: documented result in `PROGRESS.md`. If weights or test media can't be downloaded, mark blocked and move on.

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
- [ ] README: Vercel deploy steps (root dir `web`, env vars), demo script (3 minutes: what to click, what to say, which hackathon track each part targets), and a short architecture overview including how the ML predictions flow into the UI.
- Accept: a teammate could follow the README from a clean clone.
