import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { AnalysisProvider, useAnalysis, useCurrentAnalysis } from '@/features/analysis/context/analysis-context';
import type { AnalysisResponse } from '@/types';

const mockResult: AnalysisResponse = {
  prediction: 'scam',
  confidence: 0.95,
  rule_score: 85,
  rule_label: 'High risk',
  reasons: ['Suspicious URL'],
  suggested_action: 'block',
  summary: 'Test summary',
  risk_level: 'HIGH',
  scam_category: 'Phishing',
  detected_indicators: ['url'],
  threats: ['phishing'],
  recommended_actions: ['Report'],
  entities: [],
  entity_summary: { total_entities: 0, by_type: {}, threat_indicators: [] },
  entity_risk: { high: [], medium: [], low: [] },
  decision_score: 90,
  decision_level: 'HIGH',
  decision_reasoning: 'test',
  supporting_evidence: [],
  conflicting_evidence: [],
  confidence_breakdown: { ml: 95, rules: 80, entities: 0, explanation: 0, overall: 90 },
  risk_breakdown: { credential_theft: 0, financial_loss: 0, identity_theft: 0, malware: 0, social_engineering: 0 },
  recommended_priority: 'high',
  recommended_action: 'report',
  assessment_score: 85,
  assessment_band: 'Suitable for immediate action',
  assessment_confidence: 'high',
  assessment_summary: 'test',
  business_reason: 'test',
  technical_reason: 'test',
  review_required: false,
  manual_review_reason: '',
  investigation_report: {},
};

describe('AnalysisProvider', () => {
  it('provides empty current analysis by default', () => {
    const { result } = renderHook(() => useCurrentAnalysis(), {
      wrapper: ({ children }) => <AnalysisProvider>{children}</AnalysisProvider>,
    });
    expect(result.current).toBeNull();
  });

  it('throws useAnalysis outside provider', () => {
    expect(() => renderHook(() => useAnalysis())).toThrow();
  });

  it('stores and retrieves analysis', () => {
    const { result } = renderHook(() => useAnalysis(), {
      wrapper: ({ children }) => <AnalysisProvider>{children}</AnalysisProvider>,
    });
    act(() => {
      result.current.storeAnalysis(mockResult, false);
    });
    expect(result.current.current).not.toBeNull();
    expect(result.current.current?.result).toBe(mockResult);
    expect(result.current.current?.isImage).toBe(false);
  });

  it('clears current analysis', () => {
    const { result } = renderHook(() => useAnalysis(), {
      wrapper: ({ children }) => <AnalysisProvider>{children}</AnalysisProvider>,
    });
    act(() => {
      result.current.storeAnalysis(mockResult, false);
    });
    act(() => {
      result.current.clearCurrent();
    });
    expect(result.current.current).toBeNull();
  });

  it('limits history to 20 entries', () => {
    const { result } = renderHook(() => useAnalysis(), {
      wrapper: ({ children }) => <AnalysisProvider>{children}</AnalysisProvider>,
    });
    act(() => {
      for (let i = 0; i < 25; i++) {
        result.current.storeAnalysis(mockResult, false);
      }
    });
    expect(result.current.history.length).toBeLessThanOrEqual(20);
  });
});
