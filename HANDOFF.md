# HANDOFF: Animal Logger (KnightHacks 2026)

Everything decided and learned in the cloud planning session, so a local session on a laptop can pick up cleanly. `CLAUDE.md` holds the standing rules; `TASKS.md` is the backlog; this file holds the context and research behind them.

Branch with all of this work: `claude/animal-logger-claude-md-iy1oyj` (pushed to `waychlate/knighthacks2026`).

## 1. The idea

An animal logger for parks. A visitor opens the app and sees a live log of recently seen animals: species, which camera saw it, and a timestamp. The audience is tourists in the park who want to know what they're in for.

Stretch goal: log sightings to a database, train an ML model on the patterns, and show predictions like "Predicting a [species] around 2:30 PM."

Hackathon tracks targeted: **Best First Time**, **Best AI Hack**, **Best Use of a Hugging Face Model**, and maybe **Best Use of Databricks**.

## 2. Decisions made

| Area | Decision | Why |
|---|---|---|
| Detector | Python worker, OpenCV/ffmpeg capture, YOLO (Ultralytics) | Best CV ecosystem; pretrained, no training needed. |
| Species ID | **BioCLIP** (Hugging Face), zero-shot against a per-park candidate species list | Counts as the Hugging Face model for that track; no per-call cost; works offline. A vision LLM is an optional fallback only. |
| Backend | **Supabase** (Postgres, Storage, Realtime). No custom API server | Worker writes directly; frontend reads and subscribes. Less to build and host. |
| Frontend | React + Vite + Tailwind, `supabase-js`, Recharts | Fast to build. |
| Hosting | **Vercel** for the frontend (Netlify would be equivalent). The worker runs on a laptop for the demo | The worker is long-running and cannot run on Vercel. |
| Prediction | pandas + scikit-learn in `/ml` | Hour-of-day patterns don't need deep learning. |
| Databricks | Optional and undecided. A possible fit is running analytics/prediction there | Don't let it block the core app. Read that track's rules before committing. |

Species-ID alternatives that were considered: Google SpeciesNet (camera-trap trained), MegaDetector (detect only), a fine-tuned YOLO (needs labeled data), iNaturalist-trained classifiers, BirdNET (audio only).

Worker design rules: sample about 1-2 fps, never run YOLO on every frame; dedupe repeat sightings (same species, same camera, 60s cooldown, extended while the animal stays in frame); save a cropped snapshot with each sighting.

## 3. What exists in the repo

- `web/`: Vite + React + Tailwind app. Live feed, species and camera filters, cameras list and per-camera pages, a prediction card ("Predicting a ... around ..."). Hash routing. Runs on mock data when no Supabase keys are set. Lint and build pass; the UI was checked in headless Chromium.
- `supabase/schema.sql`: `cameras`, `species`, `sightings`, `predictions` tables, row-level security (public read), realtime on sightings, and a public `snapshots` storage bucket.
- `worker/`: `animal_worker` package (capture, YOLO detector, BioCLIP classifier, dedupe, Supabase store, CLI with `--dry-run`), `species.json` placeholder list, 5 passing dedupe unit tests.
- `.env.example`, `.gitignore`, `README.md` (quick start), `CLAUDE.md`, `TASKS.md`, `PROGRESS.md`.

### Verified vs not verified

Verified: web build and lint, the UI in headless Chromium, the dedupe unit tests, worker code compiles.

**Not verified:**
- YOLO and BioCLIP have never been run on real images or video (torch was never installed in the cloud session). The BioCLIP prompt format and confidence threshold need tuning on real footage.
- Nothing has run against a real Supabase project. The Supabase client code and `schema.sql` are untested.
- The `predictions` table is not yet written to by anything. The card shows hard-coded sample data.
- `/ml` does not exist yet.

## 4. Live camera source (decided 2026-10-10)

Chosen: NPS Yellowstone "North Entrance - Electric Peak", a still JPEG at `https://www.nps.gov/webcams-yell/mammoth_electric.jpg` refreshed every 30-60 s (the NPS page says elk, bison and pronghorn graze there). The user checked the cam and NPS disclaimer; credit NPS. The main demo runs on recorded clips and our own collected frames (`worker/animal_worker/still_poller.py` saves them), with the web Demo/Live toggle showing the difference.

Why not the others (from page reads and search, 2026-10-10):
- Katmai bear cams: season is "typically late June through early October", so likely ending; explore.org's terms bar bots/automated copying without written consent (more@explore.org for questions).
- Cornell FeederWatch: page returned 403 to us; stream is on YouTube; Cornell's own terms were not found or read.
- Other Yellowstone cams: scenery only; only Electric Peak is noted for animals. No recorded footage of that cam exists (NPS only offers Old Faithful livestream recordings).

Public-domain replay material: NPS Yellowstone video library (bison clips, check each link) and USGS/NPS stills.

### Draft candidate species lists (unverified)

Cornell FeederWatch, NY feeder in fall. The first four came from search-result descriptions of the cam; the rest are from model knowledge:

```json
{"species": [
  {"common_name": "Red-winged Blackbird", "scientific_name": "Agelaius phoeniceus"},
  {"common_name": "Blue Jay", "scientific_name": "Cyanocitta cristata"},
  {"common_name": "Mourning Dove", "scientific_name": "Zenaida macroura"},
  {"common_name": "Black-capped Chickadee", "scientific_name": "Poecile atricapillus"},
  {"common_name": "Tufted Titmouse", "scientific_name": "Baeolophus bicolor"},
  {"common_name": "White-breasted Nuthatch", "scientific_name": "Sitta carolinensis"},
  {"common_name": "Downy Woodpecker", "scientific_name": "Dryobates pubescens"},
  {"common_name": "Hairy Woodpecker", "scientific_name": "Dryobates villosus"},
  {"common_name": "Red-bellied Woodpecker", "scientific_name": "Melanerpes carolinus"},
  {"common_name": "Northern Cardinal", "scientific_name": "Cardinalis cardinalis"},
  {"common_name": "American Goldfinch", "scientific_name": "Spinus tristis"},
  {"common_name": "Dark-eyed Junco", "scientific_name": "Junco hyemalis"},
  {"common_name": "House Finch", "scientific_name": "Haemorhous mexicanus"},
  {"common_name": "Pileated Woodpecker", "scientific_name": "Dryocopus pileatus"},
  {"common_name": "Eastern Gray Squirrel", "scientific_name": "Sciurus carolinensis"},
  {"common_name": "Eastern Chipmunk", "scientific_name": "Tamias striatus"}
]}
```

Katmai (from model knowledge, not checked against the official NPS species list; confirm with NPSpecies, park code KATM). Only brown bear, bald eagle and gulls are likely seen regularly; keep the list short for BioCLIP accuracy:

```json
{"species": [
  {"common_name": "Brown bear", "scientific_name": "Ursus arctos"},
  {"common_name": "Bald eagle", "scientific_name": "Haliaeetus leucocephalus"},
  {"common_name": "Moose", "scientific_name": "Alces alces"},
  {"common_name": "Red fox", "scientific_name": "Vulpes vulpes"},
  {"common_name": "Glaucous-winged gull", "scientific_name": "Larus glaucescens"},
  {"common_name": "Mew gull", "scientific_name": "Larus canus"},
  {"common_name": "Common merganser", "scientific_name": "Mergus merganser"},
  {"common_name": "Common raven", "scientific_name": "Corvus corax"}
]}
```

`worker/species.json` currently holds a generic placeholder list; swap it for the chosen camera's animals.

## 5. Unattended overnight run (on the laptop)

The plan: start a local Claude Code session in **auto mode** and let it work through `TASKS.md` while the user sleeps.

- `CLAUDE.md` has an "Unattended / overnight mode" section: how to work, what is allowed, and a hard "never" list (no `.env`, no live streams, no paid APIs, no accounts or deployments, no pushing to `main`, no destructive commands, never present synthetic data as real).
- `TASKS.md` is ordered, with the **ML predictions first** (the most important deliverable; it needs no network or models): synthetic data generator, three models compared with a temporal split, a recovery check against the true generating pattern, `predict.py`, and wiring sample output into the prediction card. Then seed data, worker refactor for testability, a real-pipeline check (needs model and image downloads, so the most likely to be blocked), analytics page, polish, docs.
- `PROGRESS.md` is where the run logs results. Read its summary first in the morning.

Before the run:
1. `git fetch origin && git checkout claude/animal-logger-claude-md-iy1oyj`, then `git checkout -b overnight/run-1` (never run on `main`).
2. Keep the laptop awake and plugged in.
3. Make sure `git push` works without a password prompt (otherwise commits stay local; push them in the morning).
4. Do a short test run first; confirm it reads `TASKS.md` and makes its first commit before leaving.
5. Suggested prompt: "Follow the unattended / overnight mode section of CLAUDE.md and work through TASKS.md."

Caveat: ML results will come from synthetic data and will look better than real data would. They must be presented that way in the demo.

## 6. Still to do by hand

- Create a Supabase project, run `supabase/schema.sql`, fill in `.env` (copy `.env.example`; the service-role key stays server-side only).
- Pick the camera source and clear its terms (section 4), then update `worker/species.json`.
- Create a Vercel account (free tier, sign in with GitHub). The repo is under `waychlate`, so that account must connect Vercel to GitHub or grant access. Settings: root directory `web`, env vars `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
- Decide whether to pursue the Databricks track; read its rules first.

## 7. Cloud-session limitations worth knowing

- The cloud environment's network policy blocked several hosts, so web research was limited to search snippets. A laptop session won't have that limit.
- The GitHub push was blocked early on (403, Claude GitHub App not installed on the repo) until access was fixed; everything is now pushed.
- Heavy dependencies (torch, ultralytics, open_clip) were never installed in the cloud, which is why the worker's models are untested.
