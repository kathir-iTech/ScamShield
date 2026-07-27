import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EmptyPanel } from '@/components/ui/empty-panel';

describe('EmptyPanel', () => {
  it('renders title', () => {
    render(<EmptyPanel title="No data" />);
    expect(screen.getByText('No data')).toBeInTheDocument();
  });

  it('renders description', () => {
    render(<EmptyPanel title="No data" description="Nothing to show" />);
    expect(screen.getByText('Nothing to show')).toBeInTheDocument();
  });

  it('renders action slot', () => {
    render(<EmptyPanel title="No data" action={<button>Retry</button>} />);
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });
});
