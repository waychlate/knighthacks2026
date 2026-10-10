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
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# try it without writing to the DB:
python -m animal_worker.main --source path/to/video.mp4 --camera "Test Cam" --dry-run
```
Edit `worker/species.json` to list the animals that live in your park; BioCLIP picks from that list.
