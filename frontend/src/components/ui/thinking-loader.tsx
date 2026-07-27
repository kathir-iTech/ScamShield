import { useState, useEffect } from 'react';
import { cn } from '@/utils/cn';

interface ThinkingLoaderProps {
  phrases: string[];
  interval?: number;
  className?: string;
}

export function ThinkingLoader({ phrases, interval = 2500, className }: ThinkingLoaderProps) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((i) => (i + 1) % phrases.length);
    }, interval);
    return () => clearInterval(timer);
  }, [phrases.length, interval]);

  return (
    <div className={cn('flex items-center gap-3', className)} role="status" aria-live="polite">
      <div className="flex items-center gap-1">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-thinking" style={{ animationDelay: '0ms' }} />
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-thinking" style={{ animationDelay: '200ms' }} />
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-thinking" style={{ animationDelay: '400ms' }} />
      </div>
      <span className="text-sm text-zinc-500 dark:text-zinc-400">
        {phrases[index]}
      </span>
    </div>
  );
}
