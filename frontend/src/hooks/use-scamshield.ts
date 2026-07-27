import { useQuery, useMutation } from '@tanstack/react-query';
import * as scamshieldService from '@/services/scamshield';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: ({ signal }) => scamshieldService.health(signal),
    refetchInterval: 30000,
  });
}

export function useReady() {
  return useQuery({
    queryKey: ['ready'],
    queryFn: ({ signal }) => scamshieldService.ready(signal),
    refetchInterval: 30000,
  });
}

export function useLive() {
  return useQuery({
    queryKey: ['live'],
    queryFn: ({ signal }) => scamshieldService.live(signal),
    refetchInterval: 15000,
  });
}

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: ({ signal }) => scamshieldService.metrics(signal),
    refetchInterval: 10000,
  });
}

export function useAnalyzeText() {
  return useMutation({
    mutationFn: ({ text, signal }: { text: string; signal?: AbortSignal }) =>
      scamshieldService.analyzeText(text, signal),
  });
}

export function useAnalyzeImage() {
  return useMutation({
    mutationFn: ({ file, signal }: { file: File; signal?: AbortSignal }) =>
      scamshieldService.analyzeImage(file, signal),
  });
}
