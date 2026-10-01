import { AlertTriangle, IndianRupee, QrCode, AlertCircle } from 'lucide-react';
import type { UpiIntent } from '@/types';
import { formatInr } from '@/lib/scamshield/upi-intent';

interface Props {
  intent: UpiIntent | null | undefined;
  intents?: UpiIntent[] | null;
}

export function UpiInspectorCard({ intent, intents }: Props) {
  if (!intent) return null;

  const amountLabel = formatInr(intent.amount);
  const isPay = intent.mode === 'PAY';
  const isCollect = intent.mode === 'COLLECT';
  const hasAmount = intent.amount != null && intent.am != null;
  const isUpiIntent = intent.kind === 'UPI_INTENT';
  const isBare = intent.kind === 'BARE_VPA';

  // Determine headline and severity
  let headline: string;
  let subline: string;
  let tone: 'danger' | 'warning' | 'neutral' = 'danger';
  let icon = <QrCode className="h-6 w-6" />;

  if (isBare) {
    headline = `Contains UPI ID ${intent.pa}`;
    subline = 'This message contains a UPI handle. Anyone with this ID can request money from you. Verify the person before paying and never approve a collect request you did not expect.';
    tone = 'warning';
    icon = <IndianRupee className="h-6 w-6" />;
  } else if (isPay && hasAmount) {
    headline = `YOU WILL PAY ${amountLabel} TO ${intent.pa}`;
    subline = 'Scanning this QR will SEND money FROM your account. You will NOT receive money. Do NOT approve if you did not intend to pay this person.';
    tone = 'danger';
    icon = <AlertTriangle className="h-6 w-6" />;
  } else if (isPay && !hasAmount) {
    headline = `This QR asks you to PAY to ${intent.pa}`;
    subline = 'Amount is not shown in the QR — you will be asked to enter an amount. An attacker can trick you into entering a large amount. Do NOT approve unless you are 100% sure.';
    tone = 'danger';
    icon = <AlertTriangle className="h-6 w-6" />;
  } else if (isCollect) {
    // COLLECT is the highest-confusion case: victim expects to RECEIVE, but collect DEBITS them.
    // Render at same danger level as PAY (border-danger, bg-danger, caps) — never quieter.
    headline = hasAmount
      ? `YOU WILL PAY ${amountLabel} — COLLECT REQUEST TO ${intent.pa}`
      : `YOU WILL BE CHARGED — THIS COLLECT REQUEST WILL TAKE MONEY FROM YOU`;
    subline = 'This is a collect request, not a payment you receive. If you tap Approve, money leaves YOUR account immediately. You will NOT receive money. Decline unless you personally created this request and verified the payee outside this message.';
    tone = 'danger';
    icon = <AlertCircle className="h-6 w-6" />;
  } else {
    // UNKNOWN mode
    if (hasAmount) {
      headline = `This QR involves ${amountLabel} with ${intent.pa || intent.raw.slice(0, 40)}`;
      subline = 'Direction is not clearly marked. Assume scanning will ASK YOU TO PAY. Do not approve unless you verified the receiver and amount separately.';
      tone = 'warning';
    } else {
      headline = `UPI request to ${intent.pa || 'unknown payee'}`;
      subline = 'This UPI QR contains a payment request with no amount shown. Scanning may ask you to APPROVE a payment. Only approve if you initiated this payment and verified the payee.';
      tone = 'warning';
    }
  }

  const toneClasses =
    tone === 'danger'
      ? 'border-danger/30 bg-danger/10 text-danger'
      : tone === 'warning'
      ? 'border-warning/30 bg-warning/10 text-warning'
      : 'border-glass-border bg-glass text-text-secondary';

  return (
    <div className={`glass rounded-2xl p-6 animate-scale-in border-2 ${toneClasses}`}>
      <div className="flex items-start gap-4">
        <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${tone === 'danger' ? 'bg-danger text-white' : tone === 'warning' ? 'bg-warning/20 text-warning' : 'bg-glass text-text-tertiary'}`}>
          {icon}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide opacity-70">UPI Inspector — read before you scan</p>
          <h3 className="mt-1 text-lg font-bold leading-tight text-text-primary break-words">{headline}</h3>
          <p className="mt-2 text-sm leading-relaxed text-text-secondary">{subline}</p>

          {/* Details grid */}
          <div className="mt-4 grid gap-2 text-xs">
            {intent.pa && (
              <div className="flex justify-between rounded-lg bg-white/60 px-3 py-2 dark:bg-black/20">
                <span className="font-medium text-text-tertiary">Payee (pa)</span>
                <span className="font-mono font-semibold text-text-primary break-all">{intent.pa}</span>
              </div>
            )}
            {intent.pn && (
              <div className="flex justify-between rounded-lg bg-white/60 px-3 py-2 dark:bg-black/20">
                <span className="font-medium text-text-tertiary">Name (pn)</span>
                <span className="font-semibold text-text-primary break-all">{intent.pn}</span>
              </div>
            )}
            {hasAmount && (
              <div className="flex justify-between rounded-lg bg-white/60 px-3 py-2 dark:bg-black/20">
                <span className="font-medium text-text-tertiary">Amount</span>
                <span className="font-bold text-text-primary">{amountLabel} {intent.cu ? `(${intent.cu})` : '(INR)'}</span>
              </div>
            )}
            {!hasAmount && isUpiIntent && (
              <div className="flex justify-between rounded-lg bg-white/60 px-3 py-2 dark:bg-black/20">
                <span className="font-medium text-text-tertiary">Amount</span>
                <span className="font-semibold text-warning">Not shown in QR</span>
              </div>
            )}
            {intent.tn && (
              <div className="flex justify-between rounded-lg bg-white/60 px-3 py-2 dark:bg-black/20">
                <span className="font-medium text-text-tertiary">Note (tn)</span>
                <span className="text-text-secondary break-all">{intent.tn}</span>
              </div>
            )}
            {intent.handle && (
              <div className="flex justify-between rounded-lg bg-white/60 px-3 py-2 dark:bg-black/20">
                <span className="font-medium text-text-tertiary">Handle</span>
                <span className="font-mono text-text-tertiary">{intent.handle}</span>
              </div>
            )}
            <div className="flex justify-between rounded-lg bg-white/60 px-3 py-2 dark:bg-black/20">
              <span className="font-medium text-text-tertiary">Mode</span>
              <span className="font-semibold text-text-primary">{intent.mode} {intent.kind === 'BARE_VPA' ? '(bare handle)' : ''}</span>
            </div>
          </div>

          {/* Safety checklist */}
          <div className="mt-4 rounded-xl bg-white/70 p-3 dark:bg-black/20">
            <p className="text-xs font-semibold text-text-primary">Before you tap Pay:</p>
            <ul className="mt-1.5 space-y-1 text-xs text-text-secondary">
              <li className="flex gap-1.5"><span>•</span><span>You will <b>PAY</b> — not receive. QR scan never credits your account automatically.</span></li>
              <li className="flex gap-1.5"><span>•</span><span>Check payee name and handle with the person outside this message.</span></li>
              <li className="flex gap-1.5"><span>•</span><span>If you already paid, use the Recovery Pack to generate a 1930 report in 60 seconds.</span></li>
            </ul>
          </div>

          {intents && intents.length > 1 && (
            <p className="mt-3 text-xs text-text-tertiary">
              Found {intents.length} UPI handles in this message. The first is shown above; all are listed in entities below.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default UpiInspectorCard;
