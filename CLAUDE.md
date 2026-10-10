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
- The stream source is still undecided (a national park live cam is the goal). Check each source's terms of use before scraping. Until one is chosen, develop against a local video file or a mock sighting generator.

### Supabase notes

- The schema lives in `supabase/schema.sql` so everyone shares one source of truth.
- Keys go in `.env` (never committed). The worker uses the service-role key; the frontend only ever gets the public anon key. Enable row-level security with public read-only access on `sightings`.

## Commands

- `/web` (React + Vite): `npm install`, `npm run dev`, `npm run build`, `npm run lint`. With no Supabase keys in `.env` it runs on mock data.
- `/worker` (Python 3.10+): `pip install -r requirements.txt`, then from `/worker`:
  `python -m animal_worker.main --source <file|url|webcam index> --camera "Name" [--dry-run]`
  Tests: `python -m pytest` (from `/worker`).
- `/ml`: not scaffolded yet.
- Database: run `supabase/schema.sql` in the Supabase SQL editor.

## Conventions

- Keep changes small and focused; commit often with clear messages.
- Don't commit secrets, API keys, or large media/model files. Use `.env` (gitignored) and provide a `.env.example`.
- Keep detection, API, UI, and ML code in separate directories so teammates can work in parallel without conflicts.
- Identify the data contract (the `Sighting` shape) early and keep it consistent across all layers.
- Write a short README section for anything a teammate needs to run or demo.
- Add tests for the data layer and any prediction logic; UI tests are optional given hackathon time.

## Working agreements for Claude

- Check this file and the README before making structural decisions; update this file when the stack, commands, or data model change.
- Ask before adding heavy dependencies or paid/external services.
- Develop on the designated feature branch; don't open a PR unless asked.
