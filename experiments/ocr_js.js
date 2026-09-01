const fs = require("fs");
const path = require("path");
const { createWorker } = require("tesseract.js");

const HERE = __dirname;
const inDir = process.argv[2] || path.join(HERE, "ocr_test_images");
const out = process.argv[3] || path.join(HERE, "ocr_js_results.json");
const manifestPath = path.join(HERE, "ocr_manifest.json");

(async () => {
  try {
    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
    const worker = await createWorker("eng", 1);
    const results = {};
    for (const item of manifest.images) {
      const imgPath = path.join(inDir, item.image);
      const { data } = await worker.recognize(imgPath);
      results[item.image] = { extracted_text: data.text.trim(), raw_len: data.text.trim().length };
    }
    await worker.terminate();
    fs.writeFileSync(out, JSON.stringify(results, null, 2), "utf-8");
    console.log(`JS (tesseract.js) OCR done for ${Object.keys(results).length} images -> ${out}`);
  } catch (e) {
    console.error("JS OCR FAIL:", e.message);
    process.exit(1);
  }
})();
