# Animal Logger

A wildlife sighting log for parks. Cameras feed a Python worker that detects animals (YOLO),
identifies the species (BioCLIP from Hugging Face), and logs them to Supabase. A React app shows
a live feed of recent sightings: species, camera, timestamp.

See [CLAUDE.md](CLAUDE.md) for architecture, tracks, and conventions.

## Quick start

### 1. Frontend (works immediately, on mock data)
```bash
cd web
npm install
npm run dev
```

### 2. Supabase (real data)
1. Create a project at supabase.com.
2. Run `supabase/schema.sql` in the SQL editor.
3. `cp .env.example .env` and fill in the URL, anon key (frontend), and service-role key (worker).

To fill the feed with **synthetic** demo data, run `supabase/seed.sql` in the SQL editor after `schema.sql`
(fresh database only; it refuses to run if `sightings` is not empty). Regenerate it with
`python ml/make_seed.py` (see `ml/requirements.txt`); the rows are made up and marked `replay`.

### 3. Worker
```bash
cd worker
uv venv --python 3.12 .venv && source .venv/bin/activate   # or python3.12 -m venv; the worker needs torch wheels (3.14 may lack them)
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124   # CUDA; plain `torch` for CPU
uv pip install -r requirements.txt
python -m pytest                                           # no models needed
```
Edit `worker/species.json` (currently Yellowstone); BioCLIP picks from that list.

**Replay a recorded clip** (no database, no keys):
```bash
python -m animal_worker.main --source sample_videos/nps/yell-Bison00772MTS_1280x720.mp4 --camera "Demo Cam" --dry-run
```
Sightings from files are tagged `source_kind=replay`. Public-domain bison clips come from the
[NPS Yellowstone video library](https://www.nps.gov/yell/learn/photosmultimedia/vl_bisoncalves.htm); put them in `worker/sample_videos/` (gitignored).

**Live camera (NPS Yellowstone "North Entrance - Electric Peak", a still refreshed every 30-60 s; image credit: National Park Service):**
```bash
python -m animal_worker.main --source https://www.nps.gov/webcams-yell/mammoth_electric.jpg --camera "Electric Peak Cam" --park yellowstone --dry-run
```
An image-URL source is polled every `--every` seconds (default 60, minimum 30) and tagged `source_kind=live`; override with `--source-kind`. It stops on the first fetch error.

**Record your own replay footage** (saves each new still to `worker/sample_videos/yellowstone/`; the cam is dark infrared at night, so run it through dawn):
```bash
python -m animal_worker.still_poller --out sample_videos/yellowstone --every 60
```

### 4. ML and synthetic data
`ml/` predicts when species appear, trained on **synthetic** data only; results and caveats are in [ml/README.md](ml/README.md).
`python ml/predict.py` writes `web/public/predictions.sample.json` for the prediction card, and `python ml/make_seed.py` regenerates `supabase/seed.sql`.

## Web app: Demo / Live, chat and comments
- The header switch is **Demo** (recorded clips and seed/mock data, amber "Demo clip" bubble) or **Live** (green "Live" bubble; only the NPS Electric Peak cam has a live image, refreshed every minute; other cameras are greyed out). Live never falls back to the demo clip: a failed image says "Live feed unavailable". The feed, cameras and analytics follow the switch (`source_kind`).
- Demo clips live in `web/public/demo/` (public-domain NPS bison clips). `web/src/lib/cameraConfig.js` maps camera names to their clip and live image.
- Each park has one anonymous chat room (camera page) and every sighting has a comment thread. Run `supabase/social.sql` after `schema.sql` to enable them; without keys they run on an in-memory sample. Hide a bad message by setting `is_hidden = true` in the Supabase dashboard.
- `cd web && npm run dev | lint | build | test`.
