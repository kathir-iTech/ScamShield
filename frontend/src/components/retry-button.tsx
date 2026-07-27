import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';

interface RetryButtonProps {
  onRetry: () => void;
  label?: string;
}

export function RetryButton({ onRetry, label = 'Retry' }: RetryButtonProps) {
  return (
    <Button variant="outline" size="sm" onClick={onRetry}>
      <RefreshCw className="h-4 w-4" />
      {label}
    </Button>
  );
}
