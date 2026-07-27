import { RefreshCw } from 'lucide-react';

interface RetryButtonProps {
  onRetry: () => void;
  label?: string;
}

export function RetryButton({ onRetry, label = 'Retry' }: RetryButtonProps) {
  return (
    <button
      onClick={onRetry}
      className="glass inline-flex h-9 items-center gap-1.5 rounded-xl px-4 text-xs font-medium text-text-secondary hover:text-text-primary transition-all duration-200"
    >
      <RefreshCw className="h-4 w-4" />
      {label}
    </button>
  );
}
