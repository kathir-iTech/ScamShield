import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { PageSkeleton } from '@/components/ui/page-skeleton';

describe('PageSkeleton', () => {
  it('renders dashboard variant by default', () => {
    const { container } = render(<PageSkeleton />);
    expect(container.firstChild).toHaveAttribute('aria-busy', 'true');
  });

  it('renders analysis variant', () => {
    const { container } = render(<PageSkeleton variant="analysis" />);
    expect(container.firstChild).toHaveAttribute('aria-busy', 'true');
    expect(container.firstChild).toHaveAttribute('aria-label', 'Loading text analysis page');
  });

  it('renders report variant', () => {
    const { container } = render(<PageSkeleton variant="report" />);
    expect(container.firstChild).toHaveAttribute('aria-busy', 'true');
    expect(container.firstChild).toHaveAttribute('aria-label', 'Loading report page');
  });

  it('renders system variant', () => {
    const { container } = render(<PageSkeleton variant="system" />);
    expect(container.firstChild).toHaveAttribute('aria-busy', 'true');
    expect(container.firstChild).toHaveAttribute('aria-label', 'Loading system status page');
  });
});
