// JS-side gold-set evaluation for the frontend pipeline.js
// Runs the SAME methodology as datasets/gold/eval_gold_pipeline.py but against
// the JS pipeline: uses analyzeText().refined_prediction ("safe"/"scam") as
// binary output — this is the final, user-facing decision, not the pre-refinement
// raw ML prediction.
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { analyzeText } from '../src/lib/scamshield/pipeline.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const GOLD_PATH = join(__dirname, '..', '..', 'datasets', 'gold', 'gold_dataset.csv');

// Minimal CSV parser that handles quoted fields
function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else inQuotes = false;
      } else field += c;
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === ',') {
      row.push(field); field = '';
    } else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(field); field = '';
      if (row.some((f) => f.trim() !== '')) rows.push(row);
      row = [];
    } else field += c;
  }
  row.push(field);
  if (row.some((f) => f.trim() !== '')) rows.push(row);
  return rows;
}

const raw = readFileSync(GOLD_PATH, 'utf8');
const rows = parseCsv(raw);
const header = rows[0];
const idx = Object.fromEntries(header.map((h, i) => [h, i]));
const dataRows = rows.slice(1);

const results = [];
for (const r of dataRows) {
  const text = r[idx['text']];
  const label = r[idx['is_scam']].trim().toLowerCase() === 'true' ? 1 : 0;
  const cat = r[idx['category']];
  const result = analyzeText(text);
  const pred = result.refined_prediction === 'scam' ? 1 : 0;
  results.push({ text, label, pred, cat, confidence: result.confidence, risk: result.risk_level,
                 threats: result.threats, indicators: result.detected_indicators });
}

let tp = 0, fp = 0, fn = 0, tn = 0;
for (const { label, pred } of results) {
  if (label === 1 && pred === 1) tp++;
  else if (label === 0 && pred === 1) fp++;
  else if (label === 1 && pred === 0) fn++;
  else tn++;
}

const precision = tp / (tp + fp) || 0;
const recall = tp / (tp + fn) || 0;
const f1 = 2 * precision * recall / (precision + recall) || 0;
const fpr = fp / (fp + tn) || 0;
const fnr = fn / (fn + tp) || 0;
const acc = (tp + tn) / results.length;

console.log('=== JS PIPELINE GOLD EVALUATION ===');
console.log('Samples:', results.length);
console.log('Accuracy: ', acc.toFixed(4));
console.log('Precision:', precision.toFixed(4));
console.log('Recall:   ', recall.toFixed(4));
console.log('F1:       ', f1.toFixed(4));
console.log('FPR:      ', fpr.toFixed(4));
console.log('FNR:      ', fnr.toFixed(4));
console.log('Confusion: TP=' + tp + ' FP=' + fp + ' FN=' + fn + ' TN=' + tn);

console.log('\nTop false negatives (scam missed):');
for (const r of results.filter((r) => r.label === 1 && r.pred === 0).slice(0, 10)) {
  console.log('  [' + r.cat + '] conf=' + r.confidence.toFixed(2) + ' risk=' + r.risk + ': ' + r.text.slice(0, 75));
}
console.log('\nTop false positives (safe flagged as scam):');
for (const r of results.filter((r) => r.label === 0 && r.pred === 1).slice(0, 10)) {
  console.log('  [' + r.cat + '] conf=' + r.confidence.toFixed(2) + ' risk=' + r.risk + ': ' + r.text.slice(0, 75));
}
