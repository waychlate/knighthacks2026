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

## 4. Open decision: the live camera source

Nothing is chosen. Two research agents ran, but the cloud session's network policy blocked `nps.gov`, `explore.org`, YouTube and the Cornell sites, so **all findings came from search snippets. No cam page or terms page was actually read, and no cam is confirmed live.** Treat every row below as a lead, not a fact.

| Source | Notes | Concerns |
|---|---|---|
| Katmai brown bear cams (Brooks Falls, River Watch), explore.org with NPS | Best wildlife cam; bears are large and frequent. Pages: nps.gov/katm/learn/photosmultimedia/webcams.htm, explore.org/bears. | Seasonal (NPS says mid-June to mid-October); likely ended or replaying highlights as of 2026-10-10. Stream type unverified. Terms unread. |
| Cornell Lab FeederWatch Cam, Sapsucker Woods | allaboutbirds.org/cams/cornell-lab-feederwatch/. Reportedly on YouTube, live most days. Birds are close and large; 10+ species. | Live status unconfirmed. Terms unread; a search snippet says YouTube terms apply. Small birds may weaken YOLO. |
| Yellowstone NPS webcams | nps.gov/yell/learn/photosmultimedia/webcams.htm. About 8-10 cams. An entrance view reportedly shows elk, bison and pronghorn. | Mostly geysers and landscapes. Animals rare and probably small in frame. |
| African waterhole cams on YouTube (NamibiaCam, Okaukuejo/Etosha, Linkwasha, Camelthorn) | Large animals, many species, easy to read if the YouTube live URLs are current. | Only active during US morning hours; would need a new species list. Not a national park. |
| Others | Virginia DWR elk and marsh cams; Pennsylvania elk cam (may end mid-October). | Stream type and status unknown. |

Key finding: public NPS cams are mostly scenery or weather views, and animals rarely appear on them. The "cameras placed along trails" vision is not something public cams provide.

**Recommended approach:** pitch the national-park vision, but demo with a feed where animals actually appear (feeder or waterhole cam), and frame the app as a template that plugs into any park's cameras. Alternatively use Yellowstone or Katmai if a cam is live and showing animals.

### To resolve (needs a human)
1. Open the candidate cam pages in a normal browser; see if any is live and has animals in frame.
2. Read the source's terms of use (and YouTube's, if it is a YouTube stream). Email the operator for permission for non-commercial hackathon use.
3. Find the real stream URL (for YouTube: `yt-dlp -g <live url>` gives an HLS URL the worker can read).
4. Only after that, point the worker at it. Until then, develop and test on local files and mock data.

If research is rerun from a laptop with normal internet access, `WebFetch` should work, and an agent can read the actual pages and terms.

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
