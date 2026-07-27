import { Component, type ReactNode, type ErrorInfo } from 'react';
import { diagnostics } from '@/utils/diagnostics';
import { monitor } from '@/services/monitoring';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    diagnostics.recordRenderError(error, info.componentStack || 'unknown');
    monitor.error('Render error', {
      message: error.message,
      componentStack: info.componentStack,
    });
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex flex-col items-center justify-center gap-5 p-10 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-danger/10 text-danger text-2xl">
            !
          </div>
          <h2 className="text-lg font-semibold text-text-primary">Something went wrong</h2>
          <p className="max-w-md text-sm text-text-secondary">
            {this.state.error?.message || 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="glass-button inline-flex h-11 items-center gap-2 rounded-xl px-6 text-sm font-semibold text-white"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
