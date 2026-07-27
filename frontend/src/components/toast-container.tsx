import { X } from 'lucide-react';
import type { Toast } from '@/hooks/use-toast';

interface ToastContainerProps {
  toasts: Toast[];
  onRemove: (id: string) => void;
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  if (toasts.length === 0) return null;
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" aria-live="polite" aria-atomic="true">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`flex items-center gap-3 rounded-xl px-5 py-3.5 text-sm glass-strong backdrop-blur-2xl border ${
            toast.type === 'success' ? 'border-success/20' :
            toast.type === 'error' ? 'border-danger/20' :
            'border-glass-border'
          }`}
          role="alert"
        >
          <span className={`flex-1 ${
            toast.type === 'error' ? 'text-danger' : 'text-text-primary'
          }`}>
            {toast.message}
          </span>
          <button
            onClick={() => onRemove(toast.id)}
            className="rounded p-0.5 hover:bg-glass-hover text-text-tertiary hover:text-text-primary transition-colors"
            aria-label="Dismiss"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
