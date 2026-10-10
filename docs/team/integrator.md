# Project owner (you): integrator and demo

You own the shared pieces: Supabase, Vercel, the GPU laptop, the demo and the final README. Branch for your own changes: `owner/...`; merging is relaxed (see `TEAM.md`).

## Do first
- [ ] **Keep the laptop awake and plugged in** so the collector in `worker/` keeps saving frames (check: `ls worker/sample_videos/yellowstone | wc -l`).
- [ ] `bash scripts/setup-supabase-vercel.sh` (Supabase project, SQL, keys, Vercel, worker smoke test). About 20 minutes of clicking. Keys stay in `.env` and Vercel; send them to teammates only if they truly need them.
- [ ] Zip the collected frames for the ML teammate: `cd worker/sample_videos && zip -r ~/yellowstone-frames.zip yellowstone`, plus one NPS bison clip, and share them.
- [ ] Share the deployed link with the frontend teammate once Vercel is up.

## Then
- [ ] **Fill the Demo feed with real pipeline output:** run the worker (no `--dry-run`) on the three bison clips and any good frames, with `--camera` set to a seeded demo camera and `--park yellowstone`. Rows are tagged `replay` automatically. Check the deployed Demo mode shows them.
- [ ] Check Live mode on the deployed site with the real NPS image, and the "Live feed unavailable" fallback.
- [ ] Merge teammates' pull requests after `(cd worker && .venv/bin/python -m pytest)` and `(cd web && npm run lint && npm run build && npm test)` are green.
- [ ] Fix bugs the frontend teammate lists in `docs/qa.md`.
- [ ] Write **`docs/demo-script.md`**: a table of time, who speaks, what is on screen, what to say (3 minutes). Backup plan if the wifi dies: the local web app plus the worker in `--dry-run`.
- [ ] Final pass on `README.md`: add real screenshots, the demo script link, the deployed URL, and re-check the Status table against what is true by then.

## Freeze (hour 18)
- [ ] Final merge into `main`, redeploy, tag it: `git tag demo-freeze && git push --tags`.
- [ ] Rehearse the demo 3 times on the GPU laptop. Start the models once beforehand so the first run is not slow.
- [ ] Combine the Devpost text: your overview, `docs/devpost-ai.md` from the ML teammate, screenshots from the frontend teammate. Submit early.

## Risks
- Supabase keys never leave `.env` and Vercel's environment settings.
- Only your laptop has the GPU, so you run the live demo.
- Avoid schema or data-shape changes after the freeze.
