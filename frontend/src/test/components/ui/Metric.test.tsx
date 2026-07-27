import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Metric } from '@/components/ui/metric';

describe('Metric', () => {
  it('renders label and value', () => {
    render(<Metric label="Score" value="85%" />);
    expect(screen.getByText('Score')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('renders with icon', () => {
    const { container } = render(<Metric label="Score" value="85%" icon={<span>🔢</span>} />);
    expect(container.querySelector('span')).toBeInTheDocument();
  });

  it('applies sm size', () => {
    const { container } = render(<Metric label="Score" value="85%" size="sm" />);
    expect(container.querySelector('.text-sm')).toBeInTheDocument();
  });

  it('applies lg size', () => {
    const { container } = render(<Metric label="Score" value="85%" size="lg" />);
    expect(container.querySelector('.text-2xl')).toBeInTheDocument();
  });
});
