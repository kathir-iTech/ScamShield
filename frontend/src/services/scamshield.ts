import type {
  HealthResponse,
  ReadinessResponse,
  LivenessResponse,
  MetricsSnapshot,
  AnalysisResponse,
  ImageAnalysisResponse,
} from '@/types';
import { analyzeTextLocal } from '@/services/local-analysis';
import { recognizeImage } from '@/services/ocr';
import { decodeQrFromImage } from '@/services/qr';
import { repairUrls } from '@/lib/scamshield/repair-urls.js';

// --- Text analysis: direct local pipeline, no backend ---
export async function analyzeText(text: string, signal?: AbortSignal): Promise<AnalysisResponse> {
  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');

  // Simulate async to keep same interface as before (allows abort and loading states)
  // The pipeline itself is sync (<5ms), but we wrap to respect signal and keep UI consistent
  return new Promise<AnalysisResponse>((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException('Aborted', 'AbortError'));
      return;
    }
    const onAbort = () => reject(new DOMException('Aborted', 'AbortError'));
    signal?.addEventListener('abort', onAbort, { once: true });

    try {
      // Use queueMicrotask to keep it async but fast
      queueMicrotask(() => {
        try {
          if (signal?.aborted) {
            reject(new DOMException('Aborted', 'AbortError'));
            return;
          }
          const result = analyzeTextLocal(text);
          resolve(result);
        } catch (e) {
          reject(e);
        } finally {
          signal?.removeEventListener('abort', onAbort);
        }
      });
    } catch (e) {
      signal?.removeEventListener('abort', onAbort);
      reject(e);
    }
  });
}

// --- Image analysis: tesseract.js OCR + QR decode -> repair URLs -> local pipeline ---
export async function analyzeImage(file: File, signal?: AbortSignal): Promise<ImageAnalysisResponse> {
  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');

  // Step 1: OCR with tesseract.js (self-hosted lang data: /tessdata/eng.traineddata.gz)
  // On first use this downloads ~2.9MB gzipped (5.2MB raw) + core ~8MB on slow connections.
  // Subsequent uses hit IndexedDB cache (no download). Progress is surfaced via ocr.ts logger.
  const extractedText = await recognizeImage(file, undefined, signal);

  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');

  // Step 2: QR code decode — runs client-side with jsQR, no backend.
  // If a QR code contains a URL or UPI ID, we append it to the OCR text
  // so the SAME existing link/entity extraction + watchlist logic picks it up.
  const qrResult = await decodeQrFromImage(file);

  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');

  // Step 3: Combine OCR text with QR payload (if found) for unified pipeline input
  let combinedText = extractedText;
  if (qrResult.found && qrResult.payload) {
    const qrLabel = qrResult.type === 'url'
      ? 'QR_CODE_URL:'
      : qrResult.type === 'upi'
        ? 'QR_CODE_UPI:'
        : 'QR_CODE_TEXT:';
    combinedText = extractedText
      ? extractedText + '\n' + qrLabel + ' ' + qrResult.payload
      : qrLabel + ' ' + qrResult.payload;
  }

  // Step 4: URL repair (handles OCR mangling: dropped dots, spaces in URLs)
  const repaired = repairUrls(combinedText);

  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');

  // Step 5: Pipeline — same path as text analysis, no parallel pipeline
  const analysis = analyzeTextLocal(repaired);

  return {
    ...analysis,
    extracted_text: extractedText,
  };
}

// --- Health / system endpoints: now local, no backend dependency ---
// These are kept for dashboard compatibility but no longer call the backend.
// They return healthy stubs so the UI remains backend-free for its core function.

export async function health(signal?: AbortSignal): Promise<HealthResponse> {
  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');
  return {
    status: 'pass',
    service: 'Wary (local)',
    version: '2.0.0-local',
    build_version: 'local',
    environment: 'browser',
    startup_timestamp: Date.now() / 1000 - (performance.now() / 1000),
    uptime_seconds: Math.floor(performance.now() / 1000),
    release_id: 'local',
    checks: [{ name: 'pipeline', status: 'pass' }, { name: 'ocr', status: 'pass' }],
    dependencies: { model: 'pass', vectorizer: 'pass', config: 'pass' },
    config_summary: { mode: 'local', offline_capable: true },
    service_availability: 'available',
    active_requests: 0,
    test_mode: false,
  };
}

export async function ready(signal?: AbortSignal): Promise<ReadinessResponse> {
  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');
  return { status: 'ready' };
}

export async function live(signal?: AbortSignal): Promise<LivenessResponse> {
  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');
  return { status: 'alive' };
}

export async function metrics(signal?: AbortSignal): Promise<MetricsSnapshot> {
  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');
  return {
    total_requests: 0,
    successful_requests: 0,
    failed_requests: 0,
    active_requests: 0,
    validation_failures: 0,
    auth_failures: 0,
    rate_limit_events: 0,
    pipeline_failures: 0,
    ocr_requests: 0,
    text_requests: 0,
    average_latency_ms: 0,
    p50_latency_ms: 0,
    p95_latency_ms: 0,
    maximum_latency_ms: 0,
    uptime_seconds: Math.floor(performance.now() / 1000),
  };
}
