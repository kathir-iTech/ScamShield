import { describe, it, expect } from 'vitest';
import {
  riskStatus,
  decisionStatus,
  priorityStatus,
  assessmentStatus,
  severityStatus,
  predictionStatus,
} from '@/design/status';

describe('riskStatus', () => {
  it('returns danger for critical', () => {
    const s = riskStatus('CRITICAL');
    expect(s.variant).toBe('danger');
    expect(s.label).toBe('CRITICAL');
  });

  it('returns danger for high', () => {
    const s = riskStatus('HIGH');
    expect(s.variant).toBe('danger');
  });

  it('returns warning for medium', () => {
    const s = riskStatus('MEDIUM');
    expect(s.variant).toBe('warning');
  });

  it('returns info for very low', () => {
    const s = riskStatus('VERY LOW');
    expect(s.variant).toBe('info');
  });

  it('returns success for low', () => {
    const s = riskStatus('LOW');
    expect(s.variant).toBe('success');
  });
});

describe('decisionStatus', () => {
  it('returns danger for critical', () => {
    expect(decisionStatus('critical').variant).toBe('danger');
  });

  it('returns danger for high', () => {
    expect(decisionStatus('HIGH').variant).toBe('danger');
  });

  it('returns warning for suspicious', () => {
    expect(decisionStatus('suspicious').variant).toBe('warning');
  });

  it('returns info for low', () => {
    const s = decisionStatus('low priority');
    expect(s.variant).toBe('info');
  });

  it('returns success for allow', () => {
    expect(decisionStatus('ALLOW').variant).toBe('success');
  });
});

describe('predictionStatus', () => {
  it('returns danger for scam', () => {
    const s = predictionStatus('scam');
    expect(s.variant).toBe('danger');
    expect(s.label).toBe('SCAM');
  });

  it('returns success for not scam', () => {
    const s = predictionStatus('not scam');
    expect(s.variant).toBe('success');
    expect(s.label).toBe('SAFE');
  });
});

describe('assessmentStatus', () => {
  it('returns danger for immediate action', () => {
    expect(assessmentStatus('Suitable for immediate action').variant).toBe('danger');
  });

  it('returns warning for investigation', () => {
    expect(assessmentStatus('Suitable for security investigation').variant).toBe('warning');
  });

  it('returns info for assessment required', () => {
    expect(assessmentStatus('Further assessment required').variant).toBe('info');
  });

  it('returns success for normal', () => {
    expect(assessmentStatus('Suitable for normal communication').variant).toBe('success');
  });
});

describe('severityStatus', () => {
  it('returns danger for critical', () => {
    expect(severityStatus('critical').variant).toBe('danger');
  });

  it('returns danger for high', () => {
    expect(severityStatus('high').variant).toBe('danger');
  });

  it('returns warning for medium', () => {
    expect(severityStatus('medium').variant).toBe('warning');
  });

  it('returns info for low', () => {
    expect(severityStatus('low').variant).toBe('info');
  });

  it('returns neutral for unknown', () => {
    expect(severityStatus('unknown').variant).toBe('neutral');
  });
});

describe('priorityStatus', () => {
  it('returns danger for urgent', () => {
    expect(priorityStatus('urgent').variant).toBe('danger');
  });

  it('returns warning for high', () => {
    expect(priorityStatus('high').variant).toBe('warning');
  });

  it('returns info for normal', () => {
    expect(priorityStatus('normal').variant).toBe('info');
  });

  it('returns neutral for other', () => {
    expect(priorityStatus('low').variant).toBe('neutral');
  });
});
