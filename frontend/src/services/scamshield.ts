import api from './api';
import type {
  HealthResponse,
  ReadinessResponse,
  LivenessResponse,
  MetricsSnapshot,
  AnalysisResponse,
  ImageAnalysisResponse,
} from '@/types';

export async function analyzeText(text: string): Promise<AnalysisResponse> {
  const { data } = await api.post<AnalysisResponse>('/analyze/text', { text });
  return data;
}

export async function analyzeImage(file: File): Promise<ImageAnalysisResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post<ImageAnalysisResponse>('/analyze/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function health(): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/health');
  return data;
}

export async function ready(): Promise<ReadinessResponse> {
  const { data } = await api.get<ReadinessResponse>('/ready');
  return data;
}

export async function live(): Promise<LivenessResponse> {
  const { data } = await api.get<LivenessResponse>('/live');
  return data;
}

export async function metrics(): Promise<MetricsSnapshot> {
  const { data } = await api.get<MetricsSnapshot>('/metrics');
  return data;
}
