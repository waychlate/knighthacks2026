# Katmai live feed handoff

This is the complete handoff for merging the Katmai detector into the shared
Supabase-backed website. The code path is:

```text
YouTube live cameras -> sampled JPEG -> reviewed Katmai YOLO model
-> cooldown/deduplication -> snapshot storage + sightings row
-> Supabase Realtime -> React sightings feed
```

## Files included in Git

- `worker/animal_worker/katmai_live.py`: live detector and explicit publisher.
- `worker/animal_worker/youtube_poller.py`: frame callback after a JPEG and its
  UTC metadata have been saved.
- `worker/animal_worker/katmai_multi_poller.py`: three-camera collection.
- `worker/animal_worker/db.py`: snapshot upload and sighting insert, including
  the original capture timestamp.
- `config/katmai_cameras.json`: source URLs, canonical database names, locations.
- `supabase/schema.sql`: sightings, storage bucket, read policies, and Realtime.
- `supabase/katmai-cams.sql`: the three Katmai camera rows.
- `web/src/lib/useSightings.js`: initial fetch and Realtime INSERT subscription.

## One required artifact outside Git

The reviewed model is intentionally ignored by Git. Transfer it privately and
place it at:

```text
worker/training/katmai/current.pt
```

Do not remove `*.pt` from `.gitignore` or commit the model to the repository.

## Supabase owner setup

1. Merge the feature branch.
2. In the existing Supabase project's SQL Editor, run `supabase/schema.sql`, then
   `supabase/katmai-cams.sql`. Both are designed to be safe to rerun.
3. Create the repository-root `.env` on the machine that runs the worker:

   ```env
   SUPABASE_URL=https://PROJECT_REF.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=SERVER_SECRET_KEY
   ```

   A current `sb_secret_...` key or legacy `service_role` key can occupy the
   second variable. Never put it in `web/`, Vercel, Git, or a public chat.
4. Configure the website locally or in Vercel with public values only:

   ```env
   VITE_SUPABASE_URL=https://PROJECT_REF.supabase.co
   VITE_SUPABASE_ANON_KEY=PUBLIC_PUBLISHABLE_KEY
   ```

5. Transfer `current.pt` to the path above.
6. From `worker/`, verify setup without contacting a camera:

   ```powershell
   .\.venv\Scripts\python.exe -m animal_worker.katmai_live --check --publish
   ```

   Expected output includes `Model ready` and `Supabase ready`.
7. Start one camera first:

   ```powershell
   .\.venv\Scripts\python.exe -m animal_worker.katmai_live `
     --camera brooks-falls-low --every 60 --publish
   ```

8. After that works, omit `--camera` to run all three. Stop with `Ctrl+C`.

Every accepted detection is also recorded locally in
`worker/sample_videos/katmai-live/live_sightings.jsonl`. Its `published` field is
`true` only when the database insert succeeded. A frame without an accepted
detection does not create a sighting row. During the documented off-season the
worker labels rows `replay`, because the channels may show recorded highlights.

## Verification in Supabase and the website

In Table Editor, a successful detection creates a `sightings` row with a UTC
`seen_at`, confidence, public `snapshot_url`, and `source_kind`. The `species`
row is `Brown bear / Ursus arctos` or `Bird (unidentified) / Aves`, and the
camera row identifies the feed.

With the website set to Katmai and Live mode, the row should appear without a
page refresh. The frontend already subscribes to INSERT events on `sightings`.
If the row exists but the website does not update, confirm `sightings` is in the
`supabase_realtime` publication by rerunning `supabase/schema.sql`.

## What has and has not been verified

The worker path is covered with fake streams, fake detections, fake stores, queue
backpressure, camera-name consistency, timestamps, deduplication, and publisher
payload tests. The repository has not been connected to the team's real
Supabase project, and no live camera was contacted during automated tests. The
Supabase owner must perform the final check and one-camera run above.
