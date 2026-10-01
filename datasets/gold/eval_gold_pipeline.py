"""
Evaluate gold dataset against the FULL pipeline (services.orchestrator.analyze_text()).
Not raw model.predict() — this runs every message through the complete analysis pipeline.

Headline metrics are computed on `refined_prediction` (the final, user-facing decision),
matching the Phase 1.5 backend baseline in MODEL_STATUS.md and the methodology of
frontend/scripts/eval-gold-js.mjs. The pre-refinement raw ML field (`prediction`) is
also reported under `raw_ml` for transparency.

Exit codes: 0 = ok, 1 = threshold regression, 2 = error.
"""
import argparse
import csv
import json
import sys
import os
from pathlib import Path
from collections import defaultdict

BACKEND_DIR = str(Path(__file__).resolve().parent.parent.parent / "backend")
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from services.orchestrator import analyze_text

GOLD_PATH = Path(__file__).parent / "gold_dataset.csv"
DEFAULT_JSON_PATH = Path(__file__).parent / "metrics.json"


def compute_metrics(pairs):
    tp = sum(1 for t, p in pairs if t == 1 and p == 1)
    fp = sum(1 for t, p in pairs if t == 0 and p == 1)
    fn = sum(1 for t, p in pairs if t == 1 and p == 0)
    tn = sum(1 for t, p in pairs if t == 0 and p == 0)
    n = len(pairs)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    acc = (tp + tn) / n if n else 0.0
    return {
        "accuracy": round(acc, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "fpr": round(fpr, 4),
        "fnr": round(fnr, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "n": n,
    }


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Full-pipeline gold evaluation")
    parser.add_argument("--dataset", default=str(GOLD_PATH), help="Path to gold CSV")
    parser.add_argument(
        "--json",
        nargs="?",
        const=str(DEFAULT_JSON_PATH),
        default=None,
        metavar="PATH",
        help="Write metrics.json (default path: datasets/gold/metrics.json)",
    )
    parser.add_argument("--min-accuracy", type=float, default=None,
                        help="Fail (exit 1) if accuracy falls below this value")
    parser.add_argument("--min-recall", type=float, default=None,
                        help="Fail (exit 1) if recall falls below this value")
    parser.add_argument("--max-fpr", type=float, default=None,
                        help="Fail (exit 1) if FPR rises above this value")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    gold_path = Path(args.dataset)
    if not gold_path.is_file():
        print(f"ERROR: dataset not found: {gold_path}", file=sys.stderr)
        return 2

    print("Loading gold dataset...")
    texts, labels, cats, langs = [], [], [], []
    with open(gold_path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            texts.append(r["text"])
            labels.append(1 if r["is_scam"].strip().lower() == "true" else 0)
            cats.append(r["category"])
            langs.append(r.get("language", "en"))

    print(f"Loaded {len(texts)} gold samples. Running full pipeline...")

    y_true = []
    y_pred = []
    y_pred_raw = []
    errors = []

    for i, (text, label, cat) in enumerate(zip(texts, labels, cats)):
        try:
            result = analyze_text(text)
            ml_pred = result.get("prediction", "safe")
            refined_pred = result.get("refined_prediction") or ml_pred
            pred = 1 if refined_pred == "scam" else 0
            raw = 1 if ml_pred == "scam" else 0
            y_true.append(label)
            y_pred.append(pred)
            y_pred_raw.append(raw)
            if pred != label:
                errors.append({
                    "text": text[:120],
                    "category": cat,
                    "true": "scam" if label == 1 else "safe",
                    "predicted": "scam" if pred == 1 else "safe",
                    "confidence": result.get("confidence", 0),
                    "risk_level": result.get("risk_level", "?"),
                })
        except Exception as e:
            y_true.append(label)
            y_pred.append(0)
            y_pred_raw.append(0)
            errors.append({
                "text": text[:120],
                "category": cat,
                "true": "scam" if label == 1 else "safe",
                "predicted": f"ERROR: {e}",
                "confidence": 0,
                "risk_level": "ERROR",
            })
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(texts)} done...")

    pairs = list(zip(y_true, y_pred))
    overall = compute_metrics(pairs)
    raw_overall = compute_metrics(list(zip(y_true, y_pred_raw)))
    tp, fp, fn, tn = overall["tp"], overall["fp"], overall["fn"], overall["tn"]
    precision = overall["precision"]
    recall = overall["recall"]
    f1 = overall["f1"]
    fpr = overall["fpr"]
    fnr = overall["fnr"]
    acc = overall["accuracy"]

    print(f"\n=== FULL PIPELINE GOLD EVALUATION ===")
    print(f"Date: 2026-08-30")
    print(f"Method: services.orchestrator.analyze_text() (full pipeline, not raw model)")
    print(f"Field: refined_prediction (raw ML prediction also reported below)")
    print(f"Samples: {len(y_true)}")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print(f"F1:        {f1:.4f}")
    print(f"FPR:       {fpr:.4f}")
    print(f"FNR:       {fnr:.4f}")
    print(f"Confusion: TP={tp} FP={fp} FN={fn} TN={tn}")
    print(f"\nRaw ML field (prediction, pre-refinement):")
    print(f"  Accuracy: {raw_overall['accuracy']:.4f} Precision: {raw_overall['precision']:.4f} "
          f"Recall: {raw_overall['recall']:.4f} FPR: {raw_overall['fpr']:.4f} "
          f"TP={raw_overall['tp']} FP={raw_overall['fp']} FN={raw_overall['fn']} TN={raw_overall['tn']}")

    cat_groups = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
    for t, p, c in zip(y_true, y_pred, cats):
        if t == 1 and p == 1:
            cat_groups[c]["tp"] += 1
        elif t == 0 and p == 1:
            cat_groups[c]["fp"] += 1
        elif t == 1 and p == 0:
            cat_groups[c]["fn"] += 1
        else:
            cat_groups[c]["tn"] += 1

    print(f"\nPer-category (scam categories with FPs or FNs):")
    for c in sorted(cat_groups):
        m = cat_groups[c]
        total = m["tp"] + m["fp"] + m["fn"] + m["tn"]
        if m["fp"] > 0 or m["fn"] > 0:
            print(f"  {c:35s} TP={m['tp']:3d} FP={m['fp']:3d} FN={m['fn']:3d} TN={m['tn']:3d} (n={total})")

    lang_groups = defaultdict(list)
    for t, p, la in zip(y_true, y_pred, langs):
        lang_groups[la].append((t, p))
    per_language = {la: compute_metrics(v) for la, v in sorted(lang_groups.items())}

    print(f"\nPer-language:")
    for la, m in per_language.items():
        print(f"  {la:8s} n={m['n']:3d} acc={m['accuracy']:.4f} prec={m['precision']:.4f} "
              f"rec={m['recall']:.4f} fpr={m['fpr']:.4f} "
              f"TP={m['tp']} FP={m['fp']} FN={m['fn']} TN={m['tn']}")

    print(f"\nTop false negatives (scam missed):")
    fns = [e for e in errors if e["true"] == "scam"]
    for e in fns[:10]:
        print(f"  [{e['category']}] conf={e['confidence']:.2f} risk={e['risk_level']}: {e['text'][:80]}")

    print(f"\nTop false positives (safe flagged as scam):")
    fps = [e for e in errors if e["true"] == "safe"]
    for e in fps[:10]:
        print(f"  [{e['category']}] conf={e['confidence']:.2f} risk={e['risk_level']}: {e['text'][:80]}")

    metrics_doc = {
        "dataset": str(gold_path),
        "samples": len(y_true),
        "field": "refined_prediction",
        "accuracy": overall["accuracy"],
        "precision": overall["precision"],
        "recall": overall["recall"],
        "f1": overall["f1"],
        "fpr": overall["fpr"],
        "fnr": overall["fnr"],
        "tp": overall["tp"],
        "fp": overall["fp"],
        "fn": overall["fn"],
        "tn": overall["tn"],
        "per_language": per_language,
        "raw_ml": raw_overall,
    }

    if args.json:
        out_path = Path(args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(metrics_doc, f, indent=2, ensure_ascii=False)
        print(f"\nMetrics written to {out_path}")

    failures = []
    if args.min_accuracy is not None and acc < args.min_accuracy:
        failures.append(f"accuracy {acc:.4f} < min_accuracy {args.min_accuracy:.4f}")
    if args.min_recall is not None and recall < args.min_recall:
        failures.append(f"recall {recall:.4f} < min_recall {args.min_recall:.4f}")
    if args.max_fpr is not None and fpr > args.max_fpr:
        failures.append(f"fpr {fpr:.4f} > max_fpr {args.max_fpr:.4f}")
    if failures:
        print("\nTHRESHOLD FAILURE:")
        for msg in failures:
            print(f"  {msg}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
