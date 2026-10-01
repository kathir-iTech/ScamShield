# Gold Evaluation Dataset

## What this directory is

The gold set (`gold_dataset.csv`) is ScamShield's **evaluation-only** benchmark: 308
hand-checked samples used to measure the model and the full pipeline. It is never
used for training, tuning, or rule fitting.

### Current size and distribution

| Property | Value |
|---|---|
| Total samples | **308** (1 header + 308 rows in `gold_dataset.csv`) |
| Labels | **180 scam / 128 safe** |
| Languages | **en 248, hi-en 21, ta-en 20, te-en 19** |
| Categories | 29 (20 scam families + 9 legitimate families) |

### Why evaluation-only

Labelling gold data against known training data would leak the benchmark into the
model. `LEAKAGE_REPORT.md` documents the leakage audit that produced this set: 309
candidates were checked with exact match, cleaned exact match, 4-gram near-duplicate
overlap, and template-variant detection; 1 leaked candidate was removed and **308
passed with zero contamination**. Every claim in this README depends on that staying
true — gold text must never appear in `backend/data/*.csv` or any v2 training file.

## Labelling workflow (human-in-the-loop)

1. **Build a queue.** From the repo root:

   ```
   python datasets/gold/active_learning.py --stats
   python datasets/gold/active_learning.py --pool backend/data/scam_dataset.csv \
       --out datasets/gold/label_queue.csv --top 500
   ```

   The queue ranks candidate texts by model uncertainty (top-2 probability margin)
   and, with `--use-pipeline`, by disagreement between the raw ML model and the
   rule/refinement layer. Output columns: `rank,text,model_prob_scam,uncertainty,
   disagreement,language,suggested_label,reason`. Ranking is deterministic, so
   re-runs reproduce the same queue.

2. **Label the top rows.** Follow `docs/v2/ANNOTATION_GUIDE.md` for label rules
   (`scam` vs `safe`, category assignment, native-script and transliterated input).
   Label from the text itself — never from `suggested_label`, which is only a hint.

3. **Leakage-check before appending.** Re-run the checks in `LEAKAGE_REPORT.md`
   (exact, cleaned-exact, 4-gram overlap, template variant) against
   `backend/data/scam_dataset.csv` and the v2 datasets. Reject or paraphrase any
   candidate that fails.

4. **Append to `gold_dataset.csv`** with the full column set (`id,text,text_clean,
   language,category,is_scam,risk_level,ground_truth_label,source,version,
   extracted_entities,annotation_notes,created_at,updated_at`).

5. **Re-run the gate.**

   ```
   python evaluation/scripts/ci_gate.py
   ```

## Acceptance criteria for a new gold label

A row is accepted only when all of the following hold:

- **Source**: taken from a `label_queue.csv` entry or a documented real-world report,
  with `source` and `annotation_notes` filled in.
- **Independent judgement**: labelled by a human per `docs/v2/ANNOTATION_GUIDE.md`,
  not copied from any model output, rule output, or `suggested_label`.
- **Leakage-free**: passes every check in `LEAKAGE_REPORT.md` against all training
  datasets.
- **Unambiguous label**: `is_scam` and `ground_truth_label` agree; ambiguous texts
  (judgement-call borderline cases) are excluded rather than forced.
- **Complete row**: all 14 columns present; `language` is one of `en`, `hi-en`,
  `ta-en`, `te-en` (or a new code added deliberately); `category` matches the
  taxonomy in `GOLD_DATASET_REPORT.md`.
- **Duplicate-free**: not already present (exact or 4-gram near-duplicate) in the
  gold set.

## Path from 308 → 2,000 labels

| Milestone | Labels | How |
|---|---|---|
| Today | 308 | Existing hand-written set (`build_gold.py`, seed 42) |
| Stage 1 | ~800 | Drain the highest-uncertainty queue from `active_learning.py` (660 pool rows currently sit at uncertainty ≥ 0.5) |
| Stage 2 | ~1,500 | Add the moderate-uncertainty band (2,823 pool rows at uncertainty ≥ 0.25) plus targeted collection of native-script and non-English traffic, which the current pool under-represents |
| Stage 3 | 2,000 | Fill remaining gaps (ROMANCE/INVESTMENT FNs, legitimate near-misses) with real reported messages; `--stats` prints the live shortfall against the 2,000 target |

Growth is gated on the acceptance criteria above — volume never outranks label quality.

## No further tuning until 2,000

`MODEL_STATUS.md:62` freezes tuning against the current set:

> "FPR 14.06% / Recall 77.2% is the current accepted baseline. Do not re-tune against
> the 308-sample gold set further without adding more gold data first — further
> tightening here risks overfitting to this specific set."

Accordingly: **no rule weights, thresholds, model hyperparameters, or decision logic
are tuned against this set until it reaches 2,000 accepted labels.** Work in the
mechanism — evaluation pipelines, gates, queue building, preprocessing correctness —
and grow the data; the numbers move only when the evidence base moves.
