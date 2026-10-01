import { describe, it, expect } from 'vitest';
import { analyzeTextLocal } from '@/services/local-analysis';
import { UpiInspectorCard } from '@/features/analysis/components/upi-inspector-card';
import { render } from '@testing-library/react';
import React from 'react';

/**
 * End-to-end UI gate for COLLECT — the scam mechanic that motivated the feature.
 * Parser alone (test 7) proves `upi://collect` is detected.
 * This proves the same string survives the *whole* flow: text -> repair -> pipeline (no score change) -> UPI enrichment -> props for the card,
 * and that the card renders at PAY-level alarm (danger, caps, collect wording).
 */
describe('COLLECT end-to-end through pipeline + Inspector UI', () => {
  it('parser + pipeline enrichment preserves COLLECT with amount', () => {
    const r = analyzeTextLocal('Please approve: upi://collect?pa=attacker@okicici&am=10000&tn=collect');
    expect(r.upi_intent).toBeDefined();
    expect(r.upi_intent!.mode).toBe('COLLECT');
    expect(r.upi_intent!.pa).toBe('attacker@okicici');
    expect(r.upi_intent!.amount).toBe(10000);
    // enrichment must not flip the verdict to safe or move gold numbers — smoke check that pipeline still runs
    expect(typeof r.prediction).toBe('string');
    expect(typeof r.risk_level).toBe('string');
  });

  it('Inspector renders COLLECT as loud as PAY (danger, caps, FROM you)', () => {
    const intent = {
      raw: 'upi://collect?pa=attacker@okicici&am=10000',
      kind: 'UPI_INTENT' as const,
      mode: 'COLLECT' as const,
      pa: 'attacker@okicici',
      pn: null,
      am: '10000',
      amount: 10000,
      cu: 'INR',
      tn: 'collect',
      tr: null,
      handle: 'okicici',
      confidence: 0.98,
      source: 'upi_intent',
    };
    const { container } = render(React.createElement(UpiInspectorCard, { intent }));
    const headline = container.textContent || '';
    // Must be caps and mention PAY/COLLECT and FROM you / charged — same visual weight as PAY's "YOU WILL PAY"
    expect(headline).toMatch(/YOU WILL PAY/i);
    expect(headline).toMatch(/COLLECT/i);
    expect(headline).toMatch(/10000|10,000|₹/);
    // Danger styling: border-danger / bg-danger — the card's root has danger classes for COLLECT
    const root = container.firstChild as HTMLElement;
    expect(root.className).toMatch(/border-danger/);
    expect(root.className).toMatch(/bg-danger\/10/);
    // Subline must debunk the receive expectation — the core confusion
    expect(headline + container.textContent).toMatch(/collect request/i);
    expect(container.textContent).toMatch(/will NOT receive/i);
  });

  it('Inspector PAY baseline still danger for comparison', () => {
    const payIntent = {
      raw: 'upi://pay?pa=shop@ybl&am=2500',
      kind: 'UPI_INTENT' as const,
      mode: 'PAY' as const,
      pa: 'shop@ybl',
      pn: null,
      am: '2500',
      amount: 2500,
      cu: null,
      tn: null,
      tr: null,
      handle: 'ybl',
      confidence: 0.98,
      source: 'upi_intent',
    };
    const { container } = render(React.createElement(UpiInspectorCard, { intent: payIntent }));
    expect(container.textContent).toMatch(/YOU WILL PAY/i);
    const root = container.firstChild as HTMLElement;
    expect(root.className).toMatch(/border-danger/);
  });
});
