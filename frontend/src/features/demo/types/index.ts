import type { AnalysisResponse } from '@/types';

export interface DemoCase {
  id: string;
  title: string;
  category: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  description: string;
  icon: string;
  result: AnalysisResponse;
}

export interface WalkthroughStep {
  target: string;
  title: string;
  content: string;
  position: 'top' | 'bottom' | 'left' | 'right' | 'center';
}
