import { useState, useCallback } from 'react';
import { PageTransition } from '@/components/ui/page-transition';
import { QUESTIONS, evaluateTriage, generateComplaintTemplate, CHAKSHU_URL, type TriageAnswers } from '@/lib/triage/digital-arrest';
import { Phone, Shield, AlertTriangle, Check, Copy, ExternalLink, ArrowLeft, LifeBuoy } from 'lucide-react';

export default function DigitalArrestTriage() {
  const [answers, setAnswers] = useState<TriageAnswers>({ q1: null, q2: null, q3: null, q4: null });
  const [step, setStep] = useState(0);
  const [showResult, setShowResult] = useState(false);

  // Complaint template details (only for ALREADY_PAID)
  const [amount, setAmount] = useState('');
  const [account, setAccount] = useState('');
  const [callerPhone, setCallerPhone] = useState('');
  const [timeApprox, setTimeApprox] = useState('');
  const [whatHappened, setWhatHappened] = useState('');
  const [copied, setCopied] = useState(false);

  const currentQ = QUESTIONS[step];
  const result = showResult ? evaluateTriage(answers) : null;

  const handleAnswer = useCallback((value: boolean) => {
    const qid = QUESTIONS[step].id;
    const next: TriageAnswers = { ...answers, [qid]: value };
    setAnswers(next);

    if (step < QUESTIONS.length - 1) {
      setStep((s) => s + 1);
    } else {
      setShowResult(true);
    }
  }, [answers, step]);

  const handleBack = useCallback(() => {
    if (showResult) {
      setShowResult(false);
      return;
    }
    if (step > 0) setStep((s) => s - 1);
  }, [showResult, step]);

  const handleReset = useCallback(() => {
    setAnswers({ q1: null, q2: null, q3: null, q4: null });
    setStep(0);
    setShowResult(false);
    setAmount('');
    setAccount('');
    setCallerPhone('');
    setTimeApprox('');
    setWhatHappened('');
    setCopied(false);
  }, []);

  const complaintText = generateComplaintTemplate({
    amount: amount || undefined,
    accountOrUpi: account || undefined,
    callerPhone: callerPhone || undefined,
    timeApprox: timeApprox || undefined,
    whatHappened: whatHappened || undefined,
  });

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(complaintText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback: select text
      setCopied(false);
    }
  }, [complaintText]);

  const handleChakshu = useCallback(() => {
    window.open(CHAKSHU_URL, '_blank', 'noopener,noreferrer');
  }, []);

  return (
    <PageTransition>
      <div className="mx-auto max-w-2xl px-6 py-8 sm:py-12">
        {/* Header */}
        <div className="mb-6 flex items-center gap-3">
          <button
            onClick={handleBack}
            disabled={step === 0 && !showResult}
            className="flex h-10 w-10 items-center justify-center rounded-xl glass text-text-tertiary hover:text-text-secondary disabled:opacity-30"
            aria-label="Go back"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-text-primary sm:text-2xl">Digital Arrest Check</h1>
            <p className="text-sm text-text-tertiary">Calm, private, on your phone — 4 quick questions</p>
          </div>
        </div>

        {/* Progress — one question per screen */}
        {!showResult && (
          <div className="mb-6 flex items-center gap-2">
            <div className="flex-1 flex gap-1.5">
              {QUESTIONS.map((_, i) => (
                <div
                  key={i}
                  className={`h-2 flex-1 rounded-full transition-colors ${i < step ? 'bg-accent' : i === step ? 'bg-accent/60 animate-pulse' : 'bg-glass-border'}`}
                />
              ))}
            </div>
            <span className="text-xs tabular-nums text-text-tertiary"> {step + 1} / {QUESTIONS.length}</span>
          </div>
        )}

        {/* Question screens */}
        {!showResult ? (
          <div className="glass rounded-3xl p-8 sm:p-10 animate-scale-in">
            <div className="mb-8">
              <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-accent/10">
                <LifeBuoy className="h-8 w-8 text-accent" />
              </div>
              <h2 className="text-center text-xl font-bold leading-tight text-text-primary sm:text-2xl">
                {currentQ.text}
              </h2>
              {currentQ.helper && (
                <p className="mt-3 text-center text-sm leading-relaxed text-text-secondary/80">
                  {currentQ.helper}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => handleAnswer(true)}
                className="flex h-20 items-center justify-center rounded-2xl border-2 border-accent/30 bg-accent/10 text-lg font-bold text-accent transition hover:bg-accent/15 active:scale-[0.98]"
                aria-label="Yes"
              >
                Yes
              </button>
              <button
                onClick={() => handleAnswer(false)}
                className="flex h-20 items-center justify-center rounded-2xl border-2 border-glass-border bg-glass text-lg font-bold text-text-primary transition hover:bg-glass-hover active:scale-[0.98]"
                aria-label="No"
              >
                No
              </button>
            </div>

            <p className="mt-6 text-center text-xs text-text-tertiary">
              Take your time. There is no rush — a real officer will never punish you for pausing.
            </p>
          </div>
        ) : result ? (
          <div className="space-y-6">
            {/* ALREADY_PAID — Call 1930 prominently BEFORE anything else */}
            {result.outcome === 'ALREADY_PAID_ACT_NOW' && (
              <div className="rounded-3xl border-2 border-danger/30 bg-danger/10 p-8 text-center animate-scale-in">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-danger text-white animate-pulse">
                  <Phone className="h-8 w-8" />
                </div>
                <h2 className="text-2xl font-bold text-danger">Call 1930 now</h2>
                <p className="mt-2 text-sm font-medium text-text-primary">India’s 24×7 cybercrime helpline — every minute counts to freeze the transaction</p>
                <a
                  href="tel:1930"
                  className="mt-6 inline-flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-danger px-8 text-lg font-bold text-white shadow-lg transition hover:bg-danger/90 active:scale-[0.98] sm:w-auto"
                >
                  <Phone className="h-5 w-5" />
                  Call 1930
                </a>
                <p className="mt-3 text-xs text-text-tertiary">If you can’t call, ask a family member to call for you right now.</p>
              </div>
            )}

            {/* Outcome card */}
            <div
              className={`rounded-3xl p-8 animate-glass-enter ${
                result.severity === 'critical'
                  ? 'glass border-danger/20 bg-danger/5'
                  : result.severity === 'warning'
                  ? 'glass border-warning/20 bg-warning/5'
                  : 'glass border-success/20 bg-success/5'
              }`}
            >
              <div className="flex items-start gap-4">
                <div
                  className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${
                    result.severity === 'critical'
                      ? 'bg-danger/15 text-danger'
                      : result.severity === 'warning'
                      ? 'bg-warning/15 text-warning'
                      : 'bg-success/15 text-success'
                  }`}
                >
                  {result.severity === 'critical' ? (
                    <AlertTriangle className="h-6 w-6" />
                  ) : result.severity === 'warning' ? (
                    <Shield className="h-6 w-6" />
                  ) : (
                    <Check className="h-6 w-6" />
                  )}
                </div>
                <div>
                  <h2 className="text-xl font-bold text-text-primary">{result.title}</h2>
                  <p className="mt-2 text-base leading-relaxed text-text-secondary">{result.message}</p>
                </div>
              </div>

              <ul className="mt-6 space-y-2">
                {result.actions.map((a, i) => (
                  <li key={i} className="flex items-start gap-3 rounded-xl bg-glass border border-glass-border p-3">
                    <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-accent" />
                    <span className="text-sm text-text-secondary">{a}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Complaint template — only for ALREADY_PAID */}
            {result.outcome === 'ALREADY_PAID_ACT_NOW' && (
              <div className="glass rounded-2xl p-6 animate-slide-up">
                <h3 className="text-sm font-semibold text-text-primary">Complaint template for cybercrime.gov.in or reading aloud to 1930</h3>
                <p className="mt-1 text-xs text-text-tertiary">Fill what you can — even partial details help. Copy and paste when filing.</p>

                <div className="mt-4 grid gap-3">
                  <label className="text-xs font-medium text-text-secondary">
                    Amount sent
                    <input value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="e.g., Rs 50,000" className="mt-1 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm" />
                  </label>
                  <label className="text-xs font-medium text-text-secondary">
                    Sent to (account / UPI ID / phone)
                    <input value={account} onChange={(e) => setAccount(e.target.value)} placeholder="e.g., ramesh@okaxis or 98765XXXXX" className="mt-1 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm" />
                  </label>
                  <label className="text-xs font-medium text-text-secondary">
                    Caller’s phone number
                    <input value={callerPhone} onChange={(e) => setCallerPhone(e.target.value)} placeholder="e.g., +91 98XXXX XXXXX" className="mt-1 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm" />
                  </label>
                  <label className="text-xs font-medium text-text-secondary">
                    Approximate time
                    <input value={timeApprox} onChange={(e) => setTimeApprox(e.target.value)} placeholder="e.g., 3 Sep 2026 around 2:30 PM" className="mt-1 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm" />
                  </label>
                  <label className="text-xs font-medium text-text-secondary">
                    What happened (brief)
                    <textarea value={whatHappened} onChange={(e) => setWhatHappened(e.target.value)} placeholder="Who called, what they claimed, that they said digital arrest..." rows={3} className="mt-1 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm" />
                  </label>
                </div>

                <div className="mt-4 rounded-xl bg-zinc-900 p-4">
                  <pre className="whitespace-pre-wrap text-xs leading-relaxed text-zinc-100">{complaintText}</pre>
                </div>

                <button
                  onClick={handleCopy}
                  className="mt-4 inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-accent px-5 text-sm font-semibold text-white transition hover:bg-accent/90 sm:w-auto"
                >
                  <Copy className="h-4 w-4" />
                  {copied ? 'Copied!' : 'Copy details'}
                </button>
              </div>
            )}

            {/* Chakshu */}
            <div className="glass rounded-2xl p-6 animate-slide-up">
              <h3 className="text-sm font-semibold text-text-primary">Report to Chakshu</h3>
              <p className="mt-1 text-xs text-text-tertiary">Also report the number on Sanchar Saathi (Department of Telecom) to help block it for others.</p>
              <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                <button
                  onClick={handleChakshu}
                  className="inline-flex h-11 items-center justify-center gap-2 rounded-xl border border-glass-border bg-glass px-5 text-sm font-medium text-text-primary hover:bg-glass-hover"
                >
                  <ExternalLink className="h-4 w-4" />
                  Report to Chakshu — sancharsaathi.gov.in/sfc
                </button>
                <button
                  onClick={handleCopy}
                  className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-glass border border-glass-border px-5 text-sm text-text-secondary hover:text-text-primary"
                >
                  <Copy className="h-4 w-4" />
                  Copy details for Chakshu
                </button>
              </div>
              <p className="mt-2 text-xs text-text-tertiary">Chakshu does not support prefill via URL parameters, so use “Copy details” and paste there.</p>
            </div>

            <button
              onClick={handleReset}
              className="w-full rounded-2xl border border-glass-border bg-glass py-4 text-sm font-medium text-text-secondary hover:text-text-primary"
            >
              Start over
            </button>
          </div>
        ) : null}
      </div>
    </PageTransition>
  );
}
