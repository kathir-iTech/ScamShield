import { AlertTriangle, WifiOff, Clock, Bug } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface ErrorPanelProps {
  title?: string;
  message: string;
  type?: 'validation' | 'network' | 'unavailable' | 'timeout' | 'unexpected';
  onRetry?: () => void;
  onNavigate?: { label: string; onClick: () => void };
}

const errorConfig = {
  validation: { icon: AlertTriangle, label: 'Validation Error' },
  network: { icon: WifiOff, label: 'Network Error' },
  unavailable: { icon: AlertTriangle, label: 'Service Unavailable' },
  timeout: { icon: Clock, label: 'Request Timeout' },
  unexpected: { icon: Bug, label: 'Unexpected Error' },
};

export function ErrorPanel({ title, message, type = 'unexpected', onRetry, onNavigate }: ErrorPanelProps) {
  const config = errorConfig[type] ?? errorConfig.unexpected;
  const Icon = config.icon;

  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-4 p-8 text-center">
        <div className="rounded-full bg-red-100 p-3 dark:bg-red-900/30">
          <Icon className="h-6 w-6 text-red-500" aria-hidden="true" />
        </div>
        <div className="space-y-1">
          <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
            {title ?? config.label}
          </h3>
          <p className="max-w-md text-sm text-zinc-500 dark:text-zinc-400">{message}</p>
        </div>
        <div className="flex gap-3">
          {onRetry && <Button onClick={onRetry}>Retry</Button>}
          {onNavigate && (
            <Button variant="outline" onClick={onNavigate.onClick}>
              {onNavigate.label}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
