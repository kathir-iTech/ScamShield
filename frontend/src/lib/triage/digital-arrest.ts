/**
 * Digital Arrest Triage — client-side, no backend, no ML
 * Pure fixed decision tree. Must NOT import from frontend/src/lib/scamshield/.
 * This is separate from the text/OCR classifier by design.
 */

export type TriageOutcome = 'SAFE_TO_HANG_UP' | 'LIKELY_DIGITAL_ARREST_SCAM' | 'ALREADY_PAID_ACT_NOW';

export interface TriageAnswers {
  q1: boolean | null; // Are you on a call with someone claiming to be police/CBI/customs/gov?
  q2: boolean | null; // Told to stay on camera, not hang up, not tell anyone?
  q3: boolean | null; // Asked to transfer money / gift cards / move to "safe" account?
  q4: boolean | null; // Already sent any money?
}

export interface TriageQuestion {
  id: keyof TriageAnswers;
  text: string;
  helper?: string;
}

export const QUESTIONS: TriageQuestion[] = [
  {
    id: 'q1',
    text: 'Are you currently on a call with someone claiming to be police, CBI, customs, or a government official?',
    helper: 'They may say ED, CBI, Cyber Crime, Customs, Supreme Court, or “officer”.',
  },
  {
    id: 'q2',
    text: 'Have they told you to stay on camera, not hang up, or not tell anyone?',
    helper: 'Phrases like “stay on video call”, “don’t disconnect”, “don’t tell family” are red flags.',
  },
  {
    id: 'q3',
    text: 'Have they asked you to transfer money, buy gift cards, or move funds to a “safe” account?',
    helper: 'Includes UPI, bank transfer, crypto, or asking to buy vouchers.',
  },
  {
    id: 'q4',
    text: 'Have you already sent any money?',
    helper: 'Even a small test amount counts. This changes what you should do next.',
  },
];

export interface TriageResult {
  outcome: TriageOutcome;
  title: string;
  message: string;
  actions: string[];
  severity: 'safe' | 'warning' | 'critical';
}

/**
 * Decision tree:
 * - Q4 yes → ALREADY_PAID_ACT_NOW (highest priority, overrides Q1-3)
 * - Else if Q1 yes AND (Q2 yes OR Q3 yes) → LIKELY_DIGITAL_ARREST_SCAM
 * - Else if Q1 yes (alone) → LIKELY_DIGITAL_ARREST_SCAM (err on side of caution; impersonation alone is enough)
 * - Else (Q1 no/no answer yet or all no) → SAFE_TO_HANG_UP
 *
 * This is intentionally conservative for a panicking user: any impersonation
 * is treated as likely scam until proven otherwise.
 */
export function evaluateTriage(answers: TriageAnswers): TriageResult | null {
  const { q1, q2, q3, q4 } = answers;

  // Need at least Q1 answered to evaluate; Q4 can short-circuit even if others null
  if (q4 === true) {
    return {
      outcome: 'ALREADY_PAID_ACT_NOW',
      title: 'You sent money — act now',
      message:
        'Every minute counts. The faster you report, the higher the chance to freeze the transaction.',
      actions: [
        'Call 1930 now — India’s 24x7 cybercrime helpline. Keep the line open.',
        'After calling, file at cybercrime.gov.in with the details below.',
        'Do not delete the chat, call logs, or transaction screenshots.',
        'Tell a trusted family member immediately — you are not alone.',
      ],
      severity: 'critical',
    };
  }

  // If Q1 is not yet answered, cannot decide final outcome
  if (q1 === null || q1 === undefined) return null;

  if (q1 === true) {
    // Any impersonation + any coercion or money request → definitely likely
    if (q2 === true || q3 === true) {
      return {
        outcome: 'LIKELY_DIGITAL_ARREST_SCAM',
        title: 'This is almost certainly a scam — hang up now',
        message:
          'No Indian police force, court, or government agency conducts arrests over a phone or video call, or asks for money to avoid one. Hang up now. Do not transfer money, share OTP, or install any app.',
        actions: [
          'Hang up immediately — you will not be punished for disconnecting.',
          'Do not call back the number they gave you. Block it.',
          'Tell a family member or friend what happened.',
          'Call 1930 to confirm and report, or visit your nearest police station.',
        ],
        severity: 'warning',
      };
    }
    // Q1 true alone (Q2/Q3 false or not yet answered, but not both false with Q4 false)
    // We still treat as likely to be safe, but distinguish if we have full answers
    const hasAllAnswers = q2 !== null && q3 !== null;
    if (hasAllAnswers && q2 === false && q3 === false) {
      // Impersonation but no coercion and no money request — could be verification call, but still warn
      return {
        outcome: 'LIKELY_DIGITAL_ARREST_SCAM',
        title: 'Hang up — verify separately',
        message:
          'No Indian police force, court, or government agency conducts arrests over a phone or video call, or asks for money to avoid one. Hang up now and verify by calling 100 or your local police station directly.',
        actions: [
          'Hang up now — it is safe to disconnect.',
          'Do not share OTP, Aadhaar, or bank details.',
          'Call 100 or 1930 from a different phone to verify if you are worried.',
        ],
        severity: 'warning',
      };
    }
    // Partial answers but Q1 yes → still likely (conservative)
    if (q1 === true) {
      return {
        outcome: 'LIKELY_DIGITAL_ARREST_SCAM',
        title: 'This looks like a digital arrest scam — hang up now',
        message:
          'No Indian police force, court, or government agency conducts arrests over a phone or video call, or asks for money to avoid one. Hang up now.',
        actions: [
          'Hang up immediately.',
          'Block the number. Do not transfer money.',
          'Call 1930 if you need confirmation.',
        ],
        severity: 'warning',
      };
    }
  }

  // Q1 false → not a digital arrest pattern
  if (q1 === false) {
    return {
      outcome: 'SAFE_TO_HANG_UP',
      title: 'You can safely hang up',
      message:
        'You can safely hang up. No real police or government agency will punish you for disconnecting a suspicious call. If you are still worried, call 100 or your local police station directly (not the number they gave you) to double-check.',
      actions: [
        'Hang up — you are safe to disconnect.',
        'If they call back, do not engage. Block the number.',
        'If you want to verify, call 100 or 1930 yourself.',
      ],
      severity: 'safe',
    };
  }

  return null;
}

export interface ComplaintDetails {
  amount?: string;
  accountOrUpi?: string;
  callerPhone?: string;
  timeApprox?: string;
  whatHappened?: string;
}

export function generateComplaintTemplate(details: ComplaintDetails): string {
  const amount = details.amount?.trim() || '[amount]';
  const account = details.accountOrUpi?.trim() || '[account / UPI ID / phone number you sent to]';
  const phone = details.callerPhone?.trim() || '[caller’s phone number / WhatsApp number]';
  const time = details.timeApprox?.trim() || '[date and approximate time, e.g., 2 Sep 2026 around 3:30 PM]';
  const what = details.whatHappened?.trim() || '[briefly describe: who called, what they claimed, that they said you were under “digital arrest” and must stay on video call]';

  return `Complaint for cybercrime.gov.in / Call 1930

I am reporting a “digital arrest” fraud.

What happened:
${what}

The caller claimed to be from police/CBI/customs/government and said I am under investigation / digital arrest. They told me to stay on video call, not to hang up, and not to tell anyone.

They asked me to transfer money to a “safe” or “verification” account.

Details of transaction (if any):
- Amount sent: ${amount}
- Sent to (account / UPI ID / phone): ${account}
- Caller’s number: ${phone}
- Time of call/transfer: ${time}

I have not deleted call logs, chat, or transaction screenshots and can share them.

Request: Please freeze the transaction and investigate. I am available for further verification.

Complainant contact: [your name, phone, email]

Note: This template is for cybercrime.gov.in (National Cyber Crime Reporting Portal) or for reading aloud when you call 1930. Keep it factual and attach screenshots if filing online.
`.trim();
}

export const CHAKSHU_URL = 'https://sancharsaathi.gov.in/sfc';
