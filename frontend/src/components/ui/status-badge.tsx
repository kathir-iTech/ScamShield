import type { LucideIcon } from 'lucide-react';
import { cn } from '@/utils/cn';

const variantStyles: Record<string, string> = {
  success: 'bg-success/20 text-success border border-success/20',
  warning: 'bg-warning/20 text-warning border border-warning/20',
  danger: 'bg-danger/20 text-danger border border-danger/20',
  info: 'bg-accent/20 text-accent border border-accent/20',
  neutral: 'bg-glass text-text-secondary border border-glass-border',
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
