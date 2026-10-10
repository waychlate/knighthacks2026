# Teammate 2: frontend and QA

**Your job:** make the website feel finished and trustworthy, and find what is broken before a judge does. You work in `web/` and `docs/`. Branch: `web/polish` (any branch starting `web/` is fine). The app is already built; your work is testing, wording, styling and small fixes, not new features.

## 0. Set up (20 min)
```bash
git clone git@github.com:waychlate/knighthacks2026.git && cd knighthacks2026
git checkout -b web/polish
cd web && npm install && npm run dev     # needs Node 18+; open the printed localhost link
```
It runs on **mock data** with no keys; that is normal. Before every commit run `npm run lint && npm run build && npm test` and fix anything red. Read `README.md` (what the app is) and `CLAUDE.md` (the data model).

## Where things live
| You want to change | File |
|---|---|
| Header, page layout, banners | `web/src/App.jsx` |
| The Demo/Live switch | `web/src/components/ModeToggle.jsx` |
| Camera video and the Live/Demo bubble | `web/src/components/CameraPanel.jsx` |
| Sighting cards, comments button | `web/src/components/SightingCard.jsx` |
| Chat and comment boxes | `web/src/components/ThreadPanel.jsx` |
| Prediction card ("Predicting a ... around ...") | `web/src/components/PredictionCard.jsx` |
| Pages: feed, cameras, one camera, analytics | `web/src/pages/` |
| Mock sightings, mock chat | `web/src/lib/mock.js` |
Styling is Tailwind classes right in the JSX (for example `text-sm text-stone-500`). Make small edits, reload, look, repeat. Do not edit `web/src/lib/cameraConfig.js`, anything in `supabase/`, or `.env` without asking.

## 1. Test the app like a visitor (1 to 2 h) -> `docs/qa.md`
Do this on your **phone** and a laptop (the deployed link comes from the project owner; until then use `npm run dev`):
- Switch Demo and Live. Does the bubble change (amber "Demo clip", green "Live")?
- Open each camera. Does the video play? In Live mode, does a failed image say "Live feed unavailable" (it must never quietly play the demo clip)?
- Post in the chat from two devices: does it show on both? Try a rude word (blocked) and a very long message.
- Add a comment on a sighting. Open Analytics. Rotate the phone. Try the page on a slow connection.
Write each problem as: what you did, what you expected, what happened, device. Number them and send the list to the project owner. Fix the ones that are wording or styling yourself.

## 2. Wording and empty states (1 h)
Read every message a visitor sees (empty feed, no comments, errors, the mock-data banner, the "Waiting for the first sighting" text). Make them clear, friendly and honest. Never call mock or sample data real.

## 3. Test our README from a clean clone (1 h) -> `docs/readme-test.md`
In a fresh folder, follow `README.md` section 1 exactly. Write down every place where you got stuck or the instructions were wrong, so we can fix them.

## 4. Screenshots (30 min) -> `docs/screens/`
Once the site is deployed, take clean screenshots (phone and laptop width): feed, a camera page in Demo and Live, analytics, chat. Name them clearly (`feed-demo.png`). These go in the README and the Devpost page. Do not use screenshots with real people's names or messages.

## 5. Slides visuals (1 h) -> `docs/slides-outline.md`
Help turn the project into 5 to 6 slides: problem, solution, live demo, how the AI works (a simple diagram; the README has one), honest limits, what's next. Pick the screenshots for each slide.

## 6. Stretch (only if everything above is done)
A park selector in the web app so the second park's species list shows up. Ask the project owner before starting; it touches data code.

## Hand in
```bash
git add web/ docs/
git commit -m "Polish wording and styling, add QA notes and screenshots"
git push -u origin web/polish
```
Open a Pull Request to `main`. Small, frequent pushes beat one big one at the end.

## Done means
`docs/qa.md` with a numbered bug list, `docs/readme-test.md`, screenshots in `docs/screens/`, wording fixed, and lint, build and tests green.
