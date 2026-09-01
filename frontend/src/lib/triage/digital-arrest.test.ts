import { describe, it, expect } from 'vitest';
import { evaluateTriage, type TriageAnswers } from './digital-arrest';

describe('digital-arrest triage — exhaustive 16 combinations', () => {
  const bools: boolean[] = [true, false];

  // Generate all 16 combinations
  const combos: TriageAnswers[] = [];
  for (const q1 of bools) {
    for (const q2 of bools) {
      for (const q3 of bools) {
        for (const q4 of bools) {
          combos.push({ q1, q2, q3, q4 });
        }
      }
    }
  }

  it('covers all 16 combinations', () => {
    expect(combos).toHaveLength(16);
  });

  // Table from spec:
  // q4=true                          -> ALREADY_PAID_ACT_NOW (always, regardless of q1/q2/q3)
  // q4=false, q1=true                -> LIKELY_DIGITAL_ARREST_SCAM (regardless of q2/q3)
  // q4=false, q1=false                -> SAFE_TO_HANG_UP (regardless of q2/q3)
  for (const answers of combos) {
    const expected =
      answers.q4 === true
        ? 'ALREADY_PAID_ACT_NOW'
        : answers.q1 === true
        ? 'LIKELY_DIGITAL_ARREST_SCAM'
        : 'SAFE_TO_HANG_UP';

    it(`q1=${answers.q1} q2=${answers.q2} q3=${answers.q3} q4=${answers.q4} => ${expected}`, () => {
      const result = evaluateTriage(answers);
      expect(result).not.toBeNull();
      expect(result!.outcome).toBe(expected);
      if (expected === 'LIKELY_DIGITAL_ARREST_SCAM') {
        expect(result!.message).toContain('No Indian police force');
      }
      if (expected === 'ALREADY_PAID_ACT_NOW') {
        expect(result!.title).toMatch(/act now/i);
      }
    });
  }

  it('returns null when q1 is unanswered and q4 is not true', () => {
    expect(evaluateTriage({ q1: null, q2: false, q3: false, q4: false })).toBeNull();
    expect(evaluateTriage({ q1: null, q2: null, q3: null, q4: null })).toBeNull();
    // q4 true still returns even if q1 null
    expect(evaluateTriage({ q1: null, q2: null, q3: null, q4: true })?.outcome).toBe('ALREADY_PAID_ACT_NOW');
  });
});
