import { useState } from 'react';
import { CheckCircle2, ThumbsDown, ThumbsUp } from 'lucide-react';
import { submitFeedback, type FeedbackVerdict } from '@/features/feedback/feedback-api';

interface FeedbackWidgetProps {
  analysisId: string;
  predictedLabel?: string;
  onSubmitted?: (verdict: FeedbackVerdict) => void;
}

type SubmitStatus = 'idle' | 'submitting' | 'done' | 'error';

export function FeedbackWidget({ analysisId, predictedLabel, onSubmitted }: FeedbackWidgetProps) {
  const [status, setStatus] = useState<SubmitStatus>('idle');
  const [error, setError] = useState<string | null>(null);

  const handleVerdict = async (verdict: FeedbackVerdict) => {
    setStatus('submitting');
    setError(null);
    try {
      await submitFeedback({ analysis_id: analysisId, verdict });
      setStatus('done');
      onSubmitted?.(verdict);
    } catch (e) {
      setStatus('error');
      setError((e as Error).message || 'Could not send feedback. Please try again.');
    }
  };

  if (status === 'done') {
    return (
      <div className="glass rounded-2xl p-4 flex items-start gap-3" role="status">
        <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-success" />
        <div>
          <p className="text-sm font-semibold text-text-primary">Thank you — your feedback was recorded</p>
          <p className="mt-0.5 text-xs text-text-tertiary">
            Corrections are used to review the verdicts this model produces.
          </p>
        </div>
      </div>
    );
  }

  const buttonClass =
    'inline-flex h-9 items-center gap-1.5 rounded-lg border border-glass-border bg-glass px-3 text-xs font-medium text-text-secondary transition-all duration-200 hover:text-text-primary hover:bg-glass-hover disabled:opacity-40 disabled:cursor-not-allowed';

  return (
    <div className="glass rounded-2xl p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-text-primary">Was this verdict correct?</p>
          {predictedLabel && (
            <p className="mt-0.5 text-xs text-text-tertiary">
              Predicted label: <span className="font-mono text-text-secondary">{predictedLabel}</span>
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => void handleVerdict('correct')}
            disabled={status === 'submitting'}
            className={buttonClass}
          >
            <ThumbsUp className="h-3.5 w-3.5" /> Correct
          </button>
          <button
            type="button"
            onClick={() => void handleVerdict('incorrect')}
            disabled={status === 'submitting'}
            className={buttonClass}
          >
            <ThumbsDown className="h-3.5 w-3.5" /> Incorrect
          </button>
          <button
            type="button"
            onClick={() => void handleVerdict('unsure')}
            disabled={status === 'submitting'}
            className={buttonClass}
          >
            Not sure
          </button>
        </div>
      </div>
      {status === 'error' && (
        <p className="mt-3 text-xs text-danger" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

export default FeedbackWidget;
