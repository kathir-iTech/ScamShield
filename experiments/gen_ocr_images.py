import csv
import os
import random
import re
import sys

from PIL import Image, ImageDraw, ImageFont

GOLD = os.path.join("datasets", "gold", "gold_dataset.csv")
OUT_DIR = os.path.join("experiments", "ocr_test_images")
OUT_JSON = os.path.join("experiments", "ocr_manifest.json")

N = 25
SEED = 20260730

random.seed(SEED)


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_message(text, path):
    text = re.sub(r"\s+", " ", text).strip()
    font_size = 16
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    # Estimate dimensions
    margin_x, margin_y = 24, 24
    pad = 14
    bubble_x = 20
    line_height = int(font_size * 1.55)
    max_width = 420
    pad_img = Image.new("RGB", (10, 10))
    d2 = ImageDraw.Draw(pad_img)
    lines = wrap_text(d2, text, font, max_width)

    bubble_w = max_width + 2 * pad
    bubble_h = len(lines) * line_height + 2 * pad

    img_w = margin_x * 2 + bubble_w
    img_h = margin_y * 2 + bubble_h
    img = Image.new("RGB", (img_w, img_h), "#128C7E")
    draw = ImageDraw.Draw(img)

    # header bar (whatsapp-like)
    draw.rectangle([0, 0, img_w, 40], fill="#075E54")
    draw.text((margin_x + bubble_x, 10), "ScamShield Test Chat", fill="white", font=font)

    # bubble
    bx = bubble_x + 4
    by = 54
    draw.rounded_rectangle(
        [bx, by, bx + bubble_w, by + bubble_h],
        radius=12, fill="#DCF8C6"
    )
    yy = by + pad
    for ln in lines:
        draw.text((bx + pad, yy), ln, fill="#111111", font=font)
        yy += line_height

    img.save(path)


def main():
    with open(GOLD, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    scam = [r for r in rows if r["is_scam"].strip().lower() == "true"]
    safe = [r for r in rows if r["is_scam"].strip().lower() == "false"]

    # Deterministic interleaved mix: ~14 scam, ~11 safe
    random.shuffle(scam)
    random.shuffle(safe)
    n_scam = max(1, int(N * 0.55))
    n_safe = N - n_scam
    chosen = scam[:n_scam] + safe[:n_safe]
    chosen = sorted(chosen, key=lambda r: r["id"])

    os.makedirs(OUT_DIR, exist_ok=True)

    manifest = []
    for i, row in enumerate(chosen):
        idx = row["id"]
        text = row["text"]
        fname = f"img_{i:03d}_{idx}.png"
        path = os.path.join(OUT_DIR, fname)
        render_message(text, path)
        manifest.append({
            "image": fname,
            "gold_text": text,
            "id": idx,
            "gold_risk": row["risk_level"],
            "gold_label": row["ground_truth_label"],
            "is_scam": row["is_scam"].strip().lower() == "true",
        })

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"images": manifest, "count": len(manifest), "seed": SEED}, f, indent=2)

    print(f"Rendered {len(manifest)} images to {OUT_DIR}")
    print(json.dumps({m['id']: m['is_scam'] for m in manifest}, indent=2))


import json

if __name__ == "__main__":
    main()
