import { createWorker } from 'tesseract.js';

export interface OcrProgress {
  status: string;
  progress: number; // 0-1
  isDownloading: boolean;
}

type ProgressCallback = (p: OcrProgress) => void;

let workerInstance: Awaited<ReturnType<typeof createWorker>> | null = null;
let workerReady = false;
let initPromise: Promise<Awaited<ReturnType<typeof createWorker>>> | null = null;

// Track whether we've ever completed first load (persisted in memory only;
// persists for session, resets on reload which is exactly when download would re-happen if not cached in IndexedDB)
let hasCompletedFirstLoad = false;

const DOWNLOAD_STATUSES = new Set([
  'loading tesseract core',
  'loading language traineddata',
  'initializing tesseract',
  'initializing api',
]);

// Global progress subscribers for UI (image-analysis page can show first-load download progress)
const globalProgressListeners = new Set<ProgressCallback>();
let lastProgress: OcrProgress | null = null;

export function subscribeOcrProgress(cb: ProgressCallback): () => void {
  globalProgressListeners.add(cb);
  if (lastProgress) cb(lastProgress);
  return () => globalProgressListeners.delete(cb);
}

function notifyGlobalProgress(p: OcrProgress) {
  lastProgress = p;
  for (const cb of globalProgressListeners) cb(p);
}

function isDownloadingStatus(status: string): boolean {
  return DOWNLOAD_STATUSES.has(status);
}

export function isOcrFirstLoad(): boolean {
  return !hasCompletedFirstLoad && !workerReady;
}

async function createOcrWorker(onProgress?: ProgressCallback): Promise<Awaited<ReturnType<typeof createWorker>>> {
  // Self-hosted assets: worker, core, language data live in /public
  // /tesseract/worker.min.js  (111 KB)
  // /tesseract/tesseract-core.wasm.js + .wasm (8 MB total)
  // /tessdata/eng.traineddata[.gz] (2.9 MB gzipped, 5.2 MB raw)
  // This keeps the critical language data off the default CDN and makes
  // the app offline-capable after first download (IndexedDB cache).
  const worker = await createWorker('eng', 1, {
    workerPath: '/tesseract/worker.min.js',
    corePath: '/tesseract/tesseract-core.wasm.js',
    langPath: '/tessdata',
    gzip: true,
    logger: (m: { status: string; progress: number }) => {
      const downloading = isDownloadingStatus(m.status);
      const prog: OcrProgress = {
        status: m.status,
        progress: m.progress,
        isDownloading: downloading,
      };
      onProgress?.(prog);
      notifyGlobalProgress(prog);
    },
  } as unknown as Parameters<typeof createWorker>[2]);

  return worker;
}

export async function ensureWorker(
  onProgress?: ProgressCallback,
  signal?: AbortSignal,
): Promise<Awaited<ReturnType<typeof createWorker>>> {
  if (workerReady && workerInstance) return workerInstance;
  if (initPromise) return initPromise;

  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');

  initPromise = (async () => {
    const abortHandler = () => {
      // tesseract.js doesn't natively support abort during init, but we can
      // surface the abort to caller; the worker will still finish init in background
      // but caller can ignore result.
    };
    signal?.addEventListener('abort', abortHandler, { once: true });

    try {
      const w = await createOcrWorker(onProgress);
      if (signal?.aborted) {
        // If aborted during init, terminate the just-created worker to avoid leak
        try { await w.terminate(); } catch {}
        throw new DOMException('Aborted', 'AbortError');
      }
      workerInstance = w;
      workerReady = true;
      hasCompletedFirstLoad = true;
      return w;
    } finally {
      signal?.removeEventListener('abort', abortHandler);
      initPromise = null;
    }
  })();

  return initPromise;
}

export async function recognizeImage(
  file: File,
  onProgress?: ProgressCallback,
  signal?: AbortSignal,
): Promise<string> {
  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');

  const worker = await ensureWorker(onProgress, signal);

  if (signal?.aborted) throw new DOMException('Aborted', 'AbortError');

  // Wrap recognition with abort support via race
  let abortListener: (() => void) | null = null;
  const abortPromise = new Promise<never>((_, reject) => {
    if (signal) {
      abortListener = () => reject(new DOMException('Aborted', 'AbortError'));
      signal.addEventListener('abort', abortListener, { once: true });
    }
  });

  try {
    const resultPromise = worker.recognize(file);
    const result = signal ? await Promise.race([resultPromise, abortPromise]) : await resultPromise;
    // result is { data: { text: string } }
    const text = (result as { data: { text: string } }).data.text?.trim() ?? '';
    return text;
  } finally {
    if (signal && abortListener) signal.removeEventListener('abort', abortListener);
  }
}

export async function terminateWorker(): Promise<void> {
  if (workerInstance) {
    try { await workerInstance.terminate(); } catch {}
    workerInstance = null;
    workerReady = false;
    initPromise = null;
  }
}

// For testing / validation in Node (where window is not available)
// This export is used only by validation scripts that run in Node
export function getWorkerConfig() {
  return {
    workerPath: '/tesseract/worker.min.js',
    corePath: '/tesseract/tesseract-core.wasm.js',
    langPath: '/tessdata',
    gzip: true,
  };
}
