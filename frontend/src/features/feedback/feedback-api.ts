import api from '@/services/api';

export type FeedbackVerdict = 'correct' | 'incorrect' | 'unsure';

export interface FeedbackPayload {
  analysis_id?: string;
  verdict: FeedbackVerdict;
  corrected_label?: string;
  note?: string;
}

export interface FeedbackReceipt {
  detail: string;
  id?: string;
}

export async function submitFeedback(payload: FeedbackPayload): Promise<FeedbackReceipt> {
  const { data } = await api.post<FeedbackReceipt>('/feedback', {
    analysis_id: payload.analysis_id ?? '',
    verdict: payload.verdict,
    corrected_label: payload.corrected_label ?? '',
    note: payload.note ?? '',
  });
  return data;
}
