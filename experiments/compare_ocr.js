const fs = require("fs");
const path = require("path");
const { analyzeText } = require("./pipeline.js");
const { repairUrls } = require("./repair_urls.js");

const HERE = __dirname;
const MANIFEST = path.join(HERE, "ocr_manifest.json");
const PY = process.argv[2] || path.join(HERE, "ocr_python_results.json");
const JS = process.argv[3] || path.join(HERE, "ocr_js_results.json");
const APPLY_REPAIR = process.argv[4] === "norepair" ? false : true;

function similarity(a, b) {
  const A = a.toLowerCase().replace(/\s+/g, " ");
  const B = b.toLowerCase().replace(/\s+/g, " ");
  if (A === B) return 1.0;
  const lcs = (x, y) => {
    const dp = Array.from({ length: x.length + 1 }, () => new Array(y.length + 1).fill(0));
    for (let i = 1; i <= x.length; i++)
      for (let j = 1; j <= y.length; j++)
        dp[i][j] = x[i - 1] === y[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1]);
    return dp[x.length][y.length];
  };
  const l = lcs(A, B);
  return l / Math.max(A.length, B.length);
}

function normRisk(r) {
  return (r || "").toUpperCase().replace("VERY LOW", "VERY_LOW").replace(" ", "_").trim();
}

(async () => {
  const manifest = JSON.parse(fs.readFileSync(MANIFEST, "utf-8"));
  const py = JSON.parse(fs.readFileSync(PY, "utf-8"));
  const js = JSON.parse(fs.readFileSync(JS, "utf-8"));

  let riskMatch = 0;
  let mismatchRows = [];
  let sims = [];

  console.log(`=== Set: ${path.basename(PY).replace('python_', '').replace('_results', '')} | repair=${APPLY_REPAIR} ===`);
  for (const item of manifest.images) {
    const img = item.image;
    let pyText = (py[img] || {}).extracted_text || "";
    let jsText = (js[img] || {}).extracted_text || "";
    if (APPLY_REPAIR) { pyText = repairUrls(pyText); jsText = repairUrls(jsText); }

    const pyRes = analyzeText(pyText);
    const jsRes = analyzeText(jsText);

    const pyRisk = normRisk(pyRes.risk_level);
    const jsRisk = normRisk(jsRes.risk_level);
    const sim = similarity(pyText, jsText);
    sims.push(sim);

    const match = pyRisk === jsRisk;
    if (match) riskMatch++;

    console.log(
      `${img}: py=${pyRisk} js=${jsRisk} sim=${sim.toFixed(3)} ${match ? "MATCH" : "*** MISMATCH ***"}`
    );

    if (!match) {
      mismatchRows.push({ image: img, id: item.id, gold_risk: item.gold_risk, py_risk: pyRisk, js_risk: jsRisk, py_pred: pyRes.prediction, js_pred: jsRes.prediction, py_text: (py[img]||{}).extracted_text, js_text: (js[img]||{}).extracted_text });
    }
  }

  const n = manifest.images.length;
  const avgSim = sims.reduce((a, b) => a + b, 0) / n;

  console.log("\n=== SUMMARY ===");
  console.log(`Images: ${n}`);
  console.log(`risk_level match (py-OCR vs js-OCR): ${riskMatch}/${n}`);
  console.log(`Text-extraction similarity: avg=${avgSim.toFixed(4)} min=${Math.min(...sims).toFixed(4)} max=${Math.max(...sims).toFixed(4)}`);

  if (mismatchRows.length) {
    console.log(`\n=== ${mismatchRows.length} risk_level MISMATCH(es) — RAW OCR side by side ===`);
    for (const m of mismatchRows) {
      console.log(`\n--- ${m.image} (gold=${m.gold_risk}) py=${m.py_risk} js=${m.js_risk} ---`);
      console.log(`  PY (pred ${m.py_pred}): ${m.py_text}`);
      console.log(`  JS (pred ${m.js_pred}): ${m.js_text}`);
    }
  }
})();
