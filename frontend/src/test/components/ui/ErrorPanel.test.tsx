import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorPanel } from '@/components/ui/error-panel';

describe('ErrorPanel', () => {
  it('renders default message', () => {
    render(<ErrorPanel message="Something broke" />);
    expect(screen.getByText('Something broke')).toBeInTheDocument();
  });

  it('renders custom title', () => {
    render(<ErrorPanel title="Error" message="Something broke" />);
    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('shows retry button when onRetry provided', () => {
    render(<ErrorPanel message="Failed" onRetry={() => {}} />);
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('calls onRetry when clicked', () => {
    const onRetry = vi.fn();
    render(<ErrorPanel message="Failed" onRetry={onRetry} />);
    fireEvent.click(screen.getByText('Retry'));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('shows navigation button when onNavigate provided', () => {
    render(<ErrorPanel message="Lost" onNavigate={{ label: 'Go Home', onClick: () => {} }} />);
    expect(screen.getByText('Go Home')).toBeInTheDocument();
  });

  it('uses validation icon for validation type', () => {
    const { container } = render(<ErrorPanel message="Invalid" type="validation" />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });
});
