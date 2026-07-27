import { cn } from '@/utils/cn';
import { Lock, Zap, Shield } from 'lucide-react';

const trustItems = [
  { icon: Lock, label: 'No account' },
  { icon: Zap, label: 'Instant' },
  { icon: Shield, label: 'Private' },
];

interface TrustBadgeProps {
  className?: string;
}

export function TrustBadge({ className }: TrustBadgeProps) {
  return (
    <div className={cn('flex items-center justify-center gap-6', className)}>
      {trustItems.map((item) => (
        <div key={item.label} className="flex items-center gap-1.5 text-xs text-text-tertiary">
          <item.icon className="h-3.5 w-3.5 text-accent/60" aria-hidden="true" />
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
}
