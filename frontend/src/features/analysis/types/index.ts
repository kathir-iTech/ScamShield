import type { AnalysisResponse, ImageAnalysisResponse } from '@/types';

export type StoredAnalysis = {
  id: string;
  timestamp: number;
  inputText?: string;
  inputFileName?: string;
  result: AnalysisResponse | ImageAnalysisResponse;
  isImage: boolean;
};

export type AnalysisStatus = 'idle' | 'loading' | 'success' | 'error';
