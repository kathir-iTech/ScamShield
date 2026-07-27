import type { LucideIcon } from 'lucide-react';
import { cn } from '@/utils/cn';

const variantStyles: Record<string, string> = {
  success: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  warning: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  danger: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  info: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  neutral: 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400',
};

interface StatusBadgeProps {
  label?: string;
  variant?: string;
  size?: 'sm' | 'md';
  className?: string;
  icon?: LucideIcon;
  status?: { variant: string; label: string; icon?: LucideIcon };
  showIcon?: boolean;
}

export function StatusBadge({ label, variant = 'neutral', size = 'sm', status, icon: iconProp, showIcon = true, className }: StatusBadgeProps) {
  const resolvedVariant = status?.variant || variant;
  const resolvedLabel = status?.label || label || '';
  const Icon = iconProp || status?.icon || null;

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-medium',
        size === 'sm' ? 'px-2.5 py-0.5 text-xs' : 'px-3 py-1 text-sm',
        variantStyles[resolvedVariant] || variantStyles.neutral,
        className
      )}
    >
      {Icon && showIcon && <Icon className="h-3.5 w-3.5" aria-hidden="true" />}
      {resolvedLabel}
    </span>
  );
}
