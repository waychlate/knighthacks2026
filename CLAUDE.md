# CLAUDE.md

Guidance for Claude Code when working in this repository (KnightHacks 2026 hackathon project).

## Project overview

**Animal Logger**: a wildlife sighting log for parks. Cameras placed in a park detect and identify animals; a web app/website shows a feed of recent sightings.

A visitor opens the app and sees a live log of recently seen animals. Each entry shows:

- **Species** (what animal was seen)
- **Camera** (which camera saw it, ideally with its location in the park)
- **Timestamp** (when it was seen)

### Stretch goal: sighting predictions

Store sightings in a database, analyze them, and train an ML model to find patterns in when and where species appear. Surface this to users as predictions, e.g. "Predicting a [bird species] around 2:30 PM."

## Priorities

This is a hackathon project, so build in this order and keep each stage demoable:

1. **Sighting log (MVP)**: data model, an API to create and list sightings, and a UI feed showing species, camera, and timestamp.
2. **Detection pipeline**: camera image/video in, species label out (pretrained classifier or detector; do not train from scratch). Stub with fake or seeded data until this works.
3. **Analytics**: charts or summaries of sightings over time (by species, camera, hour of day).
4. **Prediction**: model trained on logged sightings, with predictions displayed in the UI.

Prefer a working end-to-end slice over polishing any single layer. Seed data and mock cameras are fine for demos.

## Data model (draft)

- `Camera`: id, name, location (lat/lng or label), status
- `Species`: id, common name, scientific name, optional image
- `Sighting`: id, species_id, camera_id, timestamp (UTC), confidence, optional image/clip URL

Store timestamps in UTC and convert to the park's local time only for display. Sightings should be append-only; the prediction work depends on clean history.

## Tech stack

**Not yet decided.** Update this section once chosen, and then fill in the commands below. Until then, don't assume a framework; ask or propose one before scaffolding.

## Commands

_To be filled in once the stack is chosen (install, dev server, tests, lint, build)._

## Conventions

- Keep changes small and focused; commit often with clear messages.
- Don't commit secrets, API keys, or large media/model files. Use `.env` (gitignored) and provide a `.env.example`.
- Keep detection, API, UI, and ML code in separate directories so teammates can work in parallel without conflicts.
- Identify the data contract (the `Sighting` shape) early and keep it consistent across all layers.
- Write a short README section for anything a teammate needs to run or demo.
- Add tests for the data layer and any prediction logic; UI tests are optional given hackathon time.

## Working agreements for Claude

- Check this file and the README before making structural decisions; update this file when the stack, commands, or data model change.
- Ask before adding heavy dependencies or paid/external services.
- Develop on the designated feature branch; don't open a PR unless asked.
