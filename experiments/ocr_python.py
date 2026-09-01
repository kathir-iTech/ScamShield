import json
import os
import sys

import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

HERE = os.path.dirname(os.path.abspath(__file__))
in_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "ocr_test_images")
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "ocr_python_results.json")
manifest_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "ocr_manifest.json")


def main():
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    results = {}
    for item in manifest["images"]:
        img = os.path.join(in_dir, item["image"])
        text = pytesseract.image_to_string(img).strip()
        results[item["image"]] = {"extracted_text": text, "raw_len": len(text)}

    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Python (pytesseract) OCR done for {len(results)} images -> {out}")


if __name__ == "__main__":
    main()
