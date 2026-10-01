"""
Human-in-the-loop label queue builder.

Ranks unlabelled pool texts by model uncertainty (top-2 probability margin) and,
optionally, by disagreement between the raw ML model and the rule/refinement layer
(--use-pipeline). Writes a deterministic, ranked CSV for human labelling.

Never writes to datasets/gold/gold_dataset.csv.

Usage:
  python datasets/gold/active_learning.py --pool backend/data/scam_dataset.csv \
      --out datasets/gold/label_queue.csv --top 500
  python datasets/gold/active_learning.py --stats
"""
import argparse
import csv
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"
INITIAL_CWD = Path.cwd()
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

import joblib

from config.settings import MODEL_PATH, VECTORIZER_PATH
from core.multilingual import detect_language, preprocess_for_model
from utils.text import clean_text

DEFAULT_POOL = BACKEND_DIR / "data" / "scam_dataset.csv"
DEFAULT_OUT = ROOT / "datasets" / "gold" / "label_queue.csv"
GOLD_DATASET = ROOT / "datasets" / "gold" / "gold_dataset.csv"
GOLD_CURRENT_LABELS = 308
GOLD_TARGET_LABELS = 2000

FIELDNAMES = [
    "rank",
    "text",
    "model_prob_scam",
    "uncertainty",
    "disagreement",
    "language",
    "suggested_label",
    "reason",
]


def _abs(path_str: str) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else (INITIAL_CWD / path)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Build a ranked labelling queue")
    parser.add_argument("--pool", default=str(DEFAULT_POOL), help="CSV with unlabelled candidate texts")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output queue CSV")
    parser.add_argument("--top", type=int, default=500, help="Number of rows to write")
    parser.add_argument("--model", default=str(MODEL_PATH), help="Path to model.joblib")
    parser.add_argument("--vectorizer", default=str(VECTORIZER_PATH), help="Path to vectorizer.joblib")
    parser.add_argument("--text-column", default="text", help="CSV column containing the text")
    parser.add_argument("--use-pipeline", action="store_true",
                        help="Score disagreement against services.orchestrator.analyze_text (slow)")
    parser.add_argument("--stats", action="store_true",
                        help="Print uncertainty distribution instead of writing a queue")
    args = parser.parse_args(argv)
    args.pool = str(_abs(args.pool))
    args.out = str(_abs(args.out))
    args.model = str(_abs(args.model))
    args.vectorizer = str(_abs(args.vectorizer))
    return args


def load_pool(path: str, text_column: str) -> List[str]:
    texts: List[str] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or text_column not in reader.fieldnames:
            raise SystemExit(
                f"ERROR: column '{text_column}' not found in {path} "
                f"(columns: {reader.fieldnames})"
            )
        for row in reader:
            text = (row.get(text_column) or "").strip()
            if text:
                texts.append(text)
    return texts


def score_pool(texts, model, vectorizer, use_pipeline: bool) -> List[Dict]:
    cleaned = [clean_text(preprocess_for_model(t)) for t in texts]
    matrix = vectorizer.transform(cleaned)
    proba = model.predict_proba(matrix)
    classes = list(model.classes_)
    scam_idx = classes.index(1) if 1 in classes else len(classes) - 1
    p_scam = proba[:, scam_idx]

    refined_preds = None
    if use_pipeline:
        from services.orchestrator import analyze_text
        refined_preds = []
        for i, text in enumerate(texts):
            if (i + 1) % 500 == 0:
                print(f"  pipeline {i+1}/{len(texts)}...", file=sys.stderr)
            try:
                result = analyze_text(text)
                refined_preds.append(1 if result.get("refined_prediction") == "scam" else 0)
            except Exception:
                refined_preds.append(None)

    scored: List[Dict] = []
    for i, text in enumerate(texts):
        p = float(p_scam[i])
        margin = abs(2.0 * p - 1.0)
        uncertainty = round(1.0 - margin, 6)
        model_label = "scam" if p >= 0.5 else "safe"
        disagreement = 0
        if refined_preds is not None and refined_preds[i] is not None:
            disagreement = 1 if (refined_preds[i] == 1) != (model_label == "scam") else 0
        if disagreement:
            reason = "model_rule_disagreement"
        elif uncertainty >= 0.5:
            reason = "high_uncertainty"
        elif uncertainty >= 0.25:
            reason = "moderate_uncertainty"
        else:
            reason = "low_uncertainty"
        scored.append({
            "pool_index": i,
            "text": text,
            "model_prob_scam": round(p, 6),
            "uncertainty": uncertainty,
            "disagreement": disagreement,
            "language": detect_language(text),
            "suggested_label": model_label,
            "reason": reason,
            "priority": uncertainty + (1.0 if disagreement else 0.0),
        })
    return scored


def rank_rows(scored: List[Dict]) -> List[Dict]:
    ordered = sorted(scored, key=lambda r: (-r["priority"], -r["uncertainty"], r["text"], r["pool_index"]))
    for position, row in enumerate(ordered, start=1):
        row["rank"] = position
    return ordered


def write_queue(rows: List[Dict], out_path: Path) -> None:
    if out_path.resolve() == GOLD_DATASET.resolve():
        raise SystemExit("ERROR: refusing to write into gold_dataset.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row[k] for k in FIELDNAMES})
    print(f"Wrote {len(rows)} rows to {out_path}")


def print_stats(scored: List[Dict], use_pipeline: bool) -> None:
    buckets = Counter()
    for row in scored:
        u = row["uncertainty"]
        if u < 0.1:
            buckets["0.00-0.10"] += 1
        elif u < 0.25:
            buckets["0.10-0.25"] += 1
        elif u < 0.5:
            buckets["0.25-0.50"] += 1
        elif u < 0.75:
            buckets["0.50-0.75"] += 1
        else:
            buckets["0.75-1.00"] += 1

    n = len(scored)
    ge_01 = sum(1 for r in scored if r["uncertainty"] >= 0.1)
    ge_025 = sum(1 for r in scored if r["uncertainty"] >= 0.25)
    ge_05 = sum(1 for r in scored if r["uncertainty"] >= 0.5)
    disagreements = sum(r["disagreement"] for r in scored)
    needed = max(GOLD_TARGET_LABELS - GOLD_CURRENT_LABELS, 0)

    print(f"Pool size: {n}")
    print("Uncertainty distribution (1 - top2 margin):")
    for key in ["0.00-0.10", "0.10-0.25", "0.25-0.50", "0.50-0.75", "0.75-1.00"]:
        count = buckets.get(key, 0)
        share = (count / n) if n else 0.0
        print(f"  {key}: {count:6d} ({share:6.1%})")
    print(f"uncertainty >= 0.10: {ge_01}")
    print(f"uncertainty >= 0.25: {ge_025}")
    print(f"uncertainty >= 0.50: {ge_05}")
    if use_pipeline:
        print(f"model/rule disagreements: {disagreements}")
    else:
        print("model/rule disagreements: not measured (run with --use-pipeline)")
    print(f"\nGold set: {GOLD_CURRENT_LABELS} labels; target: {GOLD_TARGET_LABELS}; still needed: {needed}")
    if ge_01 >= needed:
        print(f"Projected sample count to reach {GOLD_TARGET_LABELS}: {needed} "
              f"labelled from the {ge_01} pool rows with uncertainty >= 0.10 (pool is sufficient)")
    else:
        shortfall = needed - ge_01
        print(f"Projected sample count to reach {GOLD_TARGET_LABELS}: {needed} labels; "
              f"only {ge_01} informative pool rows available -> collect {shortfall} more texts")


def main(argv=None) -> int:
    args = parse_args(argv)
    if not Path(args.pool).is_file():
        print(f"ERROR: pool not found: {args.pool}", file=sys.stderr)
        return 2
    texts = load_pool(args.pool, args.text_column)
    if not texts:
        print("ERROR: pool contains no texts", file=sys.stderr)
        return 2
    try:
        model = joblib.load(args.model)
        vectorizer = joblib.load(args.vectorizer)
    except Exception as exc:
        print(f"ERROR: failed to load model/vectorizer: {exc}", file=sys.stderr)
        return 2

    print(f"Scoring {len(texts)} pool texts from {args.pool} "
          f"(pipeline={'on' if args.use_pipeline else 'off'})...")
    scored = score_pool(texts, model, vectorizer, args.use_pipeline)

    if args.stats:
        print_stats(scored, args.use_pipeline)
        return 0

    ranked = rank_rows(scored)
    write_queue(ranked[: max(args.top, 0)], Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
