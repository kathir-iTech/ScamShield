import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ToastContainer } from '@/components/toast-container';

const sampleToasts = [
  { id: '1', message: 'Success!', type: 'success' as const },
  { id: '2', message: 'Failed!', type: 'error' as const },
];

describe('ToastContainer', () => {
  it('returns null when empty', () => {
    const { container } = render(<ToastContainer toasts={[]} onRemove={() => {}} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders toast messages', () => {
    render(<ToastContainer toasts={sampleToasts} onRemove={() => {}} />);
    expect(screen.getByText('Success!')).toBeInTheDocument();
    expect(screen.getByText('Failed!')).toBeInTheDocument();
  });

  it('calls onRemove when dismiss button clicked', () => {
    const onRemove = vi.fn();
    render(<ToastContainer toasts={sampleToasts} onRemove={onRemove} />);
    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[0]);
    expect(onRemove).toHaveBeenCalledWith('1');
  });

  it('has aria-live region', () => {
    const { container } = render(<ToastContainer toasts={sampleToasts} onRemove={() => {}} />);
    expect(container.firstChild).toHaveAttribute('aria-live', 'polite');
  });

  it('uses role alert on each toast', () => {
    render(<ToastContainer toasts={sampleToasts} onRemove={() => {}} />);
    const alerts = screen.getAllByRole('alert');
    expect(alerts).toHaveLength(2);
  });
});
