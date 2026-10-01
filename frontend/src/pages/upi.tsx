import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { PageTransition } from '@/components/ui/page-transition';
import { UpiInspectorCard } from '@/features/analysis/components/upi-inspector-card';
import { parseUpiIntents } from '@/lib/scamshield/upi-intent';
import { IndianRupee, ScanLine, Trash2 } from 'lucide-react';

export default function UpiInspectorPage() {
  const [text, setText] = useState('');

  const intents = useMemo(() => {
    const trimmed = text.trim();
    if (!trimmed) return [];
    try {
      return parseUpiIntents(trimmed);
    } catch {
      return [];
    }
  }, [text]);

  const primary = intents[0] ?? null;

  return (
    <PageTransition>
      <div className="mx-auto max-w-3xl px-6 py-8 sm:py-12">
        <div className="mb-6">
          <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">UPI Inspector</h1>
          <p className="mt-2 text-sm text-text-secondary">
            Paste a UPI string, QR payload, or a message containing a UPI ID. We tell you whether scanning it means you
            pay or you receive — before you tap anything.
          </p>
          <p className="mt-1 text-xs text-text-tertiary">
            Parsed entirely on your device. Nothing you paste here is uploaded.
          </p>
        </div>

        <div className="glass rounded-2xl overflow-hidden">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={4}
            placeholder="upi://pay?pa=name@okaxis&amp;pn=Name&amp;am=500 — or paste a VPA like name@ybl"
            className="w-full resize-none bg-transparent px-5 py-4 text-sm font-mono text-text-primary placeholder:text-text-tertiary focus:outline-none"
            aria-label="UPI string or QR payload"
          />
          <div className="flex items-center justify-between border-t border-glass-border px-4 py-3">
            <button
              type="button"
              onClick={() => setText('')}
              disabled={!text}
              className="inline-flex h-9 items-center gap-1.5 rounded-lg px-3 text-xs text-text-tertiary hover:text-text-secondary disabled:opacity-30"
              aria-label="Clear UPI input"
            >
              <Trash2 className="h-4 w-4" /> Clear
            </button>
            <span className="inline-flex items-center gap-1.5 text-xs text-text-tertiary">
              <ScanLine className="h-4 w-4" />
              {text.trim() ? `${intents.length} UPI signal${intents.length === 1 ? '' : 's'} found` : 'Waiting for input'}
            </span>
          </div>
        </div>

        {text.trim() && intents.length === 0 && (
          <div className="mt-4 rounded-2xl border border-warning/30 bg-warning/10 p-4">
            <p className="text-sm font-semibold text-text-primary">No UPI handle found</p>
            <p className="mt-1 text-xs text-text-secondary">
              Check that you pasted the full <span className="font-mono">upi://pay?pa=...</span> payload or a complete
              VPA such as <span className="font-mono">name@okaxis</span>. Partial handles are ignored on purpose.
            </p>
          </div>
        )}

        {primary && (
          <div className="mt-6">
            <UpiInspectorCard intent={primary} intents={intents} />
          </div>
        )}

        {intents.length > 1 && (
          <div className="glass mt-4 rounded-2xl p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-text-tertiary">All UPI handles found</p>
            <ul className="mt-2 space-y-1.5">
              {intents.map((intent, i) => (
                <li
                  key={`${intent.pa}-${i}`}
                  className="flex items-center justify-between rounded-lg bg-glass border border-glass-border px-3 py-2 text-xs"
                >
                  <span className="font-mono text-text-primary break-all">{intent.pa}</span>
                  <span className="ml-3 shrink-0 text-text-tertiary">{intent.mode}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="glass mt-6 rounded-2xl p-5">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-text-primary">
            <IndianRupee className="h-4 w-4 text-accent" /> Why this matters
          </h3>
          <p className="mt-2 text-sm leading-relaxed text-text-secondary">
            A payment QR debits your account, and a collect request does the same while pretending to be money coming
            in. Anyone holding your UPI ID can raise a collect request against you, so verify the payee outside the
            message before approving anything.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link
              to="/analyze/text"
              className="inline-flex h-11 items-center rounded-xl bg-accent px-5 text-sm font-semibold text-white hover:bg-accent/90"
            >
              Analyse the full message
            </Link>
            <Link
              to="/recovery"
              className="inline-flex h-11 items-center rounded-xl border border-glass-border bg-glass px-5 text-sm font-medium text-text-primary hover:bg-glass-hover"
            >
              Already paid? Open Recovery Pack
            </Link>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
