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
