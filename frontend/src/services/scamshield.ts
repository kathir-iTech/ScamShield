import api from './api';
import type {
  HealthResponse,
  ReadinessResponse,
  LivenessResponse,
  MetricsSnapshot,
  AnalysisResponse,
  ImageAnalysisResponse,
} from '@/types';

export async function analyzeText(text: string, signal?: AbortSignal): Promise<AnalysisResponse> {
  const { data } = await api.post<AnalysisResponse>('/analyze/text', { text }, {
    signal,
    timeout: 20000,
  });
  return data;
}

export async function analyzeImage(file: File, signal?: AbortSignal): Promise<ImageAnalysisResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post<ImageAnalysisResponse>('/analyze/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    signal,
    timeout: 60000,
  });
  return data;
}

export async function health(signal?: AbortSignal): Promise<HealthResponse> {
  const { data } = await api.get<HealthResponse>('/health', { signal });
  return data;
}

export async function ready(signal?: AbortSignal): Promise<ReadinessResponse> {
  const { data } = await api.get<ReadinessResponse>('/ready', { signal });
  return data;
}

export async function live(signal?: AbortSignal): Promise<LivenessResponse> {
  const { data } = await api.get<LivenessResponse>('/live', { signal });
  return data;
}

export async function metrics(signal?: AbortSignal): Promise<MetricsSnapshot> {
  const { data } = await api.get<MetricsSnapshot>('/metrics', { signal });
  return data;
}
