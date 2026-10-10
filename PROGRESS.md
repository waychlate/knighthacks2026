# PROGRESS

Log for unattended runs. Newest entry at the bottom. Put the summary of the latest run in this block.

## Latest run summary

_No unattended run yet._

## Log

### Task 1: Environment (done 2026-10-10)
- Python 3.12.15 installed with `uv` (bootstrapped in a scratchpad venv, not global); `worker/.venv` created (gitignored).
- Installed torch 2.6.0+cu124 / torchvision 0.21.0+cu124 plus `worker/requirements.txt`. First attempt timed out on a CUDA wheel download; retried with `UV_HTTP_TIMEOUT=600`.
- Verified: `import torch, ultralytics, open_clip` works; `torch.cuda.is_available()` is True (RTX 4070 Laptop).
- Weights: BioCLIP (`imageomics/bioclip`) downloaded to the Hugging Face cache; `yolov8n.pt` downloads into the working directory on first run (gitignored `*.pt`).

### Task 2: Worker testable without models (done)
- `main.py`: per-frame logic is now `process_frame(frame, ts, camera, detector, classifier, deduper, sink)`; sinks are `LogSink` (dry run) and `StoreSink` (Supabase). Heavy imports and `dotenv` stay inside `main()`.
- Verified: `python -m pytest` in `/worker` passes (14 tests: logs a sighting, no detections, below-threshold, cooldown dedupe, two animals per frame, plus task 3 tests), also with torch/ultralytics/open_clip import-blocked.

### Task 3: Image-URL source (done)
- `capture.image_frames(url, every, ...)` polls via `still_poller.fetch_still` (User-Agent, ETag skip, minimum 30 s, errors propagate). `main.py` treats `http(s)://...jpg|jpeg|png` sources as image mode and tags them `source_kind='live'`; files/video are `replay`; `--source-kind`, `--every`, `--park` flags added. `db.py` now sends `source_kind` and `cameras.park`, which need the schema change in task 5 before a real Supabase run.
- Verified with fakes only (fake fetcher/decoder/sleep); the live NPS URL was not fetched by this run. `--help` works.

### Task 4: Real-pipeline check (done, with caveats)
- **Species list:** `worker/species.json` is now the 14-animal Yellowstone list (model knowledge, not checked against NPSpecies).
- **Clips (public domain, all `Copyright Info: Public domain` on the NPS page, <https://www.nps.gov/yell/learn/photosmultimedia/vl_bisoncalves.htm>):** three 1280x720 Lamar Valley bison-calf clips (47 s, 43 s, 20 s) downloaded from the NPS video embed pages to `worker/sample_videos/nps/` (gitignored): `yell-Bison00704MTS`, `yell-Bison00715MTS`, `yell-Bison00772MTS`. The NPS page itself notes one clip may no longer be available. No YouTube downloads.
- **Pipeline runs end to end** (`python -m animal_worker.main --source <clip> --dry-run`): YOLO + BioCLIP on the RTX 4070 (CUDA) took ~25 s wall time for the 20 s clip including model load (~1 fps sampling). First correct `SIGHTING` line: `American bison (Bison bison) 100%`.
- **Accuracy problem found:** the first run logged 8 different "species" for one bison clip. Cause: the crops are mostly red-orange calves (read as deer, coyote, crane) and body/leg fragments, plus a softmax over 14 candidates that is overconfident.
- **Prompt tuning:** scored 5 prompt variants on all 592 YOLO crops from the three clips (every crop is a bison): scientific only 47% correct; common only 48%; **"scientific (common)" 59%**; ensemble of the three 35%; taxonomy-prefix 41%. Switched `classifier.py` to `a photo of {scientific} ({common}).`. Even so, among crops BioCLIP is >80% confident about, 246 were right and 53 wrong, so ~18% of confident labels on this hard (calves, fragments) footage are wrong. `--min-confidence` stays 0.5; raising it trades misses for fewer false sightings. Adult animals in clear view were reliably right (bison 0.93-1.00).
- **Electric Peak frames (collector output):** 193 frames so far, 03:08-06:22 cam time, all night infrared with nothing visible except sensor noise and a tiny speck. 19 sampled frames gave 0 detections, which is correct. Whether YOLO (trained on COCO, small distant animals) finds elk/bison at dawn is untested until daylight frames exist.
- **COCO limit:** YOLO's animal classes are bird, cat, dog, horse, sheep, cow, elephant, bear, zebra, giraffe. Elk, bison, pronghorn and deer rely on being detected as horse/cow/sheep; a miss there never reaches BioCLIP.
