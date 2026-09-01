import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, '..', '..');

// Import frontend's pipeline (ESM)
import { analyzeText } from '../src/lib/scamshield/pipeline.js';

function parseCSV(text) {
  const rows = [];
  let current = '';
  let inQuotes = false;
  let cells = [];
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    const isQuote = c === '"';
    if (isQuote) {
      if (inQuotes && i + 1 < text.length && text[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (c === ',' && !inQuotes) {
      cells.push(current);
      current = '';
      continue;
    }
    if (c === '\n' && !inQuotes) {
      cells.push(current);
      rows.push(cells);
      cells = [];
      current = '';
      continue;
    }
    if (c === '\r' && !inQuotes) continue;
    current += c;
  }
  if (current.length > 0 || cells.length > 0) {
    cells.push(current);
    rows.push(cells);
  }
  return rows;
}

const csvPath = path.join(root, 'datasets', 'gold', 'gold_dataset.csv');
const csvText = fs.readFileSync(csvPath, 'utf-8');
const rows = parseCSV(csvText);
const header = rows[0];
const colIdx = {};
header.forEach((h, i) => { colIdx[h.trim()] = i; });
const textIdx = colIdx['text'];
const idIdx = colIdx['id'];
const categoryIdx = colIdx['category'];
const isScamIdx = colIdx['is_scam'];
const groundTruthIdx = colIdx['ground_truth_label'];
const goldRiskIdx = colIdx['risk_level'];

const messages = [];
for (let i = 1; i < rows.length; i++) {
  const fields = rows[i];
  if (fields.length <= textIdx) continue;
  const text = fields[textIdx];
  if (!text || text.trim() === '') continue;
  messages.push({
    id: fields[idIdx],
    text,
    category: fields[categoryIdx],
    is_scam: fields[isScamIdx],
    gold_label: fields[groundTruthIdx],
    gold_risk: fields[goldRiskIdx],
  });
}

console.log(`Loaded ${messages.length} messages from gold dataset (expected 308)`);
console.log(`Running FRONTEND pipeline on all messages...`);

const startTime = Date.now();
const results = [];
for (let i = 0; i < messages.length; i++) {
  const msg = messages[i];
  const r = analyzeText(msg.text);
  results.push({
    id: msg.id,
    text: msg.text,
    category: msg.category,
    is_scam: msg.is_scam,
    gold_label: msg.gold_label,
    gold_risk: msg.gold_risk,
    js_risk_level: r.risk_level,
    js_prediction: r.prediction,
    js_refined_prediction: r.refined_prediction,
    js_confidence: r.confidence,
    js_rule_score: r.rule_score,
    js_assessment_score: r.assessment_score,
    js_refined_assessment_score: r.refined_assessment_score,
  });
}
const elapsed = Date.now() - startTime;
console.log(`Frontend pipeline completed in ${elapsed}ms (${Math.round(elapsed / messages.length)}ms avg)`);

// Load previous comparison to check against Python
const compPath = path.join(root, 'experiments', 'comparison_results.json');
if (fs.existsSync(compPath)) {
  const comp = JSON.parse(fs.readFileSync(compPath, 'utf-8'));
  let match = 0;
  let predMatch = 0;
  for (let i = 0; i < results.length; i++) {
    const r = results[i];
    const c = comp.find(x => x.id === r.id);
    if (c && c.py_risk_level === r.js_risk_level) match++;
    if (c && c.py_prediction === r.js_prediction) predMatch++;
  }
  console.log(`\n=== FRONTEND vs PYTHON (from previous comparison_results.json) ===`);
  console.log(`Total: ${results.length}`);
  console.log(`risk_level match: ${match}/${results.length} (${(match/results.length*100).toFixed(1)}%)`);
  console.log(`prediction match: ${predMatch}/${results.length} (${(predMatch/results.length*100).toFixed(1)}%)`);
  if (match === results.length) console.log(`*** EXACT MATCH on all ${results.length} messages! ***`);
}

// Also compare to gold risk? But gold risk is ground truth, not pipeline
// For validation bar: we previously reported JS vs Python match, not vs gold.
// We should also report that.

// Write js_results_frontend.json for later python comparison
const outPath = path.join(__dirname, 'frontend_js_results.json');
fs.writeFileSync(outPath, JSON.stringify(results, null, 2));
console.log(`\nFrontend results written to ${outPath}`);
console.log(`Now run: python frontend/scripts/validate_text_python.py  (to compare with Python pipeline)`);
