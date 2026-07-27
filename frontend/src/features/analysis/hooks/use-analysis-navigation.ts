import { useNavigate } from 'react-router-dom';
import { useAnalysis } from '@/features/analysis/context/analysis-context';
import type { AnalysisResponse, ImageAnalysisResponse } from '@/types';

export function useAnalysisNavigation() {
  const navigate = useNavigate();
  const { storeAnalysis } = useAnalysis();

  const navigateToResult = (
    result: AnalysisResponse | ImageAnalysisResponse,
    isImage: boolean,
    inputText?: string,
    inputFileName?: string
  ) => {
    storeAnalysis(result, isImage, inputText, inputFileName);
    navigate('/analysis/result');
  };

  return { navigateToResult };
}
