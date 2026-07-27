import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';
import type { AnalysisResponse, ImageAnalysisResponse } from '@/types';
import type { StoredAnalysis } from '@/features/analysis/types';

interface AnalysisContextValue {
  current: StoredAnalysis | null;
  history: StoredAnalysis[];
  storeAnalysis: (
    result: AnalysisResponse | ImageAnalysisResponse,
    isImage: boolean,
    inputText?: string,
    inputFileName?: string
  ) => string;
  clearCurrent: () => void;
}

const AnalysisContext = createContext<AnalysisContextValue | null>(null);

let analysisId = 0;

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [current, setCurrent] = useState<StoredAnalysis | null>(null);
  const [history, setHistory] = useState<StoredAnalysis[]>([]);

  const storeAnalysis = useCallback(
    (
      result: AnalysisResponse | ImageAnalysisResponse,
      isImage: boolean,
      inputText?: string,
      inputFileName?: string
    ) => {
      const id = String(++analysisId);
      const entry: StoredAnalysis = {
        id,
        timestamp: Date.now(),
        inputText,
        inputFileName,
        result,
        isImage,
      };
      setCurrent(entry);
      setHistory((prev) => [entry, ...prev].slice(0, 20));
      return id;
    },
    []
  );

  const clearCurrent = useCallback(() => setCurrent(null), []);

  return (
    <AnalysisContext.Provider value={{ current, history, storeAnalysis, clearCurrent }}>
      {children}
    </AnalysisContext.Provider>
  );
}

export function useAnalysis(): AnalysisContextValue {
  const ctx = useContext(AnalysisContext);
  if (!ctx) throw new Error('useAnalysis must be used within AnalysisProvider');
  return ctx;
}

export function useCurrentAnalysis(): StoredAnalysis | null {
  const ctx = useContext(AnalysisContext);
  return ctx?.current ?? null;
}
