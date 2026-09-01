import json
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("."))

from services.orchestrator import analyze_text  # noqa: E402

MANIFEST = os.path.join("experiments", "ocr_manifest.json")
PY = os.path.join("experiments", "ocr_python_results.json")
JS = os.path.join("experiments", "ocr_js_results.json")
OUT = os.path.join("experiments", "ocr_pypipeline_results.json")


def risk(r):
    return (r or "").replace("VERY LOW", "VERY_LOW").replace(" ", "_").upper()


def main():
    with open(MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    with open(PY, "r", encoding="utf-8") as f:
        py = json.load(f)
    with open(JS, "r", encoding="utf-8") as f:
        js = json.load(f)

    results = {}
    for item in manifest["images"]:
        img = item["image"]
        entry = {}
        for label, src in (("pytext", py), ("jstext", js)):
            text = src[img]["extracted_text"]
            try:
                res = analyze_text(text)
                entry[label] = {"risk_level": risk(res.get("risk_level"))}
            except Exception as e:
                entry[label] = {"risk_level": "ERROR", "err": str(e)}
        results[img] = entry

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Python pipeline OCR cross-check done")


if __name__ == "__main__":
    main()
