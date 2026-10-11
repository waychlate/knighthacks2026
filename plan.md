# Animal Logger: final 6 hours before judging

## Context
Live table demo (3–5 min, recorded fallback video). Most features already work. The remaining work makes the AI visible, makes the predictions real, and shows the app scales to more parks. A teammate is on live-detection reliability and model fine-tuning, so worker changes must stay small and isolated.

## Decisions (from the grilling)
- Live moment: Yellowstone still, polled every 60 s. Katmai video is a talking point only.
- Demo mode: the worker runs real YOLO + BioCLIP on recorded clips every ~10 s, pre-warmed. Rows are tagged `source_kind='replay'`, and the ML job ignores them. A distinct demo camera name is optional.
- Bounding boxes: the worker saves an annotated frame automatically with every sighting, in Demo and Live. The normal feed stays clean. A Dev toggle (next to Demo/Live) lets you step through sightings and see the frame, box, YOLO score and species confidence.
- Real data: iNaturalist research-grade observations per park, species x hour of day, park-level. Labeled "based on public iNaturalist observations". The synthetic camera-level sample stays out of the demo.
- Parks: add Yosemite, Everglades, Grand Canyon, Great Smoky Mountains and Denali as greyed markers with "cameras coming soon". Chat and pings work there. Species lists come from top iNaturalist species per park.
- Ownership: I make the worker change as one new module, one migration and a 2-line hook, then tell the teammate to merge it.

## Update after merging origin/main (DrewV2 PR #1, adren334 UI)
- `main.process_frame` already calls `sink.record_detection(species, conf, det, camera, ts)` when the sink has it, and `det` carries `box`, `score`, `label`. So step 3 needs no hook in `main.py`: add `record_detection` to `StoreSink`.
- `annotate_sightings.py` only annotates local files from `sightings.json`. Reuse its drawing code (colours, label box) in a function that draws on one in-memory frame.
- `process_frame` does not pass the full frame to the sink. Smallest fix: `record_detection` receives `det`; add `det.frame` (or pass the frame) in `detector.py`. Check `Detection` first.
- Step 1 builds on `ml/parks.py` (`ParkConfig`) and `predict.py --park`; add an iNat-backed path next to the synthetic one, and keep the `synthetic` flag honest.
- Step 2 may conflict with adren334's edits to `ParkPage.jsx`; keep that change small.
- Katmai has a real species list (`worker/species_katmai.json`, `worker/reference/katmai/npspecies_full.csv`); use it for the Katmai park.

## Work order (cut from the bottom)
1. **iNaturalist predictions** (`ml/`)
   - Add a loader (e.g. `ml/inat.py`) that fetches observations per park and writes a local cache. This runs in an attended session only, per CLAUDE.md.
   - Build species x hour profiles with the existing hourly-profile model in `ml/models.py`, and make `predict.py` output park-level predictions with `source: "inaturalist"`.
   - Update `web/public/predictions.sample.json` (or a new real file) and the prediction card with the new label.
   - Add a test for the loader's parsing and for the profile.
   - Note the bias (daytime, near trails, tourists) in `ml/README.md`.
2. **Greyed parks and chat** (`web/`)
   - Add the 5 parks in `web/src/lib/parks.js` with `active:false` and iNat-derived `species`.
   - `GlobePage.jsx`: grey marker colour, using a flag instead of the hard-coded katmai/other colour.
   - `ParkPage.jsx:31-32`: for inactive parks, show the "no cameras yet" note plus the chat tab (`ChatPanel`/`useThread` already take any slug). Pings already work via `radiusKm`.
   - Fix the stale Katmai comment in `parks.js`.
3. **Dev mode and annotated frames**
   - Add `supabase/dev-frames.sql` (new nullable columns on `sightings`: `frame_url`, `bbox`, `yolo_score`; run in Supabase by hand).
   - Add `worker/animal_worker/annotate.py`, which draws the box and label (reusing the drawing logic in `worker/draw_test.py`) and uploads via the same path as `db.upload_snapshot`.
   - Add a 2-line hook in `main.process_frame` (main.py:93-105) to pass `det.box` and `det.score` to the sink. Extend `db.insert_sighting` and the fakes used in the tests.
   - The annotated frame is saved automatically on every sighting the worker records, in both Demo and Live runs. There is no manual step and no separate script.
   - Web: add a Dev toggle next to Demo/Live in `ModeToggle.jsx`, independent of that choice. In Dev, stepping through the sightings of the current mode shows each annotated frame, YOLO score and species confidence. Switch Demo to Dev in front of a recruiter and walk through the sightings.
   - Rows without a `frame_url` (older or seeded rows) show a "no frame saved" placeholder.
4. **Demo 10 s mode**
   - Add a demo flag to the worker (e.g. `--demo`) that lowers the 30 s floor (`capture.stream_frames`, `still_poller`, main.py:34) to 10 s and the dedupe cooldown to ~10 s. Tag the rows `replay` and loop recorded clips.
   - Pre-warm the models. Test on the demo laptop that inference keeps up.
5. **Rehearsal and fallback** (last hour)
   - Run the demo script end to end, record the fallback video, and update CLAUDE.md "Current status".

## Verification
- `ml`: `python -m pytest`, then `python predict.py` and check the park-level output.
- `worker`: `python -m pytest`, then a dry run on a sample clip with `--annotate-dir` and a look at the images.
- `web`: `npm run lint`, `npm run build`, `npm test`, then a headless-Chromium load with no console errors, checking the grey parks, chat on a greyed park, the prediction label and Dev mode.
- On the demo laptop: Demo mode shows a new sighting about every 10 s, and a Live-mode still arrives within 60 s.

## Risks
- The iNaturalist fetch needs network access, so run it attended.
- The migration must be run in the real Supabase project by hand.
- A merge conflict with the teammate in `worker/`, mitigated by the small hook.
- Demo laptop inference speed.
