# TASKS-C: integrator (you)

You own the shared pieces: Supabase, Vercel, merges, the web app, and the demo laptop. Branch for your own changes: `c/...` (merge to `main` yourself, but only after the checks below).

## Do first
- [ ] **Keep the laptop awake and plugged in** (the collector in `worker/` stops if it sleeps): `sudo systemctl mask sleep.target suspend.target` is one option, or turn off auto-suspend in settings. Check later with `ls worker/sample_videos/yellowstone | wc -l`.
- [ ] `bash scripts/setup-supabase-vercel.sh` (Supabase project, SQL, keys, Vercel, worker smoke test). About 20 minutes of clicking. Send keys to teammates **privately** only if they need them (they probably do not).
- [ ] Zip the collected frames for A: `cd worker/sample_videos && zip -r ~/yellowstone-frames.zip yellowstone` and share it, plus one NPS bison clip.
- [ ] Tell A and B they can start (they work from `TEAM.md`).

## Then
- [ ] **Fill the Demo feed with real pipeline output:** run the worker (no `--dry-run`) on the three bison clips and any good frames, with `--camera` set to a seeded demo camera, `--park yellowstone`. Rows are tagged `replay` automatically. Check the deployed site's Demo mode shows them.
- [ ] Check Live mode on the deployed site with the real NPS image (the one place that loads the live URL), and the "Live feed unavailable" fallback.
- [ ] Review and merge PRs from A and B: `git fetch && git checkout <their-branch>`, run `(cd worker && .venv/bin/python -m pytest)`, `(cd web && npm run lint && npm run build && npx vitest run)`, then merge on GitHub.
- [ ] Fix the bugs B reports in `docs/qa.md` (web side).
- [ ] Tomorrow chip, sample predictions: confirm the card reads well on the deployed site.

## Freeze (hour 18)
- [ ] Final merge of everything into `main`, redeploy, tag it: `git tag demo-freeze && git push --tags`.
- [ ] Rehearse the demo 3 times on the GPU laptop from `docs/demo-script.md`. Start the models once beforehand so the first run is not slow.
- [ ] Submit Devpost early.

## Risks to watch
- Supabase keys never leave `.env` and Vercel's env settings.
- The worker needs the GPU laptop; nobody else can run the live demo at speed.
- Do not let anyone change the schema or data contract after the freeze.
