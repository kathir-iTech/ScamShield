import csv
import json
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

GOLD = os.path.join("datasets", "gold", "gold_dataset.csv")
OUT_DIR = os.path.join("experiments", "ocr_test_images_noisy")
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


def render_base(text):
    text = " ".join(text.split())
    font_size = 16
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

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
    draw.rectangle([0, 0, img_w, 40], fill="#075E54")
    draw.text((margin_x + bubble_x, 10), "ScamShield Test Chat", fill="white", font=font)
    bx = bubble_x + 4
    by = 54
    draw.rounded_rectangle([bx, by, bx + bubble_w, by + bubble_h], radius=12, fill="#DCF8C6")
    yy = by + pad
    for ln in lines:
        draw.text((bx + pad, yy), ln, fill="#111111", font=font)
        yy += line_height
    return img


def degrade(img, i):
    variant = i % 3
    # mild Gaussian blur
    if variant in (0, 1):
        img = img.filter(ImageFilter.GaussianBlur(radius=0.7))
    elif variant == 2:
        img = img.filter(ImageFilter.GaussianBlur(radius=1.1))

    # JPEG compression artifacts
    tmp = "C:\\Users\\DEVELO~1\\AppData\\Local\\Temp\\opencode\\noisy_tmp.jpg"
    quality = 60 if variant == 0 else 45
    img.save(tmp, "JPEG", quality=quality)
    img = Image.open(tmp).convert("RGB")

    # +/- 3 degree rotation (width modes simplify to edges)
    angle = [-3, 3, 2.5][variant]
    if img.width < img.height:
        img = img.rotate(angle, expand=True, fillcolor="#128C7E")
    else:
        img = img.rotate(angle, expand=False, fillcolor="#128C7E")
    return img


def main():
    with open(GOLD, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    with open(os.path.join("experiments", "ocr_manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)

    os.makedirs(OUT_DIR, exist_ok=True)
    for i, item in enumerate(manifest["images"]):
        row = next((r for r in rows if r["id"] == item["id"]), None)
        if row is None:
            continue
        base = render_base(row["text"])
        noisy = degrade(base, i)
        noisy.save(os.path.join(OUT_DIR, item["image"]))
    print(f"Rendered {len(manifest['images'])} NOISY images to {OUT_DIR}")


if __name__ == "__main__":
    main()
