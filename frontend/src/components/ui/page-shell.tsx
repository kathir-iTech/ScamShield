import { type HTMLAttributes } from 'react';
import { cn } from '@/utils/cn';

interface PageShellProps extends HTMLAttributes<HTMLDivElement> {
  heading?: string;
  subtitle?: string;
}

export function PageShell({ heading, subtitle, children, className, ...props }: PageShellProps) {
  return (
    <div className={cn('mx-auto max-w-4xl px-4 py-10 sm:px-6 sm:py-16', className)} {...props}>
      {heading && (
        <div className="mb-12">
          <h1 className="text-4xl font-bold tracking-tight text-text-primary sm:text-5xl">
            {heading}
          </h1>
          {subtitle && (
            <p className="mt-3 text-lg text-text-secondary/70">
              {subtitle}
            </p>
          )}
        </div>
      )}
      {children}
    </div>
  );
}
