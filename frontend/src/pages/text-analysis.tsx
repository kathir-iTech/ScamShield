import { useState, useRef, useEffect } from 'react';
import { useAnalyzeText } from '@/hooks/use-scamshield';
import { useNetworkStatus } from '@/hooks/use-network-status';
import { useAnalysisNavigation } from '@/features/analysis/hooks/use-analysis-navigation';
import { GlassInput } from '@/components/ui/glass-input';
import { PipelineLoader } from '@/components/ui/pipeline-loader';
import { PageTransition } from '@/components/ui/page-transition';
import { textAnalysisSchema } from '@/utils/validation';
import { z } from 'zod';
import { Lock, Shield } from 'lucide-react';

export default function TextAnalysis() {
  const [text, setText] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showPipeline, setShowPipeline] = useState(false);
  const mutation = useAnalyzeText();
  const { navigateToResult } = useAnalysisNavigation();
  const isOnline = useNetworkStatus();
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    try {
      const data = textAnalysisSchema.parse({ text });
      abortRef.current = new AbortController();
      setShowPipeline(true);
      const result = await mutation.mutateAsync({ text: data.text, signal: abortRef.current.signal });
      setShowPipeline(false);
      navigateToResult(result, false, data.text);
    } catch (err) {
      setShowPipeline(false);
      if (err instanceof z.ZodError) {
        const fieldErrors: Record<string, string> = {};
        for (const issue of err.issues) {
          fieldErrors[issue.path[0] as string] = issue.message;
        }
        setErrors(fieldErrors);
      }
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
            Check a message
          </h1>
          <p className="mt-2 text-text-secondary/70">
            Paste any suspicious SMS, email, or chat.
          </p>
        </div>

        {!isOnline ? (
          <div className="mb-6 glass rounded-2xl p-4 flex items-center gap-3 animate-slide-up border border-success/20 bg-success/5">
            <Shield className="h-5 w-5 shrink-0 text-success" />
            <div>
              <p className="text-sm font-medium text-text-primary">Offline-ready</p>
              <p className="text-xs text-text-secondary">Text analysis runs locally on your device — no internet needed.</p>
            </div>
          </div>
        ) : (
          <div className="mb-6 glass rounded-2xl p-4 flex items-center gap-3 animate-slide-up border border-glass-border">
            <Lock className="h-4 w-4 shrink-0 text-text-tertiary" />
            <p className="text-xs text-text-tertiary">Text analysis runs 100% locally on your device. No data leaves your phone.</p>
          </div>
        )}

        {showPipeline ? (
          <div className="glass rounded-2xl overflow-hidden animate-scale-in">
            <div className="p-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/10">
                  <Shield className="h-4 w-4 text-accent" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-text-primary">Analysing message</p>
                  <p className="text-xs text-text-tertiary">AI is reviewing the content</p>
                </div>
              </div>
              <PipelineLoader />
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="glass rounded-2xl overflow-hidden">
              <div className="p-5 sm:p-6">
                <GlassInput
                  value={text}
                  onChange={setText}
                  onSubmit={() => document.querySelector<HTMLButtonElement>('button[type=submit]')?.click()}
                />
                {errors.text && (
                  <p className="mt-3 text-sm text-danger" role="alert">{errors.text}</p>
                )}
              </div>
              <div className="flex items-center justify-between border-t border-glass-border px-5 py-4 sm:px-6">
                <div className="flex items-center gap-2">
                  <Lock className="h-3 w-3 text-text-tertiary" />
                  <span className="text-xs text-text-tertiary">Processed privately</span>
                </div>
                <button
                  type="submit"
                  disabled={mutation.isPending || !text.trim()}
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
          </form>
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
                  abortRef.current = new AbortController();
                  mutation.mutate({ text, signal: abortRef.current.signal });
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
