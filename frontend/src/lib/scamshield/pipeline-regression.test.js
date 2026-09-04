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
