> **Archived.** Finished or superseded; kept for history. Current plan: [TEAM.md](../../TEAM.md).

# TASKS-web (web + social run)

Backlog for the **`overnight/web-social`** branch. Follow "Unattended / overnight mode" in CLAUDE.md. Work top to bottom. Mark a task `[x]` only when every acceptance check passed; otherwise leave it and log the blocker in `PROGRESS-web.md`.

The pipeline run has its own file, `TASKS.md`, on `overnight/pipeline`. Do not do its tasks.

## Ownership

- **You own:** all of `/web` (except `web/public/predictions.sample.json`, which you only read), `supabase/social.sql`, `PROGRESS-web.md`.
- **Do not touch:** `/worker`, `/ml`, `supabase/schema.sql`, `supabase/seed.sql`, `TASKS.md`, `PROGRESS.md`. You need no Python, GPU or model downloads; only Node and `npm install`.

## Shared data contract (both runs rely on this)

- `sightings.source_kind` is `'live'` or `'replay'`. `cameras.park` is a park slug (default `'yellowstone'`). The pipeline run adds these to `supabase/schema.sql`; **you add them to `web/src/lib/mock.js` yourself** so the app runs with no keys. If real rows lack them, treat missing `source_kind` as `'replay'` and missing `park` as `'yellowstone'`.
- Comments and chat messages never go into `sightings`. They live in tables defined in `supabase/social.sql` (yours).
- Anything mock/synthetic is labeled as such in the UI.

## Context for this run

- Chosen live source: NPS Yellowstone "North Entrance - Electric Peak", a still at `https://www.nps.gov/webcams-yell/mammoth_electric.jpg`, refreshed every 30-60 s. **In headless checks, mock the image URL (intercept the request); never load that URL from an unattended run.** The page itself may reference it; a person viewing it in a browser is the intended use.
- Camera list: Electric Peak is the one real camera (works in both modes). Add 2-3 more Yellowstone cameras that exist only in Demo mode, labeled as demo cameras; in Live mode they show greyed out with "No live feed". Other parks come tomorrow, so keep park as data, not hard-coded.
- Demo clips: put short public-domain or CC0 clips (or a placeholder poster image if none are available) in `web/public/demo/`; keep files small and note the source and license in `PROGRESS-web.md`. Never download from YouTube.

## 1. Camera list, camera view, Demo/Live toggle
- [x] Header toggle **Demo / Live**, default Demo, remembered in `localStorage` (wrapped in try/catch). One shared hook/context.
- [x] Cameras page lists cameras per the rules above. Clicking a camera opens its view with a video panel: Demo mode loops the demo clip; Live mode shows the latest still, refreshed every 60 s with a cache-busting query.
- [x] Bubble in the panel's top-left: green pulsing dot "Live", or amber "Demo clip". If the live image fails to load, show "Live feed unavailable"; **never fall back to the demo clip while the toggle says Live**.
- [x] The sightings feed filters by `source_kind` to match the mode. Empty live feed says "Waiting for the first sighting".
- [x] Pure helper functions (mode filtering, live-URL cache-busting) in `web/src/lib/` with vitest tests.
- Accept: `npm run lint`, `npm run build`, `npx vitest run` pass; headless Chromium (with the NPS URL intercepted) shows the bubble flipping with the toggle and no console errors.

## 2. Per-park live chat
- [x] `supabase/social.sql`: `chat_messages(id, park text, display_name text, body text check length <= 280, created_at timestamptz default now(), is_hidden boolean default false)`. RLS: public read where not hidden, anon insert only (no update/delete), length and non-empty checks, a per-name rate-limit trigger (e.g. at most 1 message per 2 s per name). Add the table to the realtime publication. Keep the file re-runnable.
- [x] Chat panel on the park/camera view: one room per park (the camera's `park`), display name stored in `localStorage`, live updates via Supabase Realtime. With no keys, use an in-memory mock room labeled as sample chat (cross-tab via `BroadcastChannel` is a nice touch, optional).
- [x] Client-side word filter and 280-char cap in a pure function with vitest tests; disable send for empty or over-length text.
- Accept: lint, build, vitest pass; headless check shows posting a message in one tab appears in the list, no console errors.

## 3. Comments on sightings
- [x] `comments(id, sighting_id, display_name, body <=280, created_at, is_hidden)` in `social.sql` with the same RLS and rate-limit approach. `sighting_id` is a plain uuid, with no foreign key so the file runs standalone.
- [x] Expandable comment thread on each sighting card, same filter and mock behavior as chat.
- Accept: lint, build, vitest pass; headless check adds and shows a comment on a mock sighting.

## 4. Analytics page (cut first if short on time)
- [x] `#/analytics` with a nav link: Recharts for sightings by hour of day, by species, and by camera, from the loaded sightings (respecting the mode toggle). Aggregation in pure functions in `web/src/lib/` with vitest tests.
- Accept: lint, build, vitest pass; headless check of `#/analytics` shows the charts with no console errors.

## 5. Polish and resilience (cut first if short on time)
- [x] Error banner when a Supabase request fails instead of an empty list.
- [x] Layout check at 375 px and 900 px (headless screenshots); fix overflow.
- [x] Basic accessibility: labels, focus styles, `aria-current`, alt text; toggle and bubble readable by screen readers.
- Accept: lint and build pass; screenshots look right.

## 6. Docs
- [x] Short README section for the web app: Demo/Live toggle, where demo clips live, how chat and comments work, how to load `supabase/social.sql`.
