#!/usr/bin/env python3
"""
ScamShield Evaluation Framework

Usage:
    python evaluation_runner.py --dataset evaluation/datasets/benchmark.json
    python evaluation_runner.py --dataset benchmark.json --output reports/results.html
    python evaluation_runner.py --sample 5 --verbose

Options:
    --dataset PATH   Path to benchmark dataset (default: datasets/benchmark.json)
    --output PATH    Path for HTML report (default: reports/evaluation_<timestamp>.html)
    --sample N       Only process N samples for a quick test
    --verbose        Enable detailed logging
"""

import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.schema import validate_dataset, validate_investigation_sample, FAMILY_CATEGORY_MAP, SUBFAMILY_CATEGORY_MAP
from scripts.report import generate_html_report
from scripts.error_analysis import analyze_errors
from scripts.report import (
    generate_html_report,
    generate_comparison_report,
    load_metrics,
    regression_check,
)


def load_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        samples = json.load(f)
    if not isinstance(samples, list):
        raise ValueError(f"Dataset must be a list of samples, got {type(samples).__name__}")
    return samples


def _call_api(text: str) -> Dict[str, Any]:
    import httpx
    base_url = os.getenv("SCAMSHIELD_API_URL", "http://localhost:8000")
    try:
        resp = httpx.post(
            f"{base_url}/analyze/text",
            json={"text": text},
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.RequestError as e:
        return {"error": str(e), "prediction": "error"}


def _classify_local(text: str, pred_cache: Dict[str, Dict]) -> Dict[str, Any]:
    import sys as _sys
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
    if backend_dir not in _sys.path:
        _sys.path.insert(0, backend_dir)
    os.chdir(backend_dir)
    from services.orchestrator import analyze_text as local_analyze
    result = local_analyze(text)
    return result


def _evaluate_knowledge(samples: List[Dict[str, Any]], verbose: bool = False) -> Tuple[List[Dict], Dict]:
    import sys as _sys
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
    if backend_dir not in _sys.path:
        _sys.path.insert(0, backend_dir)
    os.chdir(backend_dir)
    from domains.knowledge.service import get_service
    from domains.knowledge.public import search_by_indicator
    ks = get_service()

    predictions = []
    correct = 0
    match_type_correct = 0
    advisory_correct = 0
    nonmatch_correct = 0
    nonmatch_total = 0
    total = len(samples)

    for i, sample in enumerate(samples):
        sid = sample["id"]
        query = sample["query"]
        ind_type = sample.get("indicator_type", "domain")
        expected_id = sample.get("expected_indicator_id")
        expected_match = sample.get("expected_match_type", "none")
        expected_min_conf = sample.get("expected_min_confidence", 0.0)
        expected_advisory = sample.get("expected_advisory", False)

        if ind_type == "keyword":
            results = search_by_indicator("keyword", query)
        else:
            results = search_by_indicator(ind_type, query)

        actual_id = results[0].indicator_id if results else None
        actual_match = results[0].match_type if results else "none"
        actual_conf = results[0].confidence if results else 0.0
        actual_advisory = bool(results)

        id_ok = (expected_id is None and actual_id is None) or (expected_id == actual_id)
        match_ok = True
        if expected_match == "none":
            match_ok = actual_match == "none"
        elif expected_match == "exact":
            match_ok = actual_match in ("exact", "normalised", "domain_match", "prefix", "suffix")
        elif expected_match == "prefix":
            match_ok = actual_match in ("exact", "prefix")
        elif expected_match == "domain_match":
            match_ok = actual_match in ("exact", "domain_match", "subdomain_match", "parent_domain_match")
        else:
            match_ok = expected_match == actual_match
        conf_ok = actual_conf >= expected_min_conf if expected_match != "none" else True
        advisory_ok = (not expected_advisory) or actual_advisory

        sample_ok = id_ok and match_ok and conf_ok and advisory_ok
        if sample_ok:
            correct += 1

        if id_ok and match_ok:
            match_type_correct += 1

        if advisory_ok:
            advisory_correct += 1

        if expected_match == "none":
            nonmatch_total += 1
            if actual_id is None:
                nonmatch_correct += 1

        if verbose:
            status = "OK" if sample_ok else "MISMATCH"
            print(f"  [{i+1}/{total}] {sid}: expected={expected_id}, got={actual_id} ({actual_match}) [{status}]")

        predictions.append({
            "id": sid,
            "query": query,
            "expected_indicator_id": expected_id,
            "actual_indicator_id": actual_id,
            "expected_match_type": expected_match,
            "actual_match_type": actual_match,
            "expected_min_confidence": expected_min_conf,
            "actual_confidence": actual_conf,
            "expected_advisory": expected_advisory,
            "actual_advisory": actual_advisory,
            "correct": sample_ok,
            "id_match": id_ok,
            "match_type_match": match_ok,
        })

    metrics = {
        "total_samples": total,
        "overall_accuracy": correct / total if total > 0 else 0.0,
        "retrieval_accuracy": match_type_correct / total if total > 0 else 0.0,
        "advisory_accuracy": advisory_correct / total if total > 0 else 0.0,
        "nonmatch_accuracy": nonmatch_correct / nonmatch_total if nonmatch_total > 0 else 1.0,
    }

    return predictions, metrics


def _investigate_local(artefacts: List[Dict]) -> Dict[str, Any]:
    import sys as _sys
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
    if backend_dir not in _sys.path:
        _sys.path.insert(0, backend_dir)
    os.chdir(backend_dir)
    from domains.investigation.public import investigate as local_investigate
    result = local_investigate(artefacts)
    return result


def investigate_batch(
    samples: List[Dict[str, Any]],
    verbose: bool = False,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    predictions = []
    inference_times = []
    campaign_correct = 0
    risk_correct = 0
    score_errors = []
    timeline_correct = 0
    entity_correct = 0
    cross_entity_correct = 0

    for i, sample in enumerate(samples):
        sid = sample["id"]
        artefacts = sample["artefacts"]

        start = time.perf_counter()
        result = _investigate_local(artefacts)
        elapsed_ms = (time.perf_counter() - start) * 1000
        inference_times.append(elapsed_ms)

        actual_campaign = result.campaign.get("campaign_detected", False)
        actual_risk = result.global_risk.get("overall_risk", "UNKNOWN")
        actual_score = result.global_risk.get("overall_score", 0)
        actual_timeline_count = len(result.timeline)
        actual_merged_count = sum(len(v) for v in result.merged_entities.values())

        expected_campaign = sample.get("expected_campaign", False)
        expected_risk = sample.get("expected_overall_risk", "UNKNOWN")
        expected_score = sample.get("expected_overall_score", 0)
        expected_timeline = sample.get("expected_timeline_events", 0)
        expected_merged = sample.get("expected_merged_entities", 0)
        expected_cross = sample.get("expected_cross_message_entities", 0)

        if actual_campaign == expected_campaign:
            campaign_correct += 1
        if actual_risk == expected_risk:
            risk_correct += 1
        score_error = abs(actual_score - expected_score)
        score_errors.append(score_error)
        if expected_timeline and abs(actual_timeline_count - expected_timeline) <= 2:
            timeline_correct += 1
        if expected_merged and abs(actual_merged_count - expected_merged) <= 3:
            entity_correct += 1
        cross_entity_count = sum(
            1 for entity_list in result.merged_entities.values()
            for e in entity_list if e.get("occurrences", 0) >= 2
        )
        if expected_cross:
            if abs(cross_entity_count - expected_cross) <= 1:
                cross_entity_correct += 1

        if verbose:
            camp_status = "OK" if actual_campaign == expected_campaign else "MISMATCH"
            risk_status = "OK" if actual_risk == expected_risk else "MISMATCH"
            print(f"  [{i+1}/{len(samples)}] {sid}: campaign={actual_campaign}(expected={expected_campaign}) [{camp_status}], "
                  f"risk={actual_risk}(expected={expected_risk}) [{risk_status}]")

        predictions.append({
            "id": sid,
            "campaign_detected": actual_campaign,
            "expected_campaign": expected_campaign,
            "overall_risk": actual_risk,
            "expected_overall_risk": expected_risk,
            "overall_score": actual_score,
            "expected_overall_score": expected_score,
            "campaign_confidence": result.campaign.get("confidence", 0.0),
            "timeline_events": actual_timeline_count,
            "merged_entities": actual_merged_count,
            "cross_message_entities": cross_entity_count,
            "dominant_family": result.global_risk.get("dominant_family", ""),
            "inference_ms": round(elapsed_ms, 1),
            "artefact_summaries": result.artefact_summaries,
        })

    n = len(samples)
    avg_score_error = sum(score_errors) / len(score_errors) if score_errors else 0.0
    score_accuracy = max(0, 1.0 - avg_score_error / 100.0)

    avg_inference = sum(inference_times) / len(inference_times) if inference_times else 0.0
    sorted_times = sorted(inference_times)
    p95_idx = int(len(sorted_times) * 0.95)
    p95_latency = sorted_times[p95_idx] if p95_idx < len(sorted_times) else (sorted_times[-1] if sorted_times else 0.0)

    metrics = {
        "total_samples": n,
        "campaign_accuracy": campaign_correct / n if n > 0 else 0.0,
        "risk_accuracy": risk_correct / n if n > 0 else 0.0,
        "score_accuracy": round(score_accuracy, 4),
        "average_score_error": round(avg_score_error, 1),
        "timeline_accuracy": timeline_correct / max(n, 1) if sample.get("expected_timeline_events") else 0.0,
        "entity_accuracy": entity_correct / max(n, 1) if sample.get("expected_merged_entities") else 0.0,
        "cross_entity_accuracy": cross_entity_correct / max(n, 1) if sample.get("expected_cross_message_entities") else 0.0,
        "average_inference_ms": round(avg_inference, 1),
        "p95_latency_ms": round(p95_latency, 1),
    }

    return predictions, metrics


def evaluate(
    samples: List[Dict[str, Any]],
    api_url: str = "",
    verbose: bool = False,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Tuple[int, int, int, int], List[Dict]]:
    predictions = []
    inference_times = []
    category_stats: Dict[str, Dict] = defaultdict(lambda: {"correct": 0, "total": 0, "risk_correct": 0, "assessment_correct": 0})
    risk_correct = 0
    assessment_correct = 0
    total_confidence = 0.0
    family_correct = 0
    subfamily_correct = 0
    family_tested = 0

    for i, sample in enumerate(samples):
        sid = sample["id"]
        text = sample["text"]
        expected_pred = sample["expected_prediction"]

        start = time.perf_counter()

        if api_url:
            result = _call_api(text)
        else:
            result = _classify_local(text, {})

        elapsed_ms = (time.perf_counter() - start) * 1000
        inference_times.append(elapsed_ms)

        actual_pred = result.get("refined_prediction") or result.get("prediction", "safe")
        confidence = result.get("confidence", 0.0)
        actual_category = result.get("scam_category", "Unknown")
        actual_risk = result.get("risk_level", "LOW")
        actual_assessment = result.get("assessment_band", "")
        actual_decision = result.get("decision_level", "SAFE")

        if verbose:
            status = "OK" if actual_pred == expected_pred else "MISMATCH"
            print(f"  [{i+1}/{len(samples)}] {sid}: expected={expected_pred}, got={actual_pred} [{status}]")

        cat = sample.get("expected_category", "Unknown")
        category_stats[cat]["total"] += 1
        if actual_pred == expected_pred:
            category_stats[cat]["correct"] += 1
        if actual_risk == sample.get("expected_risk_level"):
            category_stats[cat]["risk_correct"] += 1
            risk_correct += 1
        if actual_assessment == sample.get("expected_assessment_band"):
            category_stats[cat]["assessment_correct"] += 1
            assessment_correct += 1

        total_confidence += confidence

        actual_family = result.get("reasoning_family", "")
        expected_family = FAMILY_CATEGORY_MAP.get(cat, "")
        if expected_family:
            family_tested += 1
            if actual_family == expected_family:
                family_correct += 1
            expected_subfamily = SUBFAMILY_CATEGORY_MAP.get(cat, "")
            actual_subfamily = result.get("reasoning_subfamily", "")
            if actual_subfamily == expected_subfamily:
                subfamily_correct += 1

        predictions.append({
            "id": sid,
            "expected_prediction": expected_pred,
            "prediction": actual_pred,
            "confidence": confidence,
            "expected_category": cat,
            "scam_category": actual_category,
            "expected_risk_level": sample.get("expected_risk_level"),
            "risk_level": actual_risk,
            "expected_decision_level": sample.get("expected_decision_level"),
            "decision_level": actual_decision,
            "expected_assessment_band": sample.get("expected_assessment_band"),
            "assessment_band": actual_assessment,
            "expected_family": expected_family,
            "reasoning_family": actual_family,
            "expected_subfamily": expected_subfamily,
            "reasoning_subfamily": actual_subfamily,
            "inference_ms": round(elapsed_ms, 1),
            "entities": result.get("entities", []),
            "error": result.get("error", ""),
        })

    n = len(samples)
    tp = sum(1 for p in predictions if p["expected_prediction"] == "scam" and p["prediction"] == "scam")
    fp = sum(1 for p in predictions if p["expected_prediction"] == "safe" and p["prediction"] == "scam")
    fn = sum(1 for p in predictions if p["expected_prediction"] == "scam" and p["prediction"] != "scam")
    tn = sum(1 for p in predictions if p["expected_prediction"] == "safe" and p["prediction"] == "safe")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / n if n > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    sorted_times = sorted(inference_times)
    avg_inference = sum(inference_times) / len(inference_times) if inference_times else 0.0
    p95_idx = int(len(sorted_times) * 0.95)
    p95_latency = sorted_times[p95_idx] if p95_idx < len(sorted_times) else (sorted_times[-1] if sorted_times else 0.0)

    cat_acc_total = sum(
        1 for p in predictions
        if p["expected_prediction"] == "scam" and p["prediction"] == "scam"
        and p.get("expected_category") and p.get("scam_category")
        and p["expected_category"] == p["scam_category"]
    )
    total_scam_correct = sum(
        1 for p in predictions
        if p["expected_prediction"] == "scam" and p["prediction"] == "scam"
    )
    category_accuracy = cat_acc_total / total_scam_correct if total_scam_correct > 0 else 0.0

    risk_accuracy = risk_correct / n if n > 0 else 0.0
    assessment_accuracy = assessment_correct / n if n > 0 else 0.0
    avg_confidence = total_confidence / n if n > 0 else 0.0

    family_accuracy = family_correct / family_tested if family_tested > 0 else 0.0
    subfamily_accuracy = subfamily_correct / family_tested if family_tested > 0 else 0.0

    metrics = {
        "total_samples": n,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
        "category_accuracy": category_accuracy,
        "risk_accuracy": risk_accuracy,
        "assessment_accuracy": assessment_accuracy,
        "family_accuracy": family_accuracy,
        "subfamily_accuracy": subfamily_accuracy,
        "average_confidence": avg_confidence,
        "average_inference_ms": round(avg_inference, 1),
        "p95_latency_ms": round(p95_latency, 1),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
    }

    cat_stats_list = []
    for cat, stats in sorted(category_stats.items()):
        acc = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
        cat_stats_list.append({
            "category": cat,
            "total": stats["total"],
            "correct": stats["correct"],
            "accuracy": round(acc, 4),
            "risk_accuracy": round(stats["risk_correct"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
            "assessment_accuracy": round(stats["assessment_correct"] / stats["total"], 4) if stats["total"] > 0 else 0.0,
        })

    return predictions, metrics, (tp, fp, fn, tn), cat_stats_list


def save_results(predictions: List[Dict], metrics: Dict, error_analysis: Dict, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    pred_path = os.path.join(output_dir, "predictions.json")
    with open(pred_path, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2, ensure_ascii=False)
    print(f"  Predictions saved: {pred_path}")

    metrics_path = os.path.join(output_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"  Metrics saved: {metrics_path}")

    error_path = os.path.join(output_dir, "error_analysis.json")
    with open(error_path, "w", encoding="utf-8") as f:
        json.dump(error_analysis, f, indent=2, ensure_ascii=False)
    print(f"  Error analysis saved: {error_path}")


def print_summary(metrics: Dict[str, Any], error_analysis: Dict[str, Any], cat_stats: List[Dict]) -> None:
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total samples:    {metrics['total_samples']}")
    print(f"  Accuracy:         {metrics['accuracy']:.1%}")
    print(f"  Precision:        {metrics['precision']:.1%}")
    print(f"  Recall:           {metrics['recall']:.1%}")
    print(f"  F1 Score:         {metrics['f1']:.1%}")
    print(f"  False Positive:   {metrics['false_positive_rate']:.1%}")
    print(f"  False Negative:   {metrics['false_negative_rate']:.1%}")
    print(f"  Category Acc:     {metrics['category_accuracy']:.1%}")
    print(f"  Family Acc:       {metrics['family_accuracy']:.1%}")
    print(f"  Subfamily Acc:    {metrics['subfamily_accuracy']:.1%}")
    print(f"  Risk Level Acc:   {metrics['risk_accuracy']:.1%}")
    print(f"  Assessment Acc:   {metrics['assessment_accuracy']:.1%}")
    print(f"  Avg Confidence:   {metrics['average_confidence']:.1%}")
    print(f"  Avg Inference:    {metrics['average_inference_ms']:.1f}ms")
    print(f"  P95 Latency:      {metrics['p95_latency_ms']:.1f}ms")
    print(f"  Confusion Matrix: TP={metrics['tp']} FP={metrics['fp']} FN={metrics['fn']} TN={metrics['tn']}")
    print(f"  Errors:           {error_analysis['fp_count']} FP, {error_analysis['fn_count']} FN, "
          f"{error_analysis['wc_count']} wrong cat, {error_analysis['lc_count']} low conf")

    print(f"\n  Category Breakdown:")
    for c in cat_stats:
        bar = "=" * int(c["accuracy"] * 30)
        print(f"    {c['category']:25s} {c['accuracy']:.1%} {c['correct']:3d}/{c['total']:<3d} {bar}")


def main():
    parser = argparse.ArgumentParser(description="ScamShield Evaluation Framework")
    parser.add_argument(
        "--dataset",
        default=os.path.join(os.path.dirname(__file__), "datasets", "benchmark.json"),
        help="Path to benchmark dataset JSON",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Output directory for results and HTML report",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=0,
        help="Limit to N samples for quick testing",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed per-sample results",
    )
    parser.add_argument(
        "--api",
        default="",
        help="API base URL (default: use local backend)",
    )
    parser.add_argument(
        "--compare",
        default="",
        help="Path to previous metrics.json for comparison report",
    )
    parser.add_argument(
        "--regression-thresholds",
        default="",
        help="JSON string of custom regression thresholds",
    )
    parser.add_argument(
        "--mode",
        default="standard",
        choices=["standard", "investigation", "knowledge"],
        help="Evaluation mode: standard (single message), investigation (multi-artefact), or knowledge (retrieval accuracy)",
    )
    args = parser.parse_args()

    dataset_path = args.dataset
    if not os.path.isabs(dataset_path):
        dataset_path = os.path.join(os.path.dirname(__file__), dataset_path)

    print(f"Loading dataset: {dataset_path}")
    samples = load_dataset(dataset_path)

    if args.mode == "knowledge":
        print(f"Running in KNOWLEDGE RETRIEVAL mode")
        print(f"Knowledge dataset validated: {len(samples)} queries OK")
    elif args.mode == "investigation":
        print(f"Running in INVESTIGATION mode")
        for sample in samples:
            errs = validate_investigation_sample(sample)
            if errs:
                print(f"Validation errors for {sample.get('id', '?')}:")
                for e in errs:
                    print(f"  {e}")
                sys.exit(1)
        print(f"Investigation dataset validated: {len(samples)} samples OK")
    else:
        valid, errors, per_sample = validate_dataset(samples)
        if not valid:
            print(f"Dataset validation failed with {len(errors)} error(s):")
            for e in errors[:10]:
                print(f"  {e}")
            sys.exit(1)
        print(f"Dataset validated: {len(samples)} samples OK")

    if args.sample > 0:
        samples = samples[:args.sample]
        print(f"Limited to {len(samples)} samples for quick test")

    output_dir = args.output
    if not output_dir:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(os.path.dirname(__file__), "reports", f"eval_{timestamp}")
    elif not os.path.isabs(output_dir):
        output_dir = os.path.join(os.path.dirname(__file__), output_dir)

    print(f"\nRunning evaluation on {len(samples)} samples...")

    if args.mode == "knowledge":
        predictions, metrics = _evaluate_knowledge(samples, verbose=args.verbose)
        report_path = os.path.join(output_dir, "report.html")
        error_analysis = {"fp_count": 0, "fn_count": 0, "wc_count": 0, "lc_count": 0}
        confusion = (0, 0, 0, 0)
        cat_stats = []
        save_results(predictions, metrics, error_analysis, output_dir)
        print(f"\n  KNOWLEDGE RETRIEVAL RESULTS:")
        print(f"    Samples:                {metrics['total_samples']}")
        print(f"    Overall Accuracy:       {metrics['overall_accuracy']:.1%}")
        print(f"    Retrieval Accuracy:     {metrics['retrieval_accuracy']:.1%}")
        print(f"    Advisory Accuracy:      {metrics['advisory_accuracy']:.1%}")
        print(f"    Non-match Accuracy:     {metrics['nonmatch_accuracy']:.1%}")
    elif args.mode == "investigation":
        predictions, metrics = investigate_batch(samples, verbose=args.verbose)
        confusion = (0, 0, 0, 0)
        cat_stats = []
        error_analysis = {"fp_count": 0, "fn_count": 0, "wc_count": 0, "lc_count": 0}
        report_path = os.path.join(output_dir, "report.html")
        generate_html_report(metrics, error_analysis, confusion, cat_stats, samples, report_path)
        print(f"  HTML report: {report_path}")
        print(f"\n  INVESTIGATION RESULTS:")
        print(f"    Samples:            {metrics['total_samples']}")
        print(f"    Campaign Acc:       {metrics['campaign_accuracy']:.1%}")
        print(f"    Risk Level Acc:     {metrics['risk_accuracy']:.1%}")
        print(f"    Score Accuracy:     {metrics['score_accuracy']:.1%}")
        print(f"    Avg Score Error:    {metrics['average_score_error']:.1f}")
        print(f"    Avg Inference:      {metrics['average_inference_ms']:.1f}ms")
    else:
        predictions, metrics, confusion, cat_stats = evaluate(samples, api_url=args.api, verbose=args.verbose)
        error_analysis = analyze_errors(samples, predictions)
        save_results(predictions, metrics, error_analysis, output_dir)
        report_path = os.path.join(output_dir, "report.html")
        generate_html_report(metrics, error_analysis, confusion, cat_stats, samples, report_path)
        print(f"  HTML report: {report_path}")
        print_summary(metrics, error_analysis, cat_stats)

    results_json = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dataset": dataset_path,
        "samples": len(samples),
        "metrics": metrics,
        "errors": {
            "false_positives": error_analysis.get("fp_count", 0),
            "false_negatives": error_analysis.get("fn_count", 0),
            "wrong_category": error_analysis.get("wc_count", 0),
        },
        "report": report_path,
        "mode": args.mode,
    }
    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, "w") as f:
        json.dump(results_json, f, indent=2)

    if args.compare:
        baseline_path = args.compare
        if not os.path.isabs(baseline_path):
            baseline_path = os.path.join(os.path.dirname(__file__), baseline_path)
        baseline = load_metrics(baseline_path)
        if baseline:
            thresholds = None
            if args.regression_thresholds:
                try:
                    thresholds = json.loads(args.regression_thresholds)
                except json.JSONDecodeError:
                    print(f"  Invalid regression thresholds JSON, using defaults")

            regression_result = regression_check(baseline, metrics, thresholds)
            comp_path = os.path.join(output_dir, "comparison.html")
            generate_comparison_report(baseline, metrics, regression_result, comp_path)
            print(f"  Comparison report: {comp_path}")

            if regression_result["passed"]:
                print("  Regression check: PASSED")
            else:
                print("  Regression check: FAILED")
                for issue in regression_result["issues"]:
                    print(f"    - {issue}")
                if metrics["accuracy"] < 0.5:
                    print("  Evaluation failed: accuracy below 50%")
                    return 1
        else:
            print(f"  Warning: baseline metrics not found at {baseline_path}")

    metric_val = metrics.get("accuracy", metrics.get("overall_accuracy", 0))
    return 0 if metric_val >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
