const fs = require("fs");
const path = require("path");
const { analyzeText } = require("./pipeline.js");

const MANIFEST = path.join(__dirname, "ocr_manifest.json");
const PY = path.join(__dirname, "ocr_python_results.json");
const JS = path.join(__dirname, "ocr_js_results.json");
const PYPIPE = path.join(__dirname, "ocr_pypipeline_results.json");

function normRisk(r) {
  return (r || "").toUpperCase().replace("VERY LOW", "VERY_LOW").replace(" ", "_").trim();
}
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

(async () => {
  const manifest = JSON.parse(fs.readFileSync(MANIFEST, "utf-8"));
  const py = JSON.parse(fs.readFileSync(PY, "utf-8"));
  const js = JSON.parse(fs.readFileSync(JS, "utf-8"));
  const pyp = JSON.parse(fs.readFileSync(PYPIPE, "utf-8"));

  console.log("img | sim | JS-PYtext | JS-JStext | pytext->PYpipe | jstext->PYpipe | py==js | pytext_pipe==jstext_pipe");
  let jsOcrMatch = 0;
  let polyMatch = 0;
  let crossEngineOcrAgree = 0;
  const n = manifest.images.length;

  for (const item of manifest.images) {
    const img = item.image;
    const pyText = (py[img] || {}).extracted_text || "";
    const jsText = (js[img] || {}).extracted_text || "";
    const sim = similarity(pyText, jsText);

    const jsPyText = normRisk(analyzeText(pyText).risk_level);
    const jsJsText = normRisk(analyzeText(jsText).risk_level);

    const ppPy = normRisk(((pyp[img] || {}).pytext || {}).risk_level);
    const ppJs = normRisk(((pyp[img] || {}).jstext || {}).risk_level);

    const jsOcrSame = jsPyText === jsJsText;
    const polySame = ppPy === ppJs;
    const crossSame = jsPyText === ppPy && jsJsText === ppJs;
    if (jsOcrSame) jsOcrMatch++;
    if (polySame) polyMatch++;
    if (crossSame) crossEngineOcrAgree++;

    console.log(
      `${img} | ${sim.toFixed(3)} | ${jsPyText} | ${jsJsText} | ${ppPy} | ${ppJs} | ${jsOcrSame ? "Y" : "N"} | ${polySame ? "Y" : "N"}`
    );
  }

  console.log(`\n=== SUMMARY ===`);
  console.log(`Images: ${n}`);
  console.log(`JS pipeline: py-OCRtext risk == js-OCRtext risk : ${jsOcrMatch}/${n}`);
  console.log(`PY pipeline: py-OCRtext risk == js-OCRtext risk : ${polyMatch}/${n}`);
  console.log(`Cross-engine agreement (both pipelines agree on each text): ${crossEngineOcrAgree}/${n}`);
  console.log(`(If pipel.ymismatches == pipeline-mismatches, the 2 diffs are OCR-text-driven, not pipeline-driven.)`);
})();
