// Full pipeline comparison: Python vs JS/TS on gold dataset (308 messages)
// Compares final risk_level for every message

const fs = require('fs');
const path = require('path');
const pipeline = require('./pipeline');

function parseCSVLine(line) {
  const fields = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (c === '"') {
      if (inQuotes && i + 1 < line.length && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (c === ',' && !inQuotes) {
      fields.push(current);
      current = '';
    } else {
      current += c;
    }
  }
  fields.push(current);
  return fields;
}

// Proper multi-line aware CSV parser
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
    if (c === '\r' && !inQuotes) {
      continue;
    }
    current += c;
  }
  if (current.length > 0 || cells.length > 0) {
    cells.push(current);
    rows.push(cells);
  }
  return rows;
}

const csvPath = path.join(__dirname, '..', 'datasets', 'gold', 'gold_dataset.csv');
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
    text: text,
    category: fields[categoryIdx],
    is_scam: fields[isScamIdx],
    gold_label: fields[groundTruthIdx],
    gold_risk: fields[goldRiskIdx],
  });
}

console.log(`Loaded ${messages.length} messages from gold dataset`);
console.log(`Running JS pipeline on all messages...`);

const jsResults = [];
const startTime = Date.now();

for (let i = 0; i < messages.length; i++) {
  const msg = messages[i];
  const result = pipeline.analyzeText(msg.text);
  jsResults.push({
    id: msg.id,
    text: msg.text,
    category: msg.category,
    is_scam: msg.is_scam,
    gold_label: msg.gold_label,
    gold_risk: msg.gold_risk,
    js_risk_level: result.risk_level,
    js_prediction: result.prediction,
    js_refined_prediction: result.refined_prediction,
    js_confidence: result.confidence,
    js_rule_score: result.rule_score,
    js_assessment_score: result.assessment_score,
    js_refined_assessment_score: result.refined_assessment_score,
  });
  if ((i + 1) % 25 === 0) {
    const elapsed = Date.now() - startTime;
    const rate = (i + 1) / (elapsed / 1000);
    const eta = ((messages.length - i - 1) / rate);
    console.log(`  [${i + 1}/${messages.length}] ${rate.toFixed(1)} msg/sec, ETA ${eta.toFixed(0)}s`);
  }
}

const elapsed = Date.now() - startTime;
console.log(`JS pipeline completed in ${elapsed}ms (${Math.round(elapsed / messages.length)}ms avg)\n`);

const jsonPath = path.join(__dirname, 'js_results.json');
fs.writeFileSync(jsonPath, JSON.stringify(jsResults));
console.log(`JS results written to ${jsonPath}`);
console.log(`\nNow run: python experiments/compare_python_side.py`);
