import { AlertTriangle, WifiOff, Clock, Bug } from 'lucide-react';

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
    <div className="glass rounded-2xl p-8 text-center animate-scale-in" role="alert">
      <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-danger/10 text-danger">
        <Icon className="h-6 w-6" aria-hidden="true" />
      </div>
      <div className="space-y-1">
        <h3 className="text-sm font-semibold text-text-primary">
          {title ?? config.label}
        </h3>
        <p className="max-w-md mx-auto text-sm text-text-secondary">{message}</p>
      </div>
      <div className="mt-5 flex justify-center gap-3">
        {onRetry && (
          <button onClick={onRetry} className="glass-button inline-flex h-10 items-center gap-1.5 rounded-xl px-5 text-sm font-semibold text-white">
            Retry
          </button>
        )}
        {onNavigate && (
          <button onClick={onNavigate.onClick} className="glass inline-flex h-10 items-center gap-1.5 rounded-xl px-5 text-sm font-medium text-text-secondary hover:text-text-primary transition-all duration-200">
            {onNavigate.label}
          </button>
        )}
      </div>
    </div>
  );
}
