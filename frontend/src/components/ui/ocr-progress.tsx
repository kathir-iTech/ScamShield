import { useEffect, useState } from 'react';
import { Download, HardDrive, Wifi } from 'lucide-react';
import { subscribeOcrProgress, type OcrProgress } from '@/services/ocr';

interface OcrProgressProps {
  isActive: boolean;
}

export function OcrProgressIndicator({ isActive }: OcrProgressProps) {
  const [progress, setProgress] = useState<OcrProgress | null>(null);
  const [isFirstLoad, setIsFirstLoad] = useState(false);

  useEffect(() => {
    if (!isActive) return;
    const unsub = subscribeOcrProgress((p) => {
      setProgress(p);
      if (p.isDownloading) setIsFirstLoad(true);
    });
    return unsub;
  }, [isActive]);

  if (!isActive) return null;

  // If no progress yet (worker not started) show generic preparing state
  if (!progress) {
    return (
      <div className="glass rounded-2xl p-6 animate-slide-up" role="status" aria-live="polite">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10 animate-pulse">
            <Download className="h-4 w-4 text-accent" />
          </div>
          <div>
            <p className="text-sm font-semibold text-text-primary">Preparing OCR engine</p>
            <p className="text-xs text-text-tertiary">Getting ready to read your screenshot…</p>
          </div>
        </div>
      </div>
    );
  }

  const pct = Math.round(progress.progress * 100);
  const statusLabel = progress.status === 'loading tesseract core'
    ? 'Downloading OCR core'
    : progress.status === 'loading language traineddata'
    ? 'Downloading language data'
    : progress.status === 'initializing tesseract'
    ? 'Initializing OCR'
    : progress.status === 'initializing api'
    ? 'Starting OCR'
    : progress.status === 'recognizing text'
    ? 'Reading text from image'
    : progress.status;

  const showDownloadHint = progress.isDownloading || isFirstLoad;

  return (
    <div className="glass rounded-2xl overflow-hidden animate-scale-in" role="status" aria-live="polite" aria-label="Downloading OCR model">
      <div className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10">
            {progress.status === 'recognizing text' ? (
              <HardDrive className="h-4 w-4 text-accent" />
            ) : (
              <Download className="h-4 w-4 text-accent" />
            )}
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-text-primary">{statusLabel}</p>
            <p className="text-xs text-text-tertiary">
              {showDownloadHint
                ? 'First use downloads ~3 MB (5 MB raw). This may take a moment on slower connections — and only happens once.'
                : 'Analysing your screenshot…'}
            </p>
          </div>
          <span className="text-sm font-medium text-accent tabular-nums">{pct}%</span>
        </div>

        <div className="h-2 w-full overflow-hidden rounded-full bg-glass-border">
          <div
            className="h-full rounded-full bg-accent transition-all duration-300 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>

        {showDownloadHint && (
          <div className="mt-3 flex items-center gap-2 text-xs text-text-tertiary">
            <Wifi className="h-3 w-3" />
            <span>
              On a slow connection this can take 20–60 seconds. Please keep this tab open — it will continue automatically.
            </span>
          </div>
        )}

        <p className="mt-2 text-xs text-text-tertiary">
          {progress.isDownloading
            ? 'Downloading from your own site (no external CDN) — cached for next time.'
            : progress.status === 'recognizing text'
            ? 'Extracting text…'
            : 'Preparing…'}
        </p>
      </div>
    </div>
  );
}

// Compact inline progress for use inside existing pipeline loader area
export function OcrDownloadBanner() {
  const [progress, setProgress] = useState<OcrProgress | null>(null);
  useEffect(() => {
    const unsub = subscribeOcrProgress(setProgress);
    return unsub;
  }, []);
  if (!progress || !progress.isDownloading) return null;
  const pct = Math.round(progress.progress * 100);
  return (
    <div className="mb-4 rounded-xl border border-accent/20 bg-accent/5 p-3 flex items-center gap-3" role="status">
      <Download className="h-4 w-4 text-accent shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-text-primary">Downloading OCR model — {pct}%</p>
        <p className="text-xs text-text-tertiary">~3 MB, first use only. Please wait…</p>
        <div className="mt-1.5 h-1.5 w-full rounded-full bg-glass-border overflow-hidden">
          <div className="h-full bg-accent transition-all" style={{ width: `${pct}%` }} />
        </div>
      </div>
    </div>
  );
}
