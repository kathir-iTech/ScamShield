import { useQuery, useMutation } from '@tanstack/react-query';
import * as scamshieldService from '@/services/scamshield';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: scamshieldService.health,
    refetchInterval: 30000,
  });
}

export function useReady() {
  return useQuery({
    queryKey: ['ready'],
    queryFn: scamshieldService.ready,
    refetchInterval: 30000,
  });
}

export function useLive() {
  return useQuery({
    queryKey: ['live'],
    queryFn: scamshieldService.live,
    refetchInterval: 15000,
  });
}

export function useMetrics() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: scamshieldService.metrics,
    refetchInterval: 10000,
  });
}

export function useAnalyzeText() {
  return useMutation({
    mutationFn: (text: string) => scamshieldService.analyzeText(text),
  });
}

export function useAnalyzeImage() {
  return useMutation({
    mutationFn: (file: File) => scamshieldService.analyzeImage(file),
  });
}
