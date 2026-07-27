import { useState, useRef, useEffect } from 'react';
import { useAnalyzeText } from '@/hooks/use-scamshield';
import { useNetworkStatus } from '@/hooks/use-network-status';
import { useAnalysisNavigation } from '@/features/analysis/hooks/use-analysis-navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { ThinkingLoader } from '@/components/ui/thinking-loader';
import { PageTransition } from '@/components/ui/page-transition';
import { textAnalysisSchema } from '@/utils/validation';
import { z } from 'zod';
import { WifiOff, Shield, Lock } from 'lucide-react';

const THINKING_PHRASES = [
  'Reading your message...',
  'Extracting URLs, numbers, and patterns...',
  'Checking known scam markers...',
  'Looking for impersonation signs...',
  'Preparing your result...',
];

export default function TextAnalysis() {
  const [text, setText] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [detectedPaste, setDetectedPaste] = useState(false);
  const mutation = useAnalyzeText();
  const { navigateToResult } = useAnalysisNavigation();
  const isOnline = useNetworkStatus();
  const abortRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    try {
      const data = textAnalysisSchema.parse({ text });
      abortRef.current = new AbortController();
      const result = await mutation.mutateAsync({ text: data.text, signal: abortRef.current.signal });
      navigateToResult(result, false, data.text);
    } catch (err) {
      if (err instanceof z.ZodError) {
        const fieldErrors: Record<string, string> = {};
        for (const issue of err.issues) {
          fieldErrors[issue.path[0] as string] = issue.message;
        }
        setErrors(fieldErrors);
      }
    }
  };

  const handlePaste = () => {
    setDetectedPaste(true);
    setTimeout(() => setDetectedPaste(false), 2000);
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-xl space-y-6">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 dark:bg-emerald-900/20">
            <Shield className="h-6 w-6 text-emerald-500" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Check a message</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Paste any suspicious SMS, email, or chat.
          </p>
        </div>

        {!isOnline && (
          <Card>
            <CardContent className="flex items-center gap-3 py-4">
              <WifiOff className="h-5 w-5 text-amber-500 shrink-0" />
              <p className="text-sm text-zinc-600 dark:text-zinc-400">You&apos;re offline. Connect to the internet to analyse.</p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardContent className="space-y-4 pt-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="relative">
                <textarea
                  ref={inputRef}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  onPaste={handlePaste}
                  placeholder="Paste the message here..."
                  rows={6}
                  aria-invalid={!!errors.text}
                  aria-describedby={errors.text ? 'text-error' : undefined}
                  className="w-full resize-none rounded-xl border-0 bg-zinc-50 p-4 text-sm text-zinc-900 placeholder-zinc-400 transition-all duration-150 focus:bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:bg-zinc-800 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:bg-zinc-800"
                />
                {detectedPaste && (
                  <div className="absolute right-3 top-3 animate-slide-up">
                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
                      Pasted
                    </span>
                  </div>
                )}
              </div>
              {errors.text && (
                <p id="text-error" className="text-sm text-red-500" role="alert">{errors.text}</p>
              )}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="h-3 w-3 text-zinc-300 dark:text-zinc-600" />
                  <span className="text-xs text-zinc-400">Processed privately</span>
                </div>
                <Button type="submit" disabled={mutation.isPending || !text.trim() || !isOnline}>
                  {mutation.isPending ? (
                    <ThinkingLoader phrases={THINKING_PHRASES} />
                  ) : (
                    'Analyse'
                  )}
                </Button>
              </div>
            </form>
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
                    abortRef.current = new AbortController();
                    mutation.mutate({ text, signal: abortRef.current.signal });
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
