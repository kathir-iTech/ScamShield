import { useState, useEffect, useCallback } from 'react';
import { cn } from '@/utils/cn';

interface Stage {
  id: string;
  label: string;
  icon: string;
}

const PIPELINE_STAGES: Stage[] = [
  { id: 'reading', label: 'Reading message...', icon: '👁' },
  { id: 'entities', label: 'Extracting entities...', icon: '🔍' },
  { id: 'intent', label: 'Understanding intent...', icon: '🧠' },
  { id: 'patterns', label: 'Checking scam patterns...', icon: '⚡' },
  { id: 'threats', label: 'Comparing with known threats...', icon: '🛡' },
  { id: 'crossval', label: 'Cross validating...', icon: '✓' },
  { id: 'explanation', label: 'Generating explanation...', icon: '✍' },
  { id: 'recommendations', label: 'Preparing recommendations...', icon: '📋' },
];

interface PipelineLoaderProps {
  onComplete?: () => void;
  className?: string;
}

export function PipelineLoader({ onComplete, className }: PipelineLoaderProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [completedIndex, setCompletedIndex] = useState(-1);
  const [progress, setProgress] = useState(0);

  const advanceStage = useCallback(() => {
    setCompletedIndex((prev) => prev + 1);
    setActiveIndex((prev) => prev + 1);
    setProgress(0);
  }, []);

  useEffect(() => {
    if (activeIndex >= PIPELINE_STAGES.length) {
      onComplete?.();
      return;
    }

    const stageDuration = 2000 + Math.random() * 1500;
    const progressInterval = 50;
    const steps = stageDuration / progressInterval;
    let currentStep = 0;

    const progressTimer = setInterval(() => {
      currentStep++;
      setProgress(Math.min(currentStep / steps, 1));
    }, progressInterval);

    const advanceTimer = setTimeout(() => {
      advanceStage();
    }, stageDuration);

    return () => {
      clearInterval(progressTimer);
      clearTimeout(advanceTimer);
    };
  }, [activeIndex, advanceStage, onComplete]);

  return (
    <div className={cn('w-full', className)} role="status" aria-live="polite" aria-label="Analysing message">
      <div className="relative">
        <div className="absolute left-[15px] top-2 bottom-2 w-[2px] bg-glass-border">
          <div
            className="w-full bg-accent transition-all duration-500 ease-out"
            style={{ height: `${((completedIndex + 1) / PIPELINE_STAGES.length) * 100}%` }}
          />
        </div>
        <div className="space-y-0">
          {PIPELINE_STAGES.map((stage, index) => {
            const isCompleted = index <= completedIndex;
            const isActive = index === activeIndex && activeIndex < PIPELINE_STAGES.length;
            const isPending = index > activeIndex;

            return (
              <div
                key={stage.id}
                className={cn(
                  'relative flex items-center gap-4 px-6 py-3 transition-all duration-500',
                  isCompleted && 'opacity-40',
                  isActive && 'opacity-100',
                  isPending && 'opacity-20',
                )}
              >
                <div
                  className={cn(
                    'relative z-10 flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-full text-sm transition-all duration-500',
                    isCompleted && 'bg-accent/20 text-accent',
                    isActive && 'bg-accent/30 text-accent animate-pipeline-glow',
                    isPending && 'bg-glass-border/30 text-text-tertiary',
                  )}
                >
                  {isCompleted ? (
                    <svg className="h-3.5 w-3.5" viewBox="0 0 14 14" fill="none">
                      <path d="M2 7.5L5.5 11L12 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  ) : (
                    <span>{stage.icon}</span>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p
                    className={cn(
                      'text-sm font-medium transition-all duration-300',
                      isCompleted && 'text-text-secondary',
                      isActive && 'text-text-primary',
                      isPending && 'text-text-tertiary',
                    )}
                  >
                    {stage.label}
                  </p>
                  {isActive && (
                    <div className="mt-1.5 h-[3px] overflow-hidden rounded-full bg-glass-border">
                      <div
                        className="h-full rounded-full bg-accent animate-progress-beam transition-all duration-150"
                        style={{ width: `${progress * 100}%` }}
                      />
                    </div>
                  )}
                </div>
                {isCompleted && (
                  <span className="text-xs text-text-tertiary tabular-nums shrink-0">
                    {((index + 1) * 12.5).toFixed(0)}%
                  </span>
                )}
                {isActive && (
                  <span className="text-xs text-accent tabular-nums shrink-0 font-medium">
                    {(progress * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
