import { useState, useRef, useCallback } from 'react';
import { useAnalyzeImage } from '@/hooks/use-scamshield';
import { useAnalysisNavigation } from '@/features/analysis/hooks/use-analysis-navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageTransition } from '@/components/ui/page-transition';
import { Upload, Image as ImageIcon, Loader2, AlertCircle, X } from 'lucide-react';
import { imageAnalysisSchema } from '@/utils/validation';
import { z } from 'zod';

export default function ImageAnalysis() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const mutation = useAnalyzeImage();
  const { navigateToResult } = useAnalysisNavigation();

  const validateFile = useCallback((f: File): string | null => {
    try {
      imageAnalysisSchema.shape.file.parse(f);
      return null;
    } catch (err) {
      if (err instanceof z.ZodError) {
        return err.issues[0]?.message || 'Invalid file';
      }
      return 'Invalid file';
    }
  }, []);

  const handleFile = useCallback(
    (f: File) => {
      setError(null);
      const validationError = validateFile(f);
      if (validationError) {
        setError(validationError);
        setFile(null);
        setPreview(null);
        return;
      }
      setFile(f);
      setPreview(URL.createObjectURL(f));
    },
    [validateFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

  const clearFile = useCallback(() => {
    setFile(null);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
  }, [preview]);

  const handleSubmit = async () => {
    if (!file) return;
    setError(null);
    try {
      const result = await mutation.mutateAsync(file);
      navigateToResult(result, true, undefined, file.name);
    } catch {
      // error handled by mutation state
    }
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
<h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
          Image Analysis
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Extract and analyze text from an image
        </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ImageIcon className="h-5 w-5" />
              Upload Image
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div
            className={`relative flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 ${
              dragOver
                ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
                : 'border-zinc-300 hover:border-zinc-400 dark:border-zinc-600 dark:hover:border-zinc-500'
            }`}
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click();
              }}
            aria-label="Upload image for analysis"
            aria-describedby={error ? "file-error" : undefined}
          >
              <input
                ref={inputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/bmp"
                className="hidden"
                onChange={handleChange}
              aria-hidden="true"
              aria-label="Choose image file"
            />
              {preview ? (
                <div className="relative">
                  <img
                    src={preview}
                    alt="Uploaded preview"
                    className="max-h-48 rounded object-contain"
                  />
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      clearFile();
                    }}
                    className="absolute -right-2 -top-2 rounded-full bg-zinc-800 p-1 text-white hover:bg-zinc-700"
                    aria-label="Remove image"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ) : (
                <>
                  <Upload className="mb-2 h-8 w-8 text-zinc-400" />
                  <p className="text-sm font-medium text-zinc-600 dark:text-zinc-300">
                    Drag & drop or click to upload
                  </p>
                  <p className="text-xs text-zinc-400">
                    JPEG, PNG, WebP, BMP &mdash; Max 10 MB
                  </p>
                </>
              )}
            </div>

            {error && (
              <p id="file-error" className="text-sm text-red-600" role="alert">
                {error}
              </p>
            )}

            <Button
              onClick={handleSubmit}
              disabled={!file || mutation.isPending}
              className="w-full"
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                'Analyze Image'
              )}
            </Button>
          </CardContent>
        </Card>

        {mutation.isPending && (
          <Card>
            <CardContent className="space-y-3 p-6">
              <div className="h-4 w-3/4 animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" />
              <div className="h-4 w-2/3 animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" />
            </CardContent>
          </Card>
        )}

        {mutation.isError && (
          <Card>
            <CardContent className="flex items-center gap-3 p-6">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <div>
                <p className="font-medium text-red-600 dark:text-red-400">Analysis failed</p>
                <p className="text-sm text-zinc-500 dark:text-zinc-400">
                  {mutation.error?.message || 'An unexpected error occurred'}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="ml-auto"
              onClick={() => { if (file) mutation.mutate(file); }}
              >
                Retry
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </PageTransition>
  );
}

