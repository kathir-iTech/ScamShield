import { cn } from '@/utils/cn';
import type { StatusConfig } from '@/design/status';
import type { LucideIcon } from 'lucide-react';

interface StatusBadgeProps {
  status: StatusConfig;
  icon?: LucideIcon;
  size?: 'sm' | 'md';
  showIcon?: boolean;
  className?: string;
}

const variantStyles: Record<string, string> = {
  success: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300',
  warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300',
  danger: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300',
  info: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300',
  neutral: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
};

export function StatusBadge({ status, icon: IconOverride, size = 'sm', showIcon = true, className }: StatusBadgeProps) {
  const Icon = IconOverride ?? status.icon;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full font-medium',
        size === 'sm' ? 'px-2.5 py-0.5 text-xs' : 'px-3 py-1 text-sm',
        variantStyles[status.variant],
        className
      )}
    >
      {showIcon && <Icon className={size === 'sm' ? 'h-3 w-3' : 'h-3.5 w-3.5'} />}
      {status.label}
    </span>
  );
}
