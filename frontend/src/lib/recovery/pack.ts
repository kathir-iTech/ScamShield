import type { AnalysisResponse, UpiIntent } from '@/types';

export interface RecoveryDetails {
  amount?: string;
  accountOrUpi?: string;
  callerPhone?: string;
  timeApprox?: string;
  whatHappened?: string;
  transactionId?: string;
}

export interface RecoveryPack {
  header: string;
  steps1930: string[];
  cybercrimeDraft: string;
  evidenceAppendix: string[];
  hash: string | null;
  generatedAt: string;
}

// Lightweight deterministic hash for footer integrity (not anonymity).
// Uses SubtleCrypto SHA-256 when available, fallback to simple fnv-style.
// NOTE: FNV fallback is best-effort only (non-cryptographic, forgeable). It
// exists only for non-HTTPS contexts where SubtleCrypto is unavailable;
// Vercel is always HTTPS so this path should never trigger in production.
// Do not treat fnv-* values as real integrity protection.
export async function computeEvidenceHash(input: string): Promise<string> {
  try {
    if (typeof window !== 'undefined' && window.crypto?.subtle) {
      const enc = new TextEncoder().encode(input);
      const buf = await window.crypto.subtle.digest('SHA-256', enc);
      const arr = Array.from(new Uint8Array(buf));
      return arr.map((b) => b.toString(16).padStart(2, '0')).join('');
    }
  } catch {}
  // Fallback: not cryptographic, but deterministic for footer — best-effort only
  let h = 2166136261;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return 'fnv-' + (h >>> 0).toString(16).padStart(8, '0');
}

function safe(v?: string): string {
  const s = (v || '').trim();
  return s ? s : '[not provided]';
}

export function buildCybercrimeDraft(details: RecoveryDetails, analysis: AnalysisResponse | null): string {
  const amount = safe(details.amount);
  const account = safe(details.accountOrUpi);
  const phone = safe(details.callerPhone);
  const time = safe(details.timeApprox);
  const what = details.whatHappened?.trim() || '[briefly describe what happened: message, call, QR scan, amount, how you were contacted]';
  const txn = details.transactionId?.trim() ? `Transaction ID / Ref: ${details.transactionId.trim()}\n` : '';

  const cat = analysis?.scam_category || 'Unknown';
  const risk = analysis?.risk_level || 'UNKNOWN';
  const pred = analysis?.prediction || 'unknown';
  const summary = analysis?.summary || 'No automated summary.';
  const indicators = analysis?.detected_indicators?.length ? analysis.detected_indicators.join(', ') : 'none';
  const entities = analysis?.entities?.length ? analysis.entities.map((e) => `${e.value} (${e.type})`).join('; ') : 'none';

  // Distinguish digital-arrest wording vs generic
  const isDigitalArrest = cat.toLowerCase().includes('arrest') || (analysis?.detected_indicators || []).some((i) => i.toLowerCase().includes('arrest')) || (analysis?.threats || []).some((t) => t.toLowerCase().includes('arrest'));

  const intro = isDigitalArrest
    ? 'I am reporting a “digital arrest” / impersonation fraud where the caller claimed to be police/CBI/government and threatened arrest over video call.'
    : `I am reporting a suspected scam (${cat}) flagged as ${pred} (${risk}).`;

  return `Complaint for cybercrime.gov.in / Call 1930 — Recovery Pack
Generated locally on your phone on ${new Date().toLocaleString()} — paste into cybercrime.gov.in or read to 1930 operator.

${intro}

What happened:
${what}

Details:
- Amount involved: ${amount}
- Sent to (account / UPI ID / phone / QR payee): ${account}
${txn}- Caller / sender number: ${phone}
- Time of incident: ${time}

Analysis (automated, local):
- Category: ${cat}
- Risk: ${risk} — ${summary}
- Indicators: ${indicators}
- Entities: ${entities}

I have not deleted the message, call logs, screenshots, QR image, or transaction receipt and can share them for verification.

Request: Please freeze the transaction and investigate. I am available for further verification.

Complainant contact: [your name, phone, email]

Note: File at https://cybercrime.gov.in or call 1930 (24x7). Keep this draft factual. Attach screenshots and transaction proof when filing online.`.trim();
}

export function buildEvidenceAppendix(analysis: AnalysisResponse | null): string[] {
  if (!analysis) return ['No analysis available. Analyse a message first to include automated evidence.'];
  const lines: string[] = [];
  lines.push(`Prediction: ${analysis.prediction.toUpperCase()} (confidence ${(analysis.confidence * 100).toFixed(1)}%)`);
  lines.push(`Risk: ${analysis.risk_level} | Category: ${analysis.scam_category} | Assessment: ${analysis.assessment_band} (${analysis.assessment_score})`);
  lines.push(`Summary: ${analysis.summary}`);
  if (analysis.reasons?.length) lines.push(`Reasons: ${analysis.reasons.slice(0, 3).join('; ')}`);
  if (analysis.detected_indicators?.length) lines.push(`Indicators: ${analysis.detected_indicators.join(', ')}`);
  if (analysis.threats?.length) lines.push(`Threats: ${analysis.threats.join(', ')}`);
  if (analysis.entities?.length) {
    const ups = (analysis as unknown as { upi_intent?: UpiIntent | null }).upi_intent;
    if (ups) {
      lines.push(`UPI Inspector: ${ups.mode} ${ups.pa || ups.raw}${ups.amount != null ? ` — ₹${ups.amount}` : ' — amount not shown'} ${ups.tn ? `— note: ${ups.tn}` : ''}`);
    }
    lines.push(`Entities (${analysis.entities.length}): ${analysis.entities.map((e) => `${e.value} [${e.type}/${e.risk}]`).join('; ')}`);
  }
  if (analysis.supporting_evidence?.length) lines.push(`Evidence: ${analysis.supporting_evidence.map((e) => e.description).join(' | ')}`);
  lines.push(`Generated locally — no data was sent to a server.`);
  return lines;
}

export function buildRecoveryPackSync(details: RecoveryDetails, analysis: AnalysisResponse | null): Omit<RecoveryPack, 'hash'> & { hashInput: string } {
  const cybercrimeDraft = buildCybercrimeDraft(details, analysis);
  const evidenceAppendix = buildEvidenceAppendix(analysis);
  const hashInput = JSON.stringify({ details, evidence: evidenceAppendix, analysis: analysis ? { prediction: analysis.prediction, risk: analysis.risk_level, category: analysis.scam_category, indicators: analysis.detected_indicators, entities: analysis.entities } : null });
  const header = analysis
    ? `${analysis.scam_category} — ${analysis.risk_level} — ${analysis.prediction.toUpperCase()}`
    : 'No analysis — manual filing';
  const steps1930 = [
    'Call 1930 immediately — keep the line open. Say: “I need to report a cyber fraud and freeze a transaction.”',
    'Give the operator: amount, payee UPI/account/phone, time, and your phone number. Read the draft below verbatim if needed.',
    'Do NOT delete the message, QR, call logs, or screenshots. Keep the transaction receipt.',
    'After 1930, file at cybercrime.gov.in (or your state portal) and upload this pack + screenshots.',
    'Tell a trusted family member. If threatened with “digital arrest / video call”, hang up — real police never arrest over video call.',
  ];
  return { header, steps1930, cybercrimeDraft, evidenceAppendix, hashInput, generatedAt: new Date().toLocaleString() };
}
