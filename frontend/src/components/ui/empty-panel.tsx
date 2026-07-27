import type { LucideIcon } from 'lucide-react';
import { cn } from '@/utils/cn';

interface EmptyPanelProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyPanel({ icon: Icon, title, description, action, className }: EmptyPanelProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3 py-12 text-center', className)}>
      {Icon && (
        <div className="rounded-full bg-zinc-100 p-3 dark:bg-zinc-800">
          <Icon className="h-6 w-6 text-zinc-400" />
        </div>
      )}
      <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{title}</h3>
      {description && (
        <p className="max-w-sm text-sm text-zinc-500 dark:text-zinc-400">{description}</p>
      )}
      {action}
    </div>
  );
}
