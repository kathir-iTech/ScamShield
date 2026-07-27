import { useState, type ReactNode } from 'react';
import { cn } from '@/utils/cn';
import { ChevronDown } from 'lucide-react';

interface ExpandablePanelProps {
  title: string;
  count?: number;
  defaultOpen?: boolean;
  children: ReactNode;
  className?: string;
}

export function ExpandablePanel({ title, count, defaultOpen = false, children, className }: ExpandablePanelProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={cn('glass rounded-2xl overflow-hidden transition-all duration-300', className)}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-6 py-4 text-left transition-colors duration-200 hover:bg-glass-hover"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-text-primary">{title}</span>
          {count !== undefined && (
            <span className="rounded-full bg-glass-border px-2 py-0.5 text-xs text-text-tertiary tabular-nums">
              {count}
            </span>
          )}
        </div>
        <ChevronDown
          className={cn(
            'h-4 w-4 text-text-tertiary transition-transform duration-200',
            open && 'rotate-180'
          )}
        />
      </button>
      <div
        className={cn(
          'grid transition-all duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]',
          open ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'
        )}
      >
        <div className="overflow-hidden">
          <div className="px-6 pb-6">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
