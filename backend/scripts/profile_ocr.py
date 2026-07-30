import time
import sys
import os
import statistics
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def percentile(data, p):
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (p / 100.0) * (len(sorted_data) - 1)
    f = int(k)
    c = f + 1
    if f >= len(sorted_data):
        return sorted_data[-1]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])

def create_test_image(width=400, height=100, text="Test message for OCR"):
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        draw.text((10, 10), text, fill="black", font=font)
        return img
    except ImportError:
        print("PIL not available, cannot create test image")
        return None

def main():
    try:
        from ocr import extract_text
    except ImportError as e:
        print(f"Cannot import ocr module: {e}")
        print("Make sure Tesseract is installed and in PATH")
        sys.exit(1)

    test_image = create_test_image()
    if test_image is None:
        print("Failed to create test image")
        sys.exit(1)

    temp_dir = tempfile.gettempdir()
    image_path = os.path.join(temp_dir, "scamshield_ocr_test.png")
    test_image.save(image_path)
    print(f"Test image saved to {image_path}")

    n_runs = 20
    latencies = []

    for i in range(n_runs):
        t0 = time.perf_counter()
        try:
            text = extract_text(image_path)
        except Exception as e:
            print(f"OCR failed on run {i}: {e}")
            continue
        t1 = time.perf_counter()
        elapsed = (t1 - t0) * 1000
        latencies.append(elapsed)

    if not latencies:
        print("No successful OCR runs")
        sys.exit(1)

    avg_ms = statistics.mean(latencies)
    min_ms = min(latencies)
    max_ms = max(latencies)
    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)

    print(f"\n=== OCR Latency Profiling ({len(latencies)} runs) ===")
    print(f"{'Metric':<15} {'Value (ms)':<15}")
    print("-" * 30)
    print(f"{'Min':<15} {min_ms:<15.2f}")
    print(f"{'Max':<15} {max_ms:<15.2f}")
    print(f"{'Avg':<15} {avg_ms:<15.2f}")
    print(f"{'P50':<15} {p50:<15.2f}")
    print(f"{'P95':<15} {p95:<15.2f}")
    print(f"Extracted text: {text[:80]!r}..." if len(text) > 80 else f"Extracted text: {text!r}")

    os.unlink(image_path)

if __name__ == "__main__":
    main()
