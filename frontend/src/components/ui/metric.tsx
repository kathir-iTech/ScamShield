import type { ReactNode } from 'react';
import { cn } from '@/utils/cn';

interface MetricProps {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function Metric({ label, value, icon, className, size = 'md' }: MetricProps) {
  return (
    <div className={cn('space-y-1', className)}>
      <div className="flex items-center gap-1.5">
        {icon && <span className="text-zinc-400">{icon}</span>}
        <p className="text-xs font-medium text-zinc-500 dark:text-zinc-400">{label}</p>
      </div>
      <p
        className={cn(
          'font-semibold text-zinc-900 dark:text-zinc-50',
          size === 'sm' && 'text-sm',
          size === 'md' && 'text-lg',
          size === 'lg' && 'text-2xl'
        )}
      >
        {value}
      </p>
    </div>
  );
}
