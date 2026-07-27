import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CopyButton } from '@/components/ui/copy-button';

describe('CopyButton', () => {
  it('renders with default label', () => {
    render(<CopyButton text="test" />);
    expect(screen.getByText('Copy')).toBeInTheDocument();
  });

  it('renders with custom aria-label', () => {
    render(<CopyButton text="test" label="Copy URL" />);
    expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Copy URL');
  });

  it('shows copied state after click', async () => {
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
    render(<CopyButton text="test" />);
    fireEvent.click(screen.getByRole('button'));
    expect(await screen.findByText('Copied')).toBeInTheDocument();
  });

  it('has accessible label', () => {
    render(<CopyButton text="test" />);
    expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Copy to clipboard');
  });

  it('uses custom aria-label', () => {
    render(<CopyButton text="test" label="Copy this" />);
    expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Copy this');
  });
});
