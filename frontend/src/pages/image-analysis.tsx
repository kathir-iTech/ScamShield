import { useState, useRef, useEffect, useCallback } from 'react';
import { useAnalyzeImage } from '@/hooks/use-scamshield';
import { useNetworkStatus } from '@/hooks/use-network-status';
import { useAnalysisNavigation } from '@/features/analysis/hooks/use-analysis-navigation';
import { PipelineLoader } from '@/components/ui/pipeline-loader';
import { OcrProgressIndicator } from '@/components/ui/ocr-progress';
import { PageTransition } from '@/components/ui/page-transition';
import { imageAnalysisSchema } from '@/utils/validation';
import { z } from 'zod';
import { Upload, X, Shield, WifiOff, Lock } from 'lucide-react';

export default function ImageAnalysis() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPipeline, setShowPipeline] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const mutation = useAnalyzeImage();
  const { navigateToResult } = useAnalysisNavigation();
  const isOnline = useNetworkStatus();

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  const validateFile = useCallback((f: File): string | null => {
    try {
      imageAnalysisSchema.shape.file.parse(f);
      return null;
    } catch (err) {
      if (err instanceof z.ZodError) return err.issues[0]?.message || 'Invalid file';
      return 'Invalid file';
    }
  }, []);

  const handleFile = useCallback((f: File) => {
    setError(null);
    const validationError = validateFile(f);
    if (validationError) { setError(validationError); setFile(null); setPreview(null); return; }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }, [validateFile]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  }, [handleFile]);

  const clearFile = useCallback(() => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null); setPreview(null); setError(null);
    if (inputRef.current) inputRef.current.value = '';
  }, [preview]);

  const handleSubmit = async () => {
    if (!file) return;
    setError(null);
    try {
      abortRef.current = new AbortController();
      setShowPipeline(true);
      const result = await mutation.mutateAsync({ file, signal: abortRef.current.signal });
      setShowPipeline(false);
      navigateToResult(result, true, undefined, file.name);
    } catch {
      setShowPipeline(false);
    }
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-2xl px-6 py-16 sm:py-20">
        <div className="text-center mb-10">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass">
            <Shield className="h-6 w-6 text-accent" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">
            Upload a screenshot
          </h1>
          <p className="mt-2 text-text-secondary/70">
            Upload a screenshot of a suspicious message.
          </p>
        </div>

        {!isOnline && (
          <div className="mb-6 glass rounded-2xl p-4 flex items-center gap-3 animate-slide-up">
            <WifiOff className="h-5 w-5 shrink-0 text-warning" />
            <div>
              <p className="text-sm text-text-secondary">You're offline.</p>
              <p className="text-xs text-text-tertiary">Text analysis works offline. Image OCR needs internet for first-time model download (~3 MB) — if you've used it before, it may still work from cache.</p>
            </div>
          </div>
        )}

        {showPipeline ? (
          <div className="space-y-4">
            <OcrProgressIndicator isActive={showPipeline} />
            <div className="glass rounded-2xl overflow-hidden animate-scale-in">
              <div className="p-6">
                <div className="flex items-center gap-3 mb-6">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10">
                    <Shield className="h-4 w-4 text-accent" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-text-primary">Analysing screenshot</p>
                    <p className="text-xs text-text-tertiary">AI is reviewing the image</p>
                  </div>
                </div>
                <PipelineLoader />
              </div>
            </div>
          </div>
        ) : (
          <div className="glass rounded-2xl overflow-hidden">
            <div className="p-5 sm:p-6">
              <div
                className={`relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-all duration-200 ${
                  dragOver
                    ? 'border-accent/50 bg-accent/5'
                    : 'border-glass-border hover:border-glass-border-hover'
                }`}
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => inputRef.current?.click()}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click(); }}
                role="button"
                tabIndex={0}
                aria-label="Upload screenshot"
              >
                <input
                  ref={inputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  onChange={handleChange}
                  aria-hidden="true"
                />
                {preview ? (
                  <div className="relative animate-scale-in">
                    <img src={preview} alt="Preview" className="max-h-48 rounded-xl object-contain" />
                    <button type="button" onClick={(e) => { e.stopPropagation(); clearFile(); }}
                      className="absolute -right-2 -top-2 flex h-7 w-7 items-center justify-center rounded-full bg-glass-strong text-text-secondary transition-colors hover:text-text-primary hover:bg-glass-hover"
                      aria-label="Remove">
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <>
                    <Upload className="mb-3 h-8 w-8 text-text-tertiary" />
                    <p className="text-sm text-text-secondary">Click or drag to upload</p>
                    <p className="mt-1 text-xs text-text-tertiary">PNG, JPEG, WebP &mdash; up to 10 MB</p>
                  </>
                )}
              </div>

              {error && <p className="mt-3 text-sm text-danger animate-slide-up" role="alert">{error}</p>}
            </div>

            <div className="flex items-center justify-between border-t border-glass-border px-5 py-4 sm:px-6">
              <div className="flex items-center gap-2">
                <Lock className="h-3 w-3 text-text-tertiary" />
                <span className="text-xs text-text-tertiary">Processed privately</span>
              </div>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!file || mutation.isPending}
                className="glass-button group relative inline-flex h-10 items-center gap-2 rounded-xl px-5 text-sm font-semibold text-white disabled:opacity-30 disabled:cursor-not-allowed"
              >
                {mutation.isPending ? (
                  <span className="flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-white/60 animate-pulse" />
                    Analysing
                  </span>
                ) : (
                  'Analyse'
                )}
              </button>
            </div>
          </div>
        )}

        {mutation.isError && !showPipeline && (
          <div className="mt-6 glass rounded-2xl p-5 animate-slide-up" role="alert">
            <div className="flex items-center justify-between">
              <p className="text-sm text-text-secondary">
                {mutation.error?.message || 'Analysis failed.'}
              </p>
              <button
                type="button"
                onClick={() => {
                  if (!file) return;
                  abortRef.current = new AbortController();
                  mutation.mutate({ file, signal: abortRef.current.signal });
                }}
                className="glass-button relative inline-flex h-9 items-center gap-1.5 rounded-xl px-4 text-xs font-semibold text-white"
              >
                Retry
              </button>
            </div>
          </div>
        )}
      </div>
    </PageTransition>
  );
}
