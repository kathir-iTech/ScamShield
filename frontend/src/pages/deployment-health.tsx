import { useState, useEffect } from 'react';
import { health } from '@/services/scamshield';
import type { HealthResponse } from '@/types';

export function DeploymentHealth() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await health();
        setData(res);
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to fetch health');
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds: number) => {
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${d}d ${h}h ${m}m`;
  };

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <div className="rounded-xl bg-white p-8 text-center shadow-lg dark:bg-zinc-900">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
            <svg className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="mb-2 text-xl font-semibold text-zinc-900 dark:text-zinc-100">Service Unreachable</h2>
          <p className="text-zinc-500 dark:text-zinc-400">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-50 p-8 dark:bg-zinc-950">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8 flex items-center gap-3">
          <div className={`h-4 w-4 rounded-full ${data.status === 'pass' ? 'bg-emerald-500' : 'bg-red-500'}`} />
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">Deployment Health</h1>
          <span className="ml-auto rounded-full bg-zinc-200 px-3 py-1 text-sm text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
            v{data.version}
          </span>
        </div>

        <div className="mb-6 grid gap-6 md:grid-cols-3">
          <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-zinc-900">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Uptime</p>
            <p className="mt-1 text-2xl font-bold text-zinc-900 dark:text-zinc-100">{formatUptime(data.uptime_seconds)}</p>
          </div>
          <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-zinc-900">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Service</p>
            <p className="mt-1 text-2xl font-bold text-zinc-900 dark:text-zinc-100">{data.service}</p>
          </div>
          <div className="rounded-xl bg-white p-6 shadow-sm dark:bg-zinc-900">
            <p className="text-sm text-zinc-500 dark:text-zinc-400">Availability</p>
            <p className="mt-1 text-2xl font-bold text-zinc-900 dark:text-zinc-100">{data.service_availability}</p>
          </div>
        </div>

        <div className="mb-6 rounded-xl bg-white p-6 shadow-sm dark:bg-zinc-900">
          <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">System Checks</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-zinc-600 dark:text-zinc-400">ML Model</span>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${data.model_loaded ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                {data.model_loaded ? 'Loaded' : 'Unavailable'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-600 dark:text-zinc-400">Configuration</span>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${data.configuration_loaded ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                {data.configuration_loaded ? 'Valid' : 'Invalid'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-600 dark:text-zinc-400">Active Requests</span>
              <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
                {data.active_requests}
              </span>
            </div>
          </div>
        </div>

        <div className="mb-6 rounded-xl bg-white p-6 shadow-sm dark:bg-zinc-900">
          <h2 className="mb-4 text-lg font-semibold text-zinc-900 dark:text-zinc-100">Dependencies</h2>
          <div className="space-y-3">
            {data.dependency_status && (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-600 dark:text-zinc-400">Model</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${data.dependency_status.model === 'loaded' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                    {data.dependency_status.model}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-600 dark:text-zinc-400">Vectorizer</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${data.dependency_status.vectorizer === 'loaded' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                    {data.dependency_status.vectorizer}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-600 dark:text-zinc-400">Config</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${data.dependency_status.config === 'valid' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                    {data.dependency_status.config}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
