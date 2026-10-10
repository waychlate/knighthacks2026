# TASKS-A: make the detector see small animals

**Goal:** the live Electric Peak cam is a wide mountain landscape (1920x1080). A real animal there would be a few dozen pixels wide, and YOLO shrinks the frame to about 640 px before looking, so it never sees one. You will try **tiling**: cut the big frame into overlapping 640 px squares, run YOLO on each, and merge the results. Cap: **3 hours.** If it does not help, that is a fine result: measure it and write it down.

You work in `worker/` only. Do **not** touch `web/`, `supabase/`, or `.env`.

## 0. Set up (about 45 min, most of it downloading)
```bash
git clone git@github.com:waychlate/knighthacks2026.git && cd knighthacks2026
git checkout -b a/tiling
cd worker
python3 -m venv .venv && source .venv/bin/activate     # Python 3.10 to 3.12. If yours is 3.13+, ask C.
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu   # CPU version, you have no GPU
pip install -r requirements.txt
python -m pytest                                        # expect: 14 passed
```
Get the saved frames from C (a zip of about 350 JPEGs from the live cam). Unzip into `worker/sample_videos/yellowstone/`. Get one bison clip too (`worker/sample_videos/nps/*.mp4`). These folders are gitignored on purpose.

Smoke test (expect a few `SIGHTING` lines; CPU is slow, a short clip takes a few minutes):
```bash
python -m animal_worker.main --source sample_videos/nps/yell-Bison00772MTS_1280x720.mp4 --camera "Test" --dry-run
```

## 1. Look at the problem (15 min)
Open 3 files from `sample_videos/yellowstone/` (one night, one morning, one midday). Notice: no animals, and anything that appeared would be tiny. Read `worker/animal_worker/detector.py` (35 lines). `detect(frame)` runs YOLO once on the whole frame and returns crops.

## 2. Write `worker/animal_worker/tiling.py`
```python
def tiles(frame, size=640, overlap=0.2):
    """Yield (x_offset, y_offset, tile) squares that cover the whole frame."""
```
- Step = `int(size * (1 - overlap))`. Cover the right and bottom edges too (last tile may start earlier so it still fits).
- Write `worker/tests/test_tiling.py` first: a fake 1080x1920 numpy array; check every pixel is covered by at least one tile, tiles are `size x size` (or smaller only if the frame is smaller), and offsets are correct.
- Run `python -m pytest`; it must still say all passed.

## 3. Use it in the detector (behind a flag)
In `detector.py` add `detect_tiled(frame)`: for each tile call the same YOLO predict, add the tile offset to each box, then remove duplicates (the same animal can show up in two overlapping tiles; keep the one with the higher score when two boxes overlap more than 50%, called IoU). Return the same `Detection` objects (crop from the **original** frame, not the tile). Keep `detect()` unchanged. Add `--tiles` to `main.py` (off by default; it is slower).

## 4. Measure it honestly (no real small animals exist in our frames)
Make a **synthetic test**: take one frame from the bison clip, crop out a bison, resize it to 200, 120, 80, 50 and 30 px wide, paste each into a real cam frame at a random spot. Run `detect()` and `detect_tiled()` on each. Fill in this table in a new file `worker/TILING.md`:

| animal width | normal found? | tiled found? | seconds (tiled) |
|---|---|---|---|
| 200 px | | | |
| 120 px | | | |
| 80 px | | | |
| 50 px | | | |
| 30 px | | | |

Write 3 sentences: did tiling help, how much slower is it, and what is the smallest size that still works. **Label this "composite test, not real footage."** Also run `--tiles` on 20 real cam frames and note the number of detections (probably 0, and that is fine) and false alarms.

## 5. Hand in
```bash
git add worker/animal_worker/tiling.py worker/animal_worker/detector.py worker/animal_worker/main.py worker/tests/test_tiling.py worker/TILING.md
git commit -m "Add tiled detection for small animals"
git push -u origin a/tiling
```
Open a Pull Request to `main` on GitHub. C reviews it.

## If you finish early (stretch)
BioCLIP on a 30 px crop is hopeless. Try upscaling small crops to 224 px before classifying and see whether the label gets better on your composites. Record it in `TILING.md`.

## Definition of done
Tests pass, `--tiles` works, `TILING.md` has the table and the 3 sentences, PR is open. A negative result ("tiling did not help below 50 px") counts.
