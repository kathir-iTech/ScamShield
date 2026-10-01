import { useState, type FormEvent } from 'react';
import { Link, useLocation, useSearchParams } from 'react-router-dom';
import { PageTransition } from '@/components/ui/page-transition';
import { useCurrentAnalysis } from '@/features/analysis/context/analysis-context';
import { submitFeedback, type FeedbackVerdict } from '@/features/feedback';
import { CheckCircle2, MessageSquare, Send } from 'lucide-react';

const VERDICTS: { value: FeedbackVerdict; label: string }[] = [
  { value: 'correct', label: 'Correct' },
  { value: 'incorrect', label: 'Incorrect' },
  { value: 'unsure', label: 'Unsure' },
];

const CORRECTED_LABELS = [
  'Legitimate message',
  'Bank KYC Scam',
  'Lottery Scam',
  'Job Scam',
  'UPI Scam',
  'Investment Scam',
  'Courier Scam',
  'Government Scheme',
  'Electricity Bill',
  'Customs Scam',
  'Loan Scam',
  'Fake Customer Care',
  'QR Code Scam',
  'Crypto Scam',
  'Other',
];

type SubmitStatus = 'idle' | 'submitting' | 'success' | 'error';

export default function Feedback() {
  const location = useLocation();
  const [params] = useSearchParams();
  const current = useCurrentAnalysis();

  const stateAnalysisId = (location.state as { analysisId?: string } | null)?.analysisId;
  const analysisId = params.get('analysis_id') ?? stateAnalysisId ?? current?.id ?? '';

  const [verdict, setVerdict] = useState<FeedbackVerdict | ''>('');
  const [correctedLabel, setCorrectedLabel] = useState('');
  const [note, setNote] = useState('');
  const [status, setStatus] = useState<SubmitStatus>('idle');
  const [message, setMessage] = useState<string | null>(null);

  const noteRequired = verdict === 'incorrect';
  const noteLabel = noteRequired ? 'What was wrong?' : 'Note (optional)';

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!verdict) {
      setStatus('error');
      setMessage('Tell us whether the verdict was correct before sending.');
      return;
    }
    if (noteRequired && !note.trim()) {
      setStatus('error');
      setMessage('Tell us what was wrong so the verdict can be corrected.');
      return;
    }
    setStatus('submitting');
    setMessage(null);
    try {
      await submitFeedback({
        analysis_id: analysisId,
        verdict,
        corrected_label: correctedLabel === 'Other' ? '' : correctedLabel,
        note: note.trim(),
      });
      setStatus('success');
    } catch (err) {
      setStatus('error');
      setMessage((err as Error).message || 'Could not send feedback. Please try again.');
    }
  };

  if (status === 'success') {
    return (
      <PageTransition>
        <div className="mx-auto max-w-xl px-6 py-16 sm:py-20">
          <div className="glass rounded-2xl p-8 text-center animate-scale-in" role="status">
            <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-success/10">
              <CheckCircle2 className="h-7 w-7 text-success" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-text-primary">Thank you</h1>
            <p className="mt-2 text-sm text-text-secondary">
              Your feedback was recorded{analysisId ? ' against this analysis' : ''}. It is reviewed before it changes
              any scoring or rules.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              <button
                type="button"
                onClick={() => {
                  setStatus('idle');
                  setVerdict('');
                  setCorrectedLabel('');
                  setNote('');
                  setMessage(null);
                }}
                className="inline-flex h-11 items-center rounded-xl border border-glass-border bg-glass px-5 text-sm font-medium text-text-primary hover:bg-glass-hover"
              >
                Send another
              </button>
              <Link
                to="/"
                className="inline-flex h-11 items-center rounded-xl bg-accent px-5 text-sm font-semibold text-white hover:bg-accent/90"
              >
                Back to home
              </Link>
            </div>
          </div>
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="mx-auto max-w-xl px-6 py-16 sm:py-20">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass">
            <MessageSquare className="h-6 w-6 text-accent" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">Feedback</h1>
          <p className="mt-2 text-sm text-text-secondary/70">
            Was a verdict wrong? Tell us and we will review the case behind it.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="glass rounded-2xl p-7 animate-slide-up" noValidate>
          <fieldset className="mb-5">
            <legend className="text-xs font-semibold uppercase tracking-wide text-text-tertiary">
              Was the verdict correct?
            </legend>
            <div className="mt-3 flex flex-wrap gap-2">
              {VERDICTS.map((option) => (
                <label
                  key={option.value}
                  className={`inline-flex h-10 cursor-pointer items-center gap-2 rounded-xl border px-4 text-sm font-medium transition-all duration-200 ${
                    verdict === option.value
                      ? 'border-accent/40 bg-accent/10 text-accent'
                      : 'border-glass-border bg-glass text-text-secondary hover:text-text-primary'
                  }`}
                >
                  <input
                    type="radio"
                    name="verdict"
                    value={option.value}
                    checked={verdict === option.value}
                    onChange={() => {
                      setVerdict(option.value);
                      setStatus('idle');
                      setMessage(null);
                    }}
                    className="sr-only"
                  />
                  {option.label}
                </label>
              ))}
            </div>
          </fieldset>

          <label className="mb-5 block text-xs font-medium text-text-secondary">
            Corrected label (optional)
            <select
              value={correctedLabel}
              onChange={(e) => setCorrectedLabel(e.target.value)}
              disabled={verdict === 'correct'}
              className="mt-1.5 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm text-text-primary focus:outline-none disabled:opacity-40"
            >
              <option value="">Leave unchanged</option>
              {CORRECTED_LABELS.map((label) => (
                <option key={label} value={label}>
                  {label}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-xs font-medium text-text-secondary">
            {noteLabel}
            <textarea
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={4}
              required={noteRequired}
              placeholder={
                noteRequired
                  ? 'What did the analysis get wrong? Include the real sender, category, or context if you know it.'
                  : 'Anything else we should know about this message.'
              }
              className="mt-1.5 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none"
            />
          </label>

          <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-text-tertiary">
              {analysisId ? (
                <>
                  Linked to analysis <span className="font-mono text-text-secondary">{analysisId}</span>
                </>
              ) : (
                'Not linked to a specific analysis'
              )}
            </p>
            <button
              type="submit"
              disabled={status === 'submitting'}
              className="inline-flex h-11 items-center gap-2 rounded-xl bg-accent px-5 text-sm font-semibold text-white hover:bg-accent/90 disabled:opacity-40"
            >
              <Send className="h-4 w-4" />
              {status === 'submitting' ? 'Sending…' : 'Send feedback'}
            </button>
          </div>

          {status === 'error' && message && (
            <p className="mt-4 rounded-xl border border-danger/30 bg-danger/10 p-3 text-sm text-danger" role="alert">
              {message}
            </p>
          )}
        </form>
      </div>
    </PageTransition>
  );
}
