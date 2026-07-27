import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { InfoRow } from '@/components/ui/info-row';

describe('InfoRow', () => {
  it('renders label and value', () => {
    render(<InfoRow label="Status" value="Active" />);
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('renders value as ReactNode', () => {
    render(<InfoRow label="Count" value={<span>5</span>} />);
    expect(screen.getByText('5')).toBeInTheDocument();
  });
});
