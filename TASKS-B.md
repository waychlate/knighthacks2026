# TASKS-B: data, QA and the story

**Goal:** make the project judge-ready: other parks' species lists, a tester's eye on the app, and the Devpost write-up, slides and demo script. Judges read the story first, so this is as important as the code.

You work in `docs/` and `worker/species_*.json`. Do **not** touch other code or `.env`. Branch: `b/story`.

## 0. Set up (20 min)
```bash
git clone git@github.com:waychlate/knighthacks2026.git && cd knighthacks2026
git checkout -b b/story
mkdir -p docs
```
Read `README.md`, `CLAUDE.md` (project overview and tracks), `ml/README.md`, and `PROGRESS.md` (what is verified and what is not).

## 1. Test the app like a visitor (1 to 2 h) -> `docs/qa.md`
Open the deployed site (C gives you the link; until then ask C to share a screen or run `cd web && npm install && npm run dev`). Do this on your **phone** and on a laptop:
- Switch Demo and Live. Does the bubble change (amber "Demo clip" / green "Live")?
- Open each camera. Does the video play? Does Live say "Live feed unavailable" if it cannot load (it must NOT quietly show the demo clip)?
- Post in the chat from two devices. Does it appear on both? Try a rude word (it should be blocked) and a very long message.
- Add a comment on a sighting. Open Analytics. Rotate your phone.
Write each problem as: what you did, what you expected, what happened, device. Number them. Send the list to C. Re-test the fixes later.

## 2. Test our README from a clean clone (1 h) -> `docs/readme-test.md`
On a fresh clone, follow `README.md` section 1 (the web app) exactly. Write down every place where you got stuck or the instructions were wrong. This is how we know a judge could run it.

## 3. Species lists for other parks (1 to 2 h)
We can say "plug in any park". Prove it with 2 more parks, for example Everglades (Florida) and Great Smoky Mountains. For each, create `worker/species_<park>.json` in the same format as `worker/species.json` (10 to 14 animals the cameras could realistically see; common name + scientific name).
- Source: the NPS species list at https://irma.nps.gov/NPSpecies (park codes EVER, GRSM). Write the source and date in a `_comment` field.
- Keep each list short: fewer candidates means BioCLIP gets it right more often.
- Check the Latin names are spelled correctly (a typo means BioCLIP is asked about a name it does not know).

## 4. Devpost text -> `docs/devpost.md`
Sections: **Inspiration**, **What it does**, **How we built it**, **Challenges**, **What we learned**, **What's next**. Plain English for non-experts. Include:
- The pipeline in one sentence: camera image -> YOLO finds an animal -> BioCLIP (a Hugging Face model) names the species -> saved to a database -> shows up live on the site.
- A paragraph for each prize track we want: **Best First Time**, **Best AI Hack**, **Best Use of a Hugging Face Model**. For the Hugging Face one, say exactly which model (`imageomics/bioclip`) and what it does.
- **Be honest:** the live Yellowstone cam rarely shows animals, so the demo uses recorded clips (labelled "Demo clip"); the predictions use synthetic data; species ID is about 59% right on hard footage (bison calves) and better on clear adults. Judges respect honesty; they punish spin.
- Credit: images and clips are from the National Park Service (public domain).

## 5. Slides and the 3-minute demo script -> `docs/slides-outline.md`, `docs/demo-script.md`
5 to 6 slides: problem, solution, live demo, how the AI works (a simple diagram), honest limits, what's next. The demo script is a table: **time | who speaks | what is on screen | what to say.** The demo runs on C's laptop (the only GPU): C runs the worker on a clip in a terminal while the website shows the feed. Keep a backup plan: if the wifi dies, what do we show? (Answer: the local web app plus the worker in `--dry-run`.)

## 6. Hand in
```bash
git add docs/ worker/species_*.json
git commit -m "Add QA notes, devpost draft, slides outline, demo script, park species lists"
git push -u origin b/story
```
Open a Pull Request to `main`. Push small and often, not once at the end.

## Definition of done
`docs/qa.md` with a numbered bug list, `docs/readme-test.md`, 2 species files, `docs/devpost.md`, `docs/slides-outline.md`, `docs/demo-script.md`. Everything honest about what is real and what is synthetic.
