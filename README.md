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

### 3. Worker
```bash
cd worker
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# try it without writing to the DB:
python -m animal_worker.main --source path/to/video.mp4 --camera "Test Cam" --dry-run
```
Edit `worker/species.json` to list the animals that live in your park; BioCLIP picks from that list.

## Web app: Demo / Live, chat and comments
- The header switch is **Demo** (recorded clips and seed/mock data, amber "Demo clip" bubble) or **Live** (green "Live" bubble; only the NPS Electric Peak cam has a live image, refreshed every minute; other cameras are greyed out). Live never falls back to the demo clip: a failed image says "Live feed unavailable". The feed, cameras and analytics follow the switch (`source_kind`).
- Demo clips live in `web/public/demo/` (public-domain NPS bison clips). `web/src/lib/cameraConfig.js` maps camera names to their clip and live image.
- Each park has one anonymous chat room (camera page) and every sighting has a comment thread. Run `supabase/social.sql` after `schema.sql` to enable them; without keys they run on an in-memory sample. Hide a bad message by setting `is_hidden = true` in the Supabase dashboard.
- `cd web && npm run dev | lint | build | test`.
