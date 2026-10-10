# Teammate 1: ML and detection

**Your job:** make the detector see small animals (tiling), and be the person who can explain how our AI and predictions work. You work in `ml/` and `worker/`. Branch: `ml/tiling` (any branch name starting `ml/` is fine).

## The problem
The live Electric Peak cam is a wide mountain landscape (1920x1080). A real animal there would be a few dozen pixels wide, and YOLO shrinks the frame to about 640 px before looking, so it never sees one. **Tiling** cuts the big frame into overlapping 640 px squares, runs YOLO on each, and merges the results. Cap: **3 hours.** If it does not help, that is a fine result: measure it and write it down.

## 0. Set up (about 45 min, most of it downloading)
```bash
git clone git@github.com:waychlate/knighthacks2026.git && cd knighthacks2026
git checkout -b ml/tiling
cd worker
python3 -m venv .venv && source .venv/bin/activate     # Python 3.10 to 3.12. If yours is 3.13+, ask for help.
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu   # CPU version, no GPU needed
pip install -r requirements.txt
python -m pytest                                        # expect: 14 passed
```
Get the saved cam frames (a zip of about 350 JPEGs) and one bison clip from the project owner, and unzip them into `worker/sample_videos/yellowstone/` and `worker/sample_videos/nps/`. Those folders are gitignored on purpose.

Smoke test (CPU is slow; a short clip takes a few minutes):
```bash
python -m animal_worker.main --source sample_videos/nps/yell-Bison00772MTS_1280x720.mp4 --camera "Test" --dry-run
```

## 1. Look at the problem (15 min)
Open 3 frames from `sample_videos/yellowstone/` (night, morning, midday): no animals, and anything there would be tiny. Read `worker/animal_worker/detector.py` (35 lines): `detect(frame)` runs YOLO once on the whole frame and returns crops.

## 2. Write `worker/animal_worker/tiling.py`
```python
def tiles(frame, size=640, overlap=0.2):
    """Yield (x_offset, y_offset, tile) squares that cover the whole frame."""
```
- Step = `int(size * (1 - overlap))`. Cover the right and bottom edges too (the last tile may start earlier so it still fits).
- Write `worker/tests/test_tiling.py` first: a fake 1080x1920 numpy array; check every pixel is covered by at least one tile, tiles are `size x size`, and offsets are correct. `python -m pytest` must still pass.

## 3. Use it in the detector (behind a flag)
In `detector.py` add `detect_tiled(frame)`: run the same YOLO predict on each tile, add the tile offset to each box, then remove duplicates (the same animal can appear in two overlapping tiles: when two boxes overlap by more than 50%, called IoU, keep the higher score). Return the same `Detection` objects, with crops cut from the **original** frame. Keep `detect()` unchanged. Add `--tiles` to `main.py` (off by default; it is slower).

## 4. Measure it honestly (we have no real small animals)
Make a **synthetic composite test**: take a frame from the bison clip, crop out a bison, resize it to 200, 120, 80, 50 and 30 px wide, and paste each into a real cam frame. Run `detect()` and `detect_tiled()` on each. Put this table in `worker/TILING.md`:

| animal width | normal found? | tiled found? | seconds (tiled) |
|---|---|---|---|
| 200 px | | | |
| 120 px | | | |
| 80 px | | | |
| 50 px | | | |
| 30 px | | | |

Write 3 sentences: did tiling help, how much slower is it, and what is the smallest size that still works. **Label it "composite test, not real footage."** Also run `--tiles` on 20 real cam frames and note the detections and any false alarms (probably 0 detections, and that is fine).

## 5. Learn `ml/` well enough to explain it (1 h)
Read `ml/README.md`, run `cd ml && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && python evaluate.py`. You should be able to say, in your own words, in 60 seconds:
- what we predict (the chance of at least one sighting per species, camera and hour),
- why the data is synthetic and what that means for the numbers,
- what "temporal split" is and why we never shuffle across time,
- why the simple hourly profile beat gradient boosting.
Write it down in `docs/devpost-ai.md` as the "How the AI works" and "Limitations" sections for the Devpost page (plain English, honest about the 59% accuracy on hard clips and the empty live cam).

## 6. Species lists for other parks (1 to 2 h, if time)
Create `worker/species_<park>.json` in the same format as `worker/species.json` for 2 parks (for example Everglades, Great Smoky Mountains): 10 to 14 animals each, common and scientific names. Source: https://irma.nps.gov/NPSpecies (park codes EVER, GRSM); note the source and date in a `_comment` field. Short lists work better because BioCLIP has fewer wrong choices. Check the Latin spelling.

## 7. Hand in
```bash
git add worker/ docs/devpost-ai.md
git commit -m "Add tiled detection, species lists, AI write-up"
git push -u origin ml/tiling
```
Open a Pull Request to `main` on GitHub. Push small and often.

## Done means
Tests pass, `--tiles` works, `worker/TILING.md` has the table and the 3 sentences, `docs/devpost-ai.md` exists. A negative result counts. Stretch: upscale tiny crops to 224 px before BioCLIP and see if labels improve.
