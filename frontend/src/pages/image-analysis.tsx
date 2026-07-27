import { useState, useRef, useEffect, useCallback } from 'react';
import { useAnalyzeImage } from '@/hooks/use-scamshield';
import { useNetworkStatus } from '@/hooks/use-network-status';
import { useAnalysisNavigation } from '@/features/analysis/hooks/use-analysis-navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ThinkingLoader } from '@/components/ui/thinking-loader';
import { PageTransition } from '@/components/ui/page-transition';
import { imageAnalysisSchema } from '@/utils/validation';
import { z } from 'zod';
import { Upload, X, Shield, WifiOff, Lock } from 'lucide-react';

const THINKING_PHRASES = [
  'Reading your image...',
  'Extracting text...',
  'Analysing content...',
  'Checking for scam patterns...',
  'Preparing your result...',
];

export default function ImageAnalysis() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
      const result = await mutation.mutateAsync({ file, signal: abortRef.current.signal });
      navigateToResult(result, true, undefined, file.name);
    } catch {}
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-xl space-y-6">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 dark:bg-emerald-900/20">
            <Shield className="h-6 w-6 text-emerald-500" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Upload a screenshot</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Upload a screenshot of a suspicious message.
          </p>
        </div>

        {!isOnline && (
          <Card>
            <CardContent className="flex items-center gap-3 py-4">
              <WifiOff className="h-5 w-5 shrink-0 text-amber-500" />
              <p className="text-sm text-zinc-600 dark:text-zinc-400">You&apos;re offline. Connect to the internet to analyse.</p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardContent className="space-y-4 pt-6">
            <div
              className={`relative flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-12 transition-all duration-150 ${
                dragOver
                  ? 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-900/10'
                  : 'border-zinc-200 hover:border-zinc-300 dark:border-zinc-700 dark:hover:border-zinc-600'
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
                    className="absolute -right-2 -top-2 flex h-7 w-7 items-center justify-center rounded-full bg-zinc-800 text-white transition-colors hover:bg-zinc-700"
                    aria-label="Remove">
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <>
                  <Upload className="mb-3 h-8 w-8 text-zinc-400" />
                  <p className="text-sm text-zinc-600 dark:text-zinc-400">Click or drag to upload</p>
                  <p className="mt-1 text-xs text-zinc-400">PNG, JPEG, WebP &mdash; up to 10 MB</p>
                </>
              )}
            </div>

            {error && <p className="text-sm text-red-500 animate-slide-up" role="alert">{error}</p>}

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lock className="h-3 w-3 text-zinc-300 dark:text-zinc-600" />
                <span className="text-xs text-zinc-400">Processed privately</span>
              </div>
              <Button onClick={handleSubmit} disabled={!file || mutation.isPending || !isOnline}>
                {mutation.isPending ? (
                  <ThinkingLoader phrases={THINKING_PHRASES} />
                ) : (
                  'Analyse'
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {mutation.isError && (
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-zinc-600 dark:text-zinc-400">
                  {mutation.error?.message || 'Analysis failed.'}
                </p>
                <Button variant="secondary" size="sm"
                  onClick={() => {
                    if (!file) return;
                    abortRef.current = new AbortController();
                    mutation.mutate({ file, signal: abortRef.current.signal });
                  }}
                >
                  Retry
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </PageTransition>
  );
}
