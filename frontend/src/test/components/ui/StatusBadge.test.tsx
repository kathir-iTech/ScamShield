import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StatusBadge } from '@/components/ui/status-badge';
import { ShieldCheck } from 'lucide-react';

const infoStatus = { variant: 'info' as const, icon: ShieldCheck, label: 'Test Label' };

describe('StatusBadge', () => {
  it('renders label text', () => {
    render(<StatusBadge status={infoStatus} />);
    expect(screen.getByText('Test Label')).toBeInTheDocument();
  });

  it('renders with icon by default', () => {
    const { container } = render(<StatusBadge status={infoStatus} />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('hides icon when showIcon is false', () => {
    const { container } = render(<StatusBadge status={infoStatus} showIcon={false} />);
    expect(container.querySelector('svg')).not.toBeInTheDocument();
  });

  it('applies size class for sm', () => {
    const { container } = render(<StatusBadge status={infoStatus} size="sm" />);
    expect(container.firstChild).toHaveClass('text-xs');
  });

  it('applies size class for md', () => {
    const { container } = render(<StatusBadge status={infoStatus} size="md" />);
    expect(container.firstChild).toHaveClass('text-sm');
  });

  it('uses custom icon over status icon', () => {
    const { container } = render(
      <StatusBadge status={infoStatus} icon={ShieldCheck} />
    );
    expect(container.querySelector('svg')).toBeInTheDocument();
  });
});
