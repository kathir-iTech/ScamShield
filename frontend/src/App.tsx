import * as Sentry from '@sentry/react';
import { Providers } from '@/app/providers';
import { AnalysisProvider } from '@/features/analysis/context/analysis-context';
import { AppRouter } from '@/app/router';
import { AnimatedBackground } from '@/components/ui/animated-background';

export default function App() {
  return (
    <Sentry.ErrorBoundary fallback={<SentryFallback />}>
      <Providers>
        <AnalysisProvider>
          <AppRouter />
        </AnalysisProvider>
      </Providers>
    </Sentry.ErrorBoundary>
  );
}

function SentryFallback() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-5 bg-[#08080c] p-8 text-center">
      <AnimatedBackground />
      <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-danger/10 text-danger text-4xl">
        !
      </div>
      <h1 className="text-xl font-bold text-text-primary">Something went wrong</h1>
      <p className="max-w-md text-sm text-text-secondary">
        We've encountered an unexpected error. Our team has been notified.
      </p>
      <button
        onClick={() => window.location.reload()}
        className="glass-button inline-flex h-11 items-center gap-2 rounded-xl px-5 text-sm font-semibold text-white"
      >
        Reload page
      </button>
    </div>
  );
}
