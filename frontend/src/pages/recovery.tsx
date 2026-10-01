import { useState, useEffect, useCallback, useMemo } from 'react';
import { PageTransition } from '@/components/ui/page-transition';
import { useCurrentAnalysis } from '@/features/analysis/context/analysis-context';
import { buildRecoveryPackSync, computeEvidenceHash, type RecoveryDetails } from '@/lib/recovery/pack';
import { CHAKSHU_URL } from '@/lib/triage/digital-arrest';
import { Phone, Copy, Shield, ExternalLink, FileText, AlertTriangle, Check, Printer } from 'lucide-react';

export default function Recovery() {
  const current = useCurrentAnalysis();
  const analysis = current?.result || null;
  const inputText = current?.inputText || '';

  // Auto-fill from analysis entities / UPI inspector
  const autoAccount = useMemo(() => {
    const ups = (analysis as unknown as { upi_intent?: { pa?: string } | null })?.upi_intent?.pa;
    if (ups) return ups;
    const upiEnt = analysis?.entities.find((e) => e.type === 'upi_id' || e.type === 'upi_intent');
    if (upiEnt) return upiEnt.value;
    return '';
  }, [analysis]);
  const autoPhone = useMemo(() => {
    const ph = analysis?.entities.find((e) => e.type === 'phone_indian' || e.type === 'phone_international' || e.type === 'phone');
    return ph?.value || '';
  }, [analysis]);
  const autoAmount = useMemo(() => {
    const ups = (analysis as unknown as { upi_intent?: { amount?: number | null } | null })?.upi_intent;
    if (ups?.amount != null) return `Rs ${ups.amount}`;
    const cur = analysis?.entities.find((e) => e.type === 'currency_amount');
    return cur?.value || '';
  }, [analysis]);

  const [amount, setAmount] = useState(autoAmount);
  const [account, setAccount] = useState(autoAccount);
  const [callerPhone, setCallerPhone] = useState(autoPhone);
  const [timeApprox, setTimeApprox] = useState('');
  const [whatHappened, setWhatHappened] = useState(inputText.slice(0, 400));
  const [txnId, setTxnId] = useState('');
  const [copied, setCopied] = useState(false);
  const [hash, setHash] = useState<string | null>(null);

  // Update auto-fills when analysis changes (first load only)
  useEffect(() => {
    if (autoAccount && !account) setAccount(autoAccount);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoAccount]);
  useEffect(() => {
    if (autoPhone && !callerPhone) setCallerPhone(autoPhone);
  }, [autoPhone]);
  useEffect(() => {
    if (autoAmount && !amount) setAmount(autoAmount);
  }, [autoAmount]);
  useEffect(() => {
    if (inputText && !whatHappened) setWhatHappened(inputText.slice(0, 400));
  }, [inputText, whatHappened]);

  const details: RecoveryDetails = { amount: amount || undefined, accountOrUpi: account || undefined, callerPhone: callerPhone || undefined, timeApprox: timeApprox || undefined, whatHappened: whatHappened || undefined, transactionId: txnId || undefined };
  const pack = useMemo(() => buildRecoveryPackSync(details, analysis), [details, analysis]);

  useEffect(() => {
    computeEvidenceHash(pack.hashInput).then(setHash);
  }, [pack.hashInput]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(pack.cybercrimeDraft + '\n\n---\nEvidence hash (SHA-256 of this pack): ' + (hash || '') + '\nGenerated: ' + pack.generatedAt + '\n---\n' + pack.evidenceAppendix.join('\n'));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  }, [pack, hash]);

  const handlePrint = useCallback(() => {
    const w = window.open('', '_blank');
    if (!w) return;
    w.document.write(`<!DOCTYPE html><html><head><title>Recovery Pack - Wary</title><style>body{font-family:system-ui,sans-serif;max-width:800px;margin:40px auto;padding:0 20px;line-height:1.6;color:#1a1a2e}h1{font-size:22px;border-bottom:2px solid #059669;padding-bottom:8px}h2{font-size:16px;color:#059669;margin-top:28px}pre{white-space:pre-wrap;background:#f4f4f5;padding:16px;border-radius:8px;font-size:13px}.meta{color:#666;font-size:12px}</style></head><body><h1>Recovery Pack — ${pack.header}</h1><p class="meta">Generated locally on your phone on ${pack.generatedAt} — no data sent to server<br>Hash: ${hash || 'computing...'}<br>Chakshu: ${CHAKSHU_URL}</p><h2>What to do now (1930)</h2><ol>${pack.steps1930.map((s) => `<li>${s}</li>`).join('')}</ol><h2>Copy for 1930 / cybercrime.gov.in</h2><pre>${pack.cybercrimeDraft.replace(/</g,'&lt;')}</pre><h2>Evidence appendix</h2><pre>${pack.evidenceAppendix.join('\n').replace(/</g,'&lt;')}</pre><hr><p class="meta">Evidence hash (SHA-256 of details+evidence, for integrity, not anonymity): ${hash || ''}<br>This pack was generated 100% locally. Verify hash by recomputing on the same inputs.</p></body></html>`);
    w.document.close();
    w.focus();
    setTimeout(() => w.print(), 300);
  }, [pack, hash]);

  return (
    <PageTransition>
      <div className="mx-auto max-w-3xl px-6 py-8 sm:py-12">
        <div className="mb-6">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">Recovery Pack — 60 seconds to 1930</h1>
          <p className="mt-2 text-sm text-text-secondary">Fill what you can. Everything stays on your phone. Copy one text for both the 1930 call and cybercrime.gov.in filing.</p>
          <p className="mt-1 text-xs text-text-tertiary">For students: most losses here are job-task, investment, digital-arrest, and UPI-collect. This pack is built for that.</p>
        </div>

        {!analysis && (
          <div className="mb-6 rounded-2xl border border-warning/30 bg-warning/10 p-4 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 shrink-0 text-warning mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-text-primary">No analysis loaded</p>
              <p className="text-xs text-text-secondary">You can still fill and copy this pack manually, but auto-fill works best after you analyse the message/QR first. <a href="/analyze/text" className="underline text-accent">Analyse a message</a> then return here.</p>
            </div>
          </div>
        )}

        {analysis && (
          <div className="mb-6 glass rounded-2xl p-4">
            <p className="text-xs font-semibold text-text-tertiary uppercase tracking-wide">From your last analysis</p>
            <p className="mt-1 text-sm text-text-primary">{pack.header}</p>
            <p className="text-xs text-text-secondary">{analysis.summary}</p>
            <p className="mt-1 text-xs text-text-tertiary">Indicators: {analysis.detected_indicators.slice(0, 4).join(', ') || 'none'} · Entities: {analysis.entities.length}</p>
          </div>
        )}

        {/* 1930 call banner */}
        <div className="rounded-3xl border-2 border-danger/30 bg-danger/10 p-6 text-center mb-6">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-danger text-white animate-pulse">
            <Phone className="h-7 w-7" />
          </div>
          <h2 className="text-xl font-bold text-danger">Call 1930 now — every minute counts</h2>
          <p className="mt-1 text-xs text-text-secondary">India’s 24×7 cybercrime helpline. Keep the line open. Read the draft below.</p>
          <a href="tel:1930" className="mt-4 inline-flex h-12 w-full items-center justify-center gap-2 rounded-2xl bg-danger px-8 text-base font-bold text-white shadow hover:bg-danger/90 sm:w-auto">
            <Phone className="h-5 w-5" /> Call 1930
          </a>
          <p className="mt-2 text-xs text-text-tertiary">If you can’t call, ask a trusted person to call for you right now.</p>
        </div>

        {/* Form */}
        <div className="glass rounded-2xl p-6 mb-6">
          <h3 className="text-sm font-semibold text-text-primary">Your incident — fill what you can</h3>
          <p className="text-xs text-text-tertiary">Auto-filled where possible from your analysis. You can edit. Nothing is uploaded.</p>
          <div className="mt-4 grid gap-3">
            <label className="text-xs font-medium text-text-secondary">
              Amount involved
              <input value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="e.g., Rs 50,000 or Rs 2,000 + Rs 30,000" className="mt-1 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm" />
            </label>
            <label className="text-xs font-medium text-text-secondary">
              Sent to (UPI / account / phone / QR payee)
              <input value={account} onChange={(e) => setAccount(e.target.value)} placeholder="e.g., ramesh@okaxis or 98765XXXXX / QR payee" className="mt-1 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm font-mono" />
            </label>
            <label className="text-xs font-medium text-text-secondary">
              Transaction ID / UTR (if any)
              <input value={txnId} onChange={(e) => setTxnId(e.target.value)} placeholder="e.g., 4098XXXX or UPI ref" className="mt-1 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm font-mono" />
            </label>
            <label className="text-xs font-medium text-text-secondary">
              Caller / sender phone
              <input value={callerPhone} onChange={(e) => setCallerPhone(e.target.value)} placeholder="e.g., +91 98XXXX XXXXX" className="mt-1 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm" />
            </label>
            <label className="text-xs font-medium text-text-secondary">
              Time of incident
              <input value={timeApprox} onChange={(e) => setTimeApprox(e.target.value)} placeholder="e.g., 4 May 2026 around 2:30 PM" className="mt-1 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm" />
            </label>
            <label className="text-xs font-medium text-text-secondary">
              What happened (brief — will be in complaint)
              <textarea value={whatHappened} onChange={(e) => setWhatHappened(e.target.value)} placeholder="Who contacted you, what they said, QR/link, that you paid or were asked to pay..." rows={4} className="mt-1 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm" />
            </label>
          </div>
        </div>

        {/* Steps */}
        <div className="glass rounded-2xl p-6 mb-6">
          <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2"><Shield className="h-4 w-4 text-accent" /> What to do now</h3>
          <ol className="mt-3 space-y-2">
            {pack.steps1930.map((s, i) => (
              <li key={i} className="flex gap-3 rounded-xl bg-glass border border-glass-border p-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent text-xs font-bold text-white">{i + 1}</span>
                <span className="text-sm text-text-secondary">{s}</span>
              </li>
            ))}
          </ol>
        </div>

        {/* Draft */}
        <div className="glass rounded-2xl p-6 mb-6">
          <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2"><FileText className="h-4 w-4 text-accent" /> Copy for 1930 / cybercrime.gov.in</h3>
          <p className="mt-1 text-xs text-text-tertiary">One text for both. Paste at cybercrime.gov.in or read to the 1930 operator. Includes evidence appendix + hash.</p>
          <div className="mt-3 rounded-xl bg-zinc-900 p-4">
            <pre className="whitespace-pre-wrap text-xs leading-relaxed text-zinc-100">{pack.cybercrimeDraft}</pre>
          </div>
          <div className="mt-3 rounded-xl bg-glass border border-glass-border p-3">
            <p className="text-xs font-semibold text-text-primary">Evidence appendix (from local analysis)</p>
            <pre className="mt-1 whitespace-pre-wrap text-xs text-text-secondary">{pack.evidenceAppendix.join('\n')}</pre>
          </div>
          <div className="mt-3 rounded-xl bg-success/10 border border-success/20 p-3">
            <p className="text-xs font-semibold text-success flex items-center gap-1.5"><Check className="h-3.5 w-3.5" /> Integrity hash</p>
            <p className="mt-1 font-mono text-xs break-all text-text-secondary">{hash || 'computing...'}</p>
            <p className="text-xs text-text-tertiary mt-1">SHA-256 of details + evidence (integrity, not anonymity). Recompute gives same hash for same inputs. Low-entropy message templates are NOT anonymized by hash alone — do not share this hash as “anonymous” proof.</p>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <button onClick={handleCopy} className="inline-flex h-11 items-center gap-2 rounded-xl bg-accent px-5 text-sm font-semibold text-white hover:bg-accent/90">
              <Copy className="h-4 w-4" /> {copied ? 'Copied!' : 'Copy pack'}
            </button>
            <button onClick={handlePrint} className="inline-flex h-11 items-center gap-2 rounded-xl border border-glass-border bg-glass px-5 text-sm font-medium text-text-primary hover:bg-glass-hover">
              <Printer className="h-4 w-4" /> Print / Save PDF
            </button>
          </div>
        </div>

        {/* Chakshu */}
        <div className="glass rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-text-primary">Also report the number</h3>
          <p className="text-xs text-text-tertiary">Help block it for others via DoT’s Chakshu (Sanchar Saathi). Copy the same pack and paste there.</p>
          <div className="mt-3 flex flex-col gap-2 sm:flex-row">
            <a href={CHAKSHU_URL} target="_blank" rel="noopener noreferrer" className="inline-flex h-11 items-center justify-center gap-2 rounded-xl border border-glass-border bg-glass px-5 text-sm font-medium text-text-primary hover:bg-glass-hover">
              <ExternalLink className="h-4 w-4" /> Report to Chakshu — sancharsaathi.gov.in/sfc
            </a>
            <button onClick={handleCopy} className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-glass border border-glass-border px-5 text-sm text-text-secondary hover:text-text-primary">
              <Copy className="h-4 w-4" /> Copy pack for Chakshu
            </button>
          </div>
          <p className="mt-2 text-xs text-text-tertiary">Chakshu does not support URL prefill, so paste after opening.</p>
        </div>

        <p className="mt-6 text-center text-xs text-text-tertiary">This pack is generated 100% locally. No data was sent to a server. For verification, keep screenshots and transaction receipts.</p>
      </div>
    </PageTransition>
  );
}
