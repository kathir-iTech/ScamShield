import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from '@/components/ui/badge';

describe('Badge', () => {
  it('renders text content', () => {
    render(<Badge>Scam Alert</Badge>);
    expect(screen.getByText('Scam Alert')).toBeInTheDocument();
  });

  it('renders as span element', () => {
    const { container } = render(<Badge>Test</Badge>);
    expect(container.querySelector('span')).toBeInTheDocument();
  });
});
