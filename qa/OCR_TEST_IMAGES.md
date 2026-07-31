# OCR Test Images List — Manual QA

> Use these with `POST /analyze/image` (multipart form, `file` field).
> All images must be PNG/JPG/JPEG/WEBP/BMP, max 10MB.
> Create these files under `qa/test-images/` (e.g., `qa/test-images/01-scam-kyc-clean.png`).
> Recommended: 800x400px, dark text on light background, large font.

---

## Scam Screenshots (Expected: is_scam=true)

| # | File Name | Description | OCR Expected Text |
|---|-----------|-------------|-------------------|
| 1 | `01-scam-kyc-clean.png` | Clean screenshot of bank KYC scam SMS | "Your SBI account will be deactivated. Update KYC: https://sbi-kyc.xyz" |
| 2 | `02-scam-lottery-clean.png` | Clean lottery win message | "Congratulations! You won 50 Lakh. Call 9876543210" |
| 3 | `03-scam-upi-clean.png` | Clean UPI payment scam | "Your UPI transaction of Rs 15000 is pending. Confirm now" |
| 4 | `04-scam-job-clean.png` | Clean job scam with fee | "Work from home job. Earn 50000/month. Registration fee 500" |
| 5 | `05-scam-courier-clean.png` | Clean courier customs scam | "Your parcel from Dubai is held at customs. Pay 5000 release fee" |

## Legitimate Screenshots (Expected: is_scam=false)

| # | File Name | Description | OCR Expected Text |
|---|-----------|-------------|-------------------|
| 6 | `06-legit-bank-credit.png` | Legit bank credit notification | "Your account ending 4821 credited Rs 25000 on 25-Jul" |
| 7 | `07-legit-otp.png` | Legit OTP message | "Your OTP for login is 482916. Valid for 5 minutes" |
| 8 | `08-legit-order.png` | Legit delivery notification | "Your Blinkit order ORD789 has been delivered" |

## Image Quality Tests (Expected: no crash, graceful handling)

| # | File Name | Description | Expected Behavior |
|---|-----------|-------------|-------------------|
| 9 | `09-scam-kyc-blurry.png` | Blurry screenshot of KYC scam | 200 or graceful error; if OCR succeeds, is_scam=true |
| 10 | `10-scam-kyc-rotated.png` | Screenshot rotated 90 degrees | 200 or graceful error |
| 11 | `11-scam-kyc-small.png` | Tiny image (e.g., 50x50px) | 200 (may return low confidence) or validation error |
| 12 | `12-huge-image.png` | Image near 10MB limit | 200, processed within limit |
| 13 | `13-corrupted.txt` | Text file renamed to .png (corrupted) | 400 error |

## Edge Cases (Expected: validation errors)

| # | File Name | Description | Expected Behavior |
|---|-----------|-------------|-------------------|
| 14 | `14-over-10mb.png` | Image larger than 10MB | 413/400 error |
| 15 | `15-oversized-dimensions.png` | Image exceeding max dimension | 400 validation error |
| 16 | `16-empty-file.png` | Zero-byte file | 400 error |

---

## Image Generation Tips

- Use any screenshot tool (Windows: Win+Shift+S) to capture sample SMS texts.
- For rotated: open image, rotate 90°, save as new file.
- For blurry: use Paint/Photoshop blur filter, or take a low-quality phone photo of a screen.
- For huge: use a large generated image via:
  ```bash
  python -c "from PIL import Image; Image.new('RGB', (4000, 4000), 'white').save('qa/test-images/12-huge-image.png')"
  ```
- For over-10MB: `python -c "from PIL import Image; im = Image.new('RGB', (8000, 8000), 'white'); im.save('qa/test-images/14-over-10mb.png')"` (adjust size until >10MB)

---

## Test Procedure

1. Create all image files under `qa/test-images/`
2. For each: `curl -X POST http://localhost:8000/analyze/image -F "file=@qa/test-images/01-scam-kyc-clean.png"`
3. Record results in `MANUAL_TEST_RESULTS.md`
4. Report failures in `BUG_REPORT_TEMPLATE.md`
