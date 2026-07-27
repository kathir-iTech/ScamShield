import type { ReactNode } from 'react';
import { cn } from '@/utils/cn';

interface SectionProps {
  title?: string;
  description?: string;
  children: ReactNode;
  className?: string;
  as?: 'section' | 'div';
  'aria-label'?: string;
}

export function Section({ title, description, children, className, as: Tag = 'section', ...rest }: SectionProps) {
  return (
    <Tag className={cn('space-y-4', className)} {...rest}>
      {(title || description) && (
        <div className="space-y-1">
          {title && (
            <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
              {title}
            </h3>
          )}
          {description && (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">{description}</p>
          )}
        </div>
      )}
      {children}
    </Tag>
  );
}
