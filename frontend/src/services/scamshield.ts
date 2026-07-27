import api, { createCancelToken } from './api';
import type {
  HealthResponse,
  ReadinessResponse,
  LivenessResponse,
  MetricsSnapshot,
  AnalysisResponse,
  ImageAnalysisResponse,
} from '@/types';

export async function analyzeText(text: string, signal?: AbortSignal): Promise<AnalysisResponse> {
  const source = createCancelToken();
  const onAbort = () => source.cancel('Request cancelled');

  if (signal) {
    if (signal.aborted) throw new DOMException('Aborted', 'AbortError');
    signal.addEventListener('abort', onAbort, { once: true });
  }

  try {
    const { data } = await api.post<AnalysisResponse>('/analyze/text', { text }, {
      cancelToken: source.token,
      timeout: 20000,
    });
    return data;
  } finally {
    if (signal) signal.removeEventListener('abort', onAbort);
  }
}

export async function analyzeImage(file: File, signal?: AbortSignal): Promise<ImageAnalysisResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const source = createCancelToken();
  const onAbort = () => source.cancel('Upload cancelled');

  if (signal) {
    if (signal.aborted) throw new DOMException('Aborted', 'AbortError');
    signal.addEventListener('abort', onAbort, { once: true });
  }

  try {
    const { data } = await api.post<ImageAnalysisResponse>('/analyze/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      cancelToken: source.token,
      timeout: 60000,
    });
    return data;
  } finally {
    if (signal) signal.removeEventListener('abort', onAbort);
  }
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
