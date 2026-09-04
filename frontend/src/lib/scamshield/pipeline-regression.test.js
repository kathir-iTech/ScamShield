import { describe, it, expect } from 'vitest';
import { analyzeText } from './pipeline.js';

// Messages for the new rule patterns added in Phase 7.
// Each pattern has a clear positive (scam) example and a safe near-miss.

const SCAM_MESSAGES = [
  // Prepaid-task scam positives
  {
    msg: "You earned Rs 50 for today's task. Now pay Rs 2000 to unlock more tasks and withdraw your earnings.",
    expectedIndicator: 'Prepaid Task Scam',
  },
  {
    msg: 'Great work! Commission of Rs 100 credited. Deposit Rs 5000 to activate the next level and earn daily Rs 2000.',
    expectedIndicator: 'Prepaid Task Scam',
  },
  {
    msg: 'Job: like YouTube videos, earn Rs 300 daily. Small payout every day. To continue, invest Rs 10,000 and unlock bigger tasks.',
    expectedIndicator: 'Prepaid Task Scam',
  },
  // Screen-share / remote-access positives
  {
    msg: 'Our bank found an issue with your account. Install AnyDesk and share your screen so we can verify and fix it. Do not tell anyone or share your OTP with anyone else.',
    expectedIndicator: 'Remote Access Request',
  },
  {
    msg: 'This is the refund team. Please install TeamViewer QuickSupport and give us the ID so we can process your refund. You will get OTP on your phone.',
    expectedIndicator: 'Remote Access Request',
  },
];

const SAFE_MESSAGES = [
  // Prepaid-task near-miss: no payment/unlock ask
  'You have earned 50 reward points in the loyalty program. Redeem them on the official app before the 30th.',
  // Legitimate IT support screen share with NO banking context at all
  'IT support here. Need to update a graphics driver on your machine. Please install AnyDesk and share the ID so our technician can connect and complete the update.',
  // Normal task without money talk
  'Your team has completed the onboarding tasks. Great progress!',
  // Casual screen share with no banking
  'Let me view the invitation design on the call - you can share your screen so I can check the layout.',
  // Plain OTP message (safe)
  'Your OTP for login is 482913, valid for 10 minutes. Do not share it with anyone.',
];

describe('Phase 7 new rule patterns', () => {
  for (const { msg } of SCAM_MESSAGES) {
    it('flags scam message: ' + msg.slice(0, 60), () => {
      const result = analyzeText(msg);
      expect(result.detected_indicators.length).toBeGreaterThan(0);
      expect(result.risk_level).not.toBe('VERY LOW');
    });
  }

  for (const msg of SAFE_MESSAGES) {
    it('does not over-flag safe near-miss: ' + msg.slice(0, 60), () => {
      const result = analyzeText(msg);
      const threats = result.threats || [];
      const invented = threats.some((t) =>
        t === 'Financial Theft' || t === 'Credential Theft' || t === 'Social Engineering'
      );
      expect(invented).toBe(false);
    });
  }

  it('detects Prepaid Task Scam indicator on clear prepaid-task message', () => {
    const result = analyzeText(SCAM_MESSAGES[0].msg);
    expect(result.detected_indicators).toContain('Prepaid Task Scam');
  });

  it('detects Remote Access Request indicator on clear screen-share message', () => {
    const result = analyzeText(SCAM_MESSAGES[3].msg);
    expect(result.detected_indicators).toContain('Remote Access Request');
  });
});

// Tier 1 FN-gap close-out: HYIP/guaranteed-return pitches, job/modeling offers
// demanding upfront fees, and formal-legal-notice digital-arrest messages.
// Each scam positive asserts the user-facing refined verdict; each safe
// near-miss proves the new rule stays silent (no invented threats, and the
// specific new rule id absent from the refinement summary).
describe('Tier 1 FN-gap rules (FN-015/016/017)', () => {
  const GAP_SCAMS = [
    {
      msg: 'HYIP: High yield investment program. 5% daily returns for 30 days. Minimum deposit Rs 5,000.',
      expectedIndicator: 'Investment Offer',
    },
    {
      msg: 'Modeling assignment for international brand. Stipend Rs 2 lakh. Registration Rs 7,500.',
      expectedIndicator: 'Job Offer',
    },
    {
      msg: 'Personal loan repayment: Your cheque bounced. Legal notice under NI Act will be filed. Settle with Rs 25,000.',
      expectedIndicator: null, // caught by FN-015 refinement, no standalone indicator
    },
  ];

  const GAP_SAFE = [
    // Legitimate market commentary mentioning returns + disclaimer, no demand
    'Market outlook: large-cap funds delivered healthy returns over the last decade. Past performance does not guarantee future results. This is not investment advice.',
    // Real job posting with no fee at all
    'Your interview with TCS is scheduled for Monday 10 AM. Venue: campus center, Block B. Carry your resume.',
    // Real posting that explicitly disavows fees (negation guard for FN-012/017)
    'Infosys hiring: Software Engineer, CTC Rs 12 LPA. Apply on the careers portal by Friday. No registration fee.',
    // Genuine legal notice with no payment or call demand (demand gate for FN-015)
    'Court notice: Summons issued under Section 138 in Case No. 452/2024. Hearing on 12 Dec. Contact your advocate.',
  ];

  for (const { msg, expectedIndicator } of GAP_SCAMS) {
    it('refined verdict is scam: ' + msg.slice(0, 60), () => {
      expect(analyzeText(msg).refined_prediction).toBe('scam');
    });
    if (expectedIndicator) {
      it('detects ' + expectedIndicator + ' indicator: ' + msg.slice(0, 60), () => {
        expect(analyzeText(msg).detected_indicators).toContain(expectedIndicator);
      });
    }
  }

  for (const msg of GAP_SAFE) {
    it('does not over-flag safe near-miss: ' + msg.slice(0, 60), () => {
      const result = analyzeText(msg);
      const threats = result.threats || [];
      const invented = threats.some((t) =>
        t === 'Financial Theft' || t === 'Credential Theft' || t === 'Social Engineering'
      );
      expect(invented).toBe(false);
      expect(result.refinement_summary || '').not.toMatch(/FN-015|FN-016|FN-017/);
    });
  }

  it('negation guard keeps FN-012 silent on explicit no-fee posting', () => {
    const result = analyzeText(GAP_SAFE[2]);
    expect(result.refinement_summary || '').not.toMatch(/FN-012/);
  });
});
