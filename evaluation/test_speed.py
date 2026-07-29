import urllib.request, json, time

req = urllib.request.Request(
    'http://localhost:8000/analyze/text',
    data=json.dumps({'text': 'Test message for timing'}).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
start = time.time()
with urllib.request.urlopen(req, timeout=120) as r:
    elapsed = time.time() - start
    d = json.loads(r.read())
    print(f"Response time: {elapsed:.3f}s")
    print(f"Prediction: {d['prediction']}, Confidence: {d['confidence']:.3f}")
