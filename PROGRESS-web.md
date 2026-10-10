# PROGRESS (web + social run)

Log for the `overnight/web-social` run. Newest entry at the bottom. Put the summary of the latest run in this block.

## Latest run summary

**Web run, 2026-10-10 (supervised): all 6 tasks built. `npm run lint`, `npm run build` and `npx vitest run` (14 tests) pass; a headless Chromium script (NPS image URL intercepted, nothing hit the real cam) passed 27 checks with no console errors.**

Not verified: nothing has run against a real Supabase project (`supabase/social.sql`, realtime chat, comments inserts, the rate-limit trigger are reviewed, not executed). The demo `<video>` was only checked for its src, not playback (Playwright's Chromium lacks H.264). Chat and comments are mock (cross-tab via BroadcastChannel) without keys.

For the merge with `overnight/pipeline`: `usePredictions` already reads `/predictions.sample.json` (offset_minutes + generated_at) with a hard-coded fallback; the file arrives with the pipeline branch. Mock cameras use the seed's names. Demo clips in `web/public/demo/` are 15 s, 640 px re-encodes of NPS public-domain Lamar Valley bison clips (`Copyright Info: Public domain`, nps.gov/yell/learn/photosmultimedia/vl_bisoncalves.htm), about 640 KB total.

## Log
