import { useState } from 'react';
import { useAnalyzeText } from '@/hooks/use-scamshield';
import { useAnalysisNavigation } from '@/features/analysis/hooks/use-analysis-navigation';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { PageTransition } from '@/components/ui/page-transition';
import { ScrollText, Loader2, AlertCircle } from 'lucide-react';
import { textAnalysisSchema } from '@/utils/validation';
import { z } from 'zod';

export default function TextAnalysis() {
  const [text, setText] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const mutation = useAnalyzeText();
  const { navigateToResult } = useAnalysisNavigation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});
    try {
      const data = textAnalysisSchema.parse({ text });
      const result = await mutation.mutateAsync(data.text);
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

  return (
    <PageTransition>
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
<h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
          Text Analysis
        </h1>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Submit a message for scam detection analysis
        </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ScrollText className="h-5 w-5" />
              Message Input
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="text">Message Text</Label>
                <Textarea
                  id="text"
                  placeholder="Paste the message to analyze..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  aria-describedby={errors.text ? 'text-error' : undefined}
                  aria-invalid={!!errors.text}
                />
                {errors.text && (
                  <p id="text-error" className="text-sm text-red-600" role="alert">
                    {errors.text}
                  </p>
                )}
<p className="text-xs text-zinc-400" aria-live="polite">
                {text.length} / 10,000 characters
              </p>
              </div>
              <Button type="submit" disabled={mutation.isPending || !text.trim()}>
                {mutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  'Analyze Message'
                )}
              </Button>
            </form>
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
                onClick={() => mutation.mutate(text)}
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

