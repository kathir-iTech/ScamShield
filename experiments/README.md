# Validation Harness — Client-Side Pipeline

This directory contains the **validation harness** for the client-side (browser) ScamShield pipeline. It is *not* part of the production app — `frontend/src/lib/scamshield/` is — but it proves the JS pipeline is a faithful 1:1 port of the Python backend.

## What it validates

1. **Gold-set text (308 messages)** — `datasets/gold/gold_dataset.csv` contains 308 labeled messages with `risk_level` ground truth.
   - `compare_pipelines.js` runs the JS pipeline (`frontend/src/lib/scamshield/pipeline.js` or `experiments/pipeline.js`) on all 308 and writes `js_results.json`.
   - `compare_python_side.py` runs the Python backend (`backend/services/orchestrator.py:analyze_text`) on the same 308 and writes `comparison_results.json` comparing `js_risk_level` vs `py_risk_level`.
   - **Bar:** 308/308 exact `risk_level` + `prediction` match (validates no drift).

2. **OCR — 25 test images × 2 sets (clean + noisy)**
   - `gen_ocr_images.py` / `gen_ocr_images_noisy.py` generate 25 PNGs from fixed seed `20260730` (see `ocr_manifest.json` — 13 scam + 12 legitimate, includes hard-gate `img_001`/`img_004`). Regenerable; images are *not* committed (see `.gitignore`).
   - `ocr_js.js` (tesseract.js) and `ocr_python.py` (Python tesseract) OCR each image → `ocr_js_results.json` / `ocr_python_results.json` (and `_noisy` variants).
   - `compare_ocr_4way.js` + `ocr_pypipeline.py` run **both** pipelines on **both** OCR texts and check agreement. Honest result is **24/25 on noisy** with the single mismatch being `img_020` (genuinely destroyed image — two engines hallucinate different garbage, not a pipeline bug). Hard-gate `img_001`/`img_004` must agree on both clean and noisy.

3. **Artifacts**
   - `export_model.py` exports `vectorizer.js` / `model.js` from the trained sklearn model (TF-IDF + LogisticRegression) — these are the files now self-hosted in `frontend/src/lib/scamshield/` and `frontend/public/tessdata/`.
   - `repair_urls.js` / `repair_urls.py` — URL-repair pass for OCR-mangled URLs, applied before pipeline.

## How to re-run (from repo root)

```bash
# 1) Gold text — JS side
node experiments/compare_pipelines.js
# → experiments/js_results.json

# 2) Gold text — Python side (requires backend venv)
python experiments/compare_python_side.py
# → experiments/comparison_results.json  (check 308/308)

# 3) OCR — generate images (fixed seed, deterministic)
python experiments/gen_ocr_images.py
python experiments/gen_ocr_images_noisy.py
# → experiments/ocr_test_images/ + _noisy/ + ocr_manifest.json

# 4) OCR — run both engines
node experiments/ocr_js.js          # → ocr_js_results.json
node experiments/ocr_js.js experiments/ocr_test_images_noisy experiments/ocr_js_noisy_results.json
python experiments/ocr_python.py    # → ocr_python_results.json
python experiments/ocr_python.py experiments/ocr_test_images_noisy experiments/ocr_python_noisy_results.json

# 5) OCR — 4-way pipeline comparison
node experiments/compare_ocr_4way.js
python experiments/ocr_pypipeline.py
# → ocr_pypipeline_results.json

# 6) Integrated app validation (uses frontend/src/lib/scamshield/pipeline.js, the real built artifact)
node frontend/scripts/validate-text.mjs    # → 308/308
node frontend/scripts/validate-ocr.mjs     # → 25/25 clean, 24/25 noisy (img_020)
```

## Regenerable vs committed

- **Committed (harness):** `*.py`, `compare_*.js`, `ocr_*.js`, `gen_*.py`, `export_model.py`, `repair_urls.*` (source), `package.json` — the *generators* and *comparators*.
- **Ignored (regenerable):** `experiments/*.json` (results/comparisons), `ocr_test_images/`, `ocr_test_images_noisy/`, `__pycache__/`, `node_modules/`, plus `vectorizer.js`/`model.js`/`pipeline.js`/`repair_urls.js`/`eng.traineddata` when they exist in `experiments/` (the canonical copies now live in `frontend/src/lib/scamshield/` + `frontend/public/`).

## Notes

- `eng.traineddata` (5.2 MB raw, 2.8 MB gzipped) is self-hosted in `frontend/public/tessdata/` for offline capability; tesseract.js is configured with `langPath:'/tessdata', workerPath:'/tesseract/worker.min.js', corePath:'/tesseract/tesseract-core.wasm.js', gzip:true` (see `frontend/src/services/ocr.ts`).
- The harness is intentionally **honest**: 24/25 not 25/25 on noisy, and hard-gate evidence is shown with before/after, not asserted.
