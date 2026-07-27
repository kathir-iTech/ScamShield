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
        {icon && <span className="text-text-tertiary">{icon}</span>}
        <p className="text-xs font-medium text-text-secondary">{label}</p>
      </div>
      <p
        className={cn(
          'font-semibold text-text-primary',
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
