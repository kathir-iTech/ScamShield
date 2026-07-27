import { type ReactNode, createElement } from 'react';
import { cn } from '@/utils/cn';

interface SectionProps {
  children: ReactNode;
  className?: string;
  title?: string;
  description?: string;
  as?: string;
}

export function Section({ children, className, title, description, as = 'section' }: SectionProps) {
  return createElement(
    as,
    { className: cn(className) },
    title && <h3 className="mb-3 text-sm font-medium text-text-primary">{title}</h3>,
    description && <p className="mb-3 text-sm text-text-secondary">{description}</p>,
    children
  );
}
