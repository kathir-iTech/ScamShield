"""Python side of pipeline comparison: reads js_results.json, runs Python pipeline, compares risk_level."""
import sys
import os
import json
import time
import csv

# Setup paths
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from services.orchestrator import analyze_text

EXPERIMENTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
JS_RESULTS_PATH = os.path.join(EXPERIMENTS_DIR, 'js_results.json')
GOLD_CSV = os.path.join(os.path.dirname(EXPERIMENTS_DIR), 'datasets', 'gold', 'gold_dataset.csv')

# Load JS results
with open(JS_RESULTS_PATH, 'r') as f:
    js_results = json.load(f)

print(f"Loaded {len(js_results)} JS results")
print(f"Running Python pipeline on all messages...\n")

python_results = []
start = time.time()

for i, js_r in enumerate(js_results):
    text = js_r['text']
    result = analyze_text(text)
    python_results.append({
        'id': js_r['id'],
        'text': text,
        'category': js_r['category'],
        'is_scam': js_r['is_scam'],
        'gold_label': js_r['gold_label'],
        'gold_risk': js_r['gold_risk'],
        'js_risk_level': js_r['js_risk_level'],
        'js_prediction': js_r['js_prediction'],
        'js_refined_prediction': js_r['js_refined_prediction'],
        'js_confidence': js_r['js_confidence'],
        'js_rule_score': js_r['js_rule_score'],
        'js_assessment_score': js_r['js_assessment_score'],
        'js_refined_assessment_score': js_r['js_refined_assessment_score'],
        'py_risk_level': result.get('risk_level', 'UNKNOWN'),
        'py_prediction': result.get('prediction', 'UNKNOWN'),
        'py_refined_prediction': result.get('refined_prediction', 'UNKNOWN'),
        'py_confidence': result.get('confidence', 0),
        'py_rule_score': result.get('rule_score', 0),
        'py_assessment_score': result.get('assessment_score', 0),
        'py_refined_assessment_score': result.get('refined_assessment_score', 0),
    })
    if (i + 1) % 50 == 0:
        elapsed = time.time() - start
        rate = (i + 1) / elapsed
        print(f"  [{i + 1}/{len(js_results)}] {rate:.1f} msg/sec, ETA {((len(js_results) - i - 1) / rate):.0f}s")

elapsed = time.time() - start
print(f"\nPython pipeline completed in {elapsed:.1f}s ({elapsed / len(js_results) * 1000:.0f}ms avg)")

# === ANALYSIS ===
print("\n" + "=" * 80)
print("COMPARISON RESULTS: risk_level (JS vs Python)")
print("=" * 80)

total = len(python_results)
exact_match = sum(1 for r in python_results if r['js_risk_level'] == r['py_risk_level'])
pred_match = sum(1 for r in python_results if r['js_prediction'] == r['py_prediction'])
refined_match = sum(1 for r in python_results if r['js_refined_prediction'] == r['py_refined_prediction'])

print(f"\nTotal messages:     {total}")
print(f"risk_level match:   {exact_match}/{total} ({exact_match / total * 100:.1f}%)")
print(f"prediction match:   {pred_match}/{total} ({pred_match / total * 100:.1f}%)")
print(f"refined_pred match: {refined_match}/{total} ({refined_match / total * 100:.1f}%)")

# Score differences
score_diffs = [abs(r['js_assessment_score'] - r['py_assessment_score']) for r in python_results]
refined_diffs = [abs(r['js_refined_assessment_score'] - r['py_refined_assessment_score']) for r in python_results]
conf_diffs = [abs(r['js_confidence'] - r['py_confidence']) for r in python_results]
rule_diffs = [abs(r['js_rule_score'] - r['py_rule_score']) for r in python_results]

print(f"\nScore differences (JS vs Python):")
print(f"  assessment_score:     avg={sum(score_diffs) / total:.3f}, max={max(score_diffs)}, zero_count={sum(1 for d in score_diffs if d == 0)}")
print(f"  refined_assessment:   avg={sum(refined_diffs) / total:.3f}, max={max(refined_diffs)}, zero_count={sum(1 for d in refined_diffs if d == 0)}")
print(f"  confidence:           avg={sum(conf_diffs) / total:.6f}, max={max(conf_diffs):.6f}, zero_count={sum(1 for d in conf_diffs if d == 0)}")
print(f"  rule_score:           avg={sum(rule_diffs) / total:.3f}, max={max(rule_diffs)}, zero_count={sum(1 for d in rule_diffs if d == 0)}")

# Mismatch analysis
mismatches = [r for r in python_results if r['js_risk_level'] != r['py_risk_level']]
if mismatches:
    print(f"\n{'=' * 80}")
    print(f"MISMATCHES: {len(mismatches)} messages with different risk_level")
    print(f"{'=' * 80}")
    for j, r in enumerate(mismatches):
        print(f"\n--- Mismatch #{j + 1} ---")
        print(f"  ID:       {r['id']}")
        print(f"  Category: {r['category']}")
        print(f"  Text:     {r['text'][:120]}{'...' if len(r['text']) > 120 else ''}")
        print(f"  Gold:     {r['gold_risk']} (label: {r['gold_label']})")
        print(f"  JS:       {r['js_risk_level']} (pred={r['js_prediction']}, refined={r['js_refined_prediction']}, ml_conf={r['js_confidence']:.4f}, rule={r['js_rule_score']}, assess={r['js_assessment_score']}, refined_assess={r['js_refined_assessment_score']})")
        print(f"  Python:   {r['py_risk_level']} (pred={r['py_prediction']}, refined={r['py_refined_prediction']}, ml_conf={r['py_confidence']:.4f}, rule={r['py_rule_score']}, assess={r['py_assessment_score']}, refined_assess={r['py_refined_assessment_score']})")
else:
    print(f"\n*** EXACT MATCH on all {total} messages! ***")

# Mismatch by category
if mismatches:
    print(f"\n{'=' * 80}")
    print("MISMATCHES BY CATEGORY")
    print(f"{'=' * 80}")
    cat_counts = {}
    for r in mismatches:
        cat = r['category']
        if cat not in cat_counts:
            cat_counts[cat] = {'total': 0, 'mismatches': []}
        cat_counts[cat]['total'] += 1
        cat_counts[cat]['mismatches'].append(r)
    
    for cat, data in sorted(cat_counts.items()):
        print(f"\n  {cat}: {data['total']} mismatch(es)")
        for r in data['mismatches']:
            print(f"    JS={r['js_risk_level']}, Py={r['py_risk_level']} — {r['text'][:80]}...")

# Prediction mismatches (separate from risk_level)
pred_mismatches = [r for r in python_results if r['js_prediction'] != r['py_prediction']]
if pred_mismatches:
    print(f"\n{'=' * 80}")
    print(f"PREDICTION MISMATCHES: {len(pred_mismatches)} messages")
    print(f"{'=' * 80}")
    for j, r in enumerate(pred_mismatches):
        print(f"\n--- Pred Mismatch #{j + 1} ---")
        print(f"  ID:       {r['id']}")
        print(f"  Category: {r['category']}")
        print(f"  Text:     {r['text'][:120]}{'...' if len(r['text']) > 120 else ''}")
        print(f"  Gold:     {r['gold_label']}")
        print(f"  JS:       pred={r['js_prediction']} (conf={r['js_confidence']:.4f})")
        print(f"  Python:   pred={r['py_prediction']} (conf={r['py_confidence']:.4f})")

# Full JSON results
results_path = os.path.join(EXPERIMENTS_DIR, 'comparison_results.json')
with open(results_path, 'w') as f:
    json.dump(python_results, f, indent=1)
print(f"\nFull results written to {results_path}")
