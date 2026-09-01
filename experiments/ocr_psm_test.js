const fs = require("fs");
const path = require("path");
const { createWorker } = require("tesseract.js");

const MANIFEST = path.join(__dirname, "ocr_manifest.json");
const IN_DIR = path.join(__dirname, "ocr_test_images");
const OUT = process.argv[2] || path.join(__dirname, "ocr_js_psm6_results.json");
const PSM = parseInt(process.argv[3] || "6", 10);

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
  try {
    const manifest = JSON.parse(fs.readFileSync(MANIFEST, "utf-8"));
    const worker = await createWorker("eng", 1, {
      logger: () => {},
    });
    await worker.setParameters({
      tessedit_pageseg_mode: String(PSM),
    });

    const results = {};
    for (const item of manifest.images) {
      const imgPath = path.join(IN_DIR, item.image);
      const { data } = await worker.recognize(imgPath);
      const text = data.text.trim();
      const gold = item.gold_text;
      results[item.image] = {
        extracted_text: text,
        raw_len: text.length,
        sim_to_gold: Number(similarity(text, gold).toFixed(4)),
      };
      const flag = (item.id.includes("0119") || item.id.includes("0014")) ? "  <-- img_001/img_004" : "";
      console.log(`  ${item.image}: sim=${results[item.image].sim_to_gold} len=${text.length}${flag}`);
    }

    await worker.terminate();
    fs.writeFileSync(OUT, JSON.stringify({ psm: PSM, results }, null, 2), "utf-8");
    console.log(`\nDone PSM=${PSM} -> ${OUT}`);
  } catch (e) {
    console.error("PSM test FAIL:", e.message);
    process.exit(1);
  }
})();
