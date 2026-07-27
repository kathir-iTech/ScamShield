import { cn } from '@/utils/cn';
import { ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';

interface VerdictBannerProps {
  verdict: 'safe' | 'scam' | 'suspicious';
  title: string;
  description?: string;
  confidence: number;
  riskLevel: string;
  assessmentBand: string;
  actions?: React.ReactNode;
  className?: string;
}

const verdictConfig = {
  safe: {
    icon: ShieldCheck,
    bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    border: 'border-emerald-200 dark:border-emerald-800',
    iconBg: 'bg-emerald-100 dark:bg-emerald-900/40',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    titleColor: 'text-emerald-900 dark:text-emerald-50',
    badge: 'bg-emerald-500 text-white',
    confidenceBar: 'bg-emerald-500',
  },
  suspicious: {
    icon: AlertTriangle,
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    border: 'border-amber-200 dark:border-amber-800',
    iconBg: 'bg-amber-100 dark:bg-amber-900/40',
    iconColor: 'text-amber-600 dark:text-amber-400',
    titleColor: 'text-amber-900 dark:text-amber-50',
    badge: 'bg-amber-500 text-white',
    confidenceBar: 'bg-amber-500',
  },
  scam: {
    icon: ShieldAlert,
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    iconBg: 'bg-red-100 dark:bg-red-900/40',
    iconColor: 'text-red-600 dark:text-red-400',
    titleColor: 'text-red-900 dark:text-red-50',
    badge: 'bg-red-500 text-white',
    confidenceBar: 'bg-red-500',
  },
};

export function VerdictBanner({ verdict, title, description, confidence, riskLevel, assessmentBand, actions, className }: VerdictBannerProps) {
  const cfg = verdictConfig[verdict];
  const Icon = cfg.icon;

  return (
    <div
      className={cn(
        'rounded-2xl border p-8 text-center',
        cfg.bg,
        cfg.border,
        'animate-scale-in',
        className
      )}
      role="status"
      aria-live="polite"
      aria-atomic="true"
    >
      <div className={cn('mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full', cfg.iconBg)}>
        <Icon className={cn('h-8 w-8', cfg.iconColor)} aria-hidden="true" />
      </div>

      <h2 className={cn('text-2xl font-bold tracking-tight', cfg.titleColor)}>
        {title}
      </h2>

      {description && (
        <p className="mx-auto mt-3 max-w-md text-sm text-zinc-600 dark:text-zinc-300">
          {description}
        </p>
      )}

      <div className="mt-4 flex items-center justify-center gap-3">
        <span className={cn('rounded-full px-3 py-1 text-xs font-semibold', cfg.badge)}>
          {confidence}% confidence
        </span>
        <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
          {riskLevel}
        </span>
      </div>

      <div className="mx-auto mt-4 max-w-xs">
        <div className="h-2 rounded-full bg-zinc-200 dark:bg-zinc-700">
          <div
            className={cn('h-full rounded-full animate-progress', cfg.confidenceBar)}
            style={{ width: `${confidence}%` }}
          />
        </div>
      </div>

      <p className="mt-4 text-sm text-zinc-500 dark:text-zinc-400">
        {assessmentBand}
      </p>

      {actions && (
        <div className="mt-6 flex items-center justify-center gap-3">
          {actions}
        </div>
      )}
    </div>
  );
}
