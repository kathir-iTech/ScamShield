import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    t0 = time.perf_counter()
    import core.metrics
    t1 = time.perf_counter()
    import_metrics_ms = (t1 - t0) * 1000

    t0 = time.perf_counter()
    import predict
    t1 = time.perf_counter()
    import_predict_ms = (t1 - t0) * 1000

    text = "Your account has been compromised. Click http://evil.com to verify now."

    t0 = time.perf_counter()
    label, confidence = predict.predict(text)
    t1 = time.perf_counter()
    first_prediction_ms = (t1 - t0) * 1000

    t0 = time.perf_counter()
    for _ in range(10):
        predict.predict(text)
    t1 = time.perf_counter()
    subsequent_predictions_ms = (t1 - t0) * 1000 / 10

    print("=== Startup Profiling ===")
    print(f"import core.metrics:      {import_metrics_ms:>8.2f} ms")
    print(f"import predict:           {import_predict_ms:>8.2f} ms")
    print(f"first predict() call:     {first_prediction_ms:>8.2f} ms (includes model loading)")
    print(f"subsequent predict() avg: {subsequent_predictions_ms:>8.2f} ms (no loading)")
    print(f"model load overhead:      {first_prediction_ms - subsequent_predictions_ms:>8.2f} ms")

if __name__ == "__main__":
    main()
