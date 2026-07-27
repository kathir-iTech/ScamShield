import * as Sentry from '@sentry/react';
import { Providers } from '@/app/providers';
import { AnalysisProvider } from '@/features/analysis/context/analysis-context';
import { AppRouter } from '@/app/router';

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
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-zinc-50 p-8 text-center dark:bg-zinc-950">
      <div className="rounded-full bg-red-100 p-4 dark:bg-red-900/30">
        <span className="text-3xl">&#9888;</span>
      </div>
      <h1 className="text-xl font-bold text-zinc-900 dark:text-zinc-50">Something went wrong</h1>
      <p className="max-w-md text-sm text-zinc-500 dark:text-zinc-400">
        We've encountered an unexpected error. Our team has been notified.
      </p>
      <button
        onClick={() => window.location.reload()}
        className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
      >
        Reload page
      </button>
    </div>
  );
}
