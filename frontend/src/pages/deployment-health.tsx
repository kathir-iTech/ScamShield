import { useState, useEffect } from 'react';
import { health } from '@/services/scamshield';
import type { HealthResponse } from '@/types';
import { ShieldAlert } from 'lucide-react';

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
      <div className="flex min-h-screen items-center justify-center bg-[#08080c]">
        <div className="glass rounded-2xl p-10 text-center max-w-md animate-scale-in">
          <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-xl bg-danger/10 text-danger">
            <ShieldAlert className="h-8 w-8" />
          </div>
          <h2 className="text-xl font-semibold text-text-primary mb-2">Service Unreachable</h2>
          <p className="text-sm text-text-secondary">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#08080c]">
        <div className="flex gap-2">
          <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
          <span className="h-2 w-2 rounded-full bg-accent animate-pulse" style={{ animationDelay: '200ms' }} />
          <span className="h-2 w-2 rounded-full bg-accent animate-pulse" style={{ animationDelay: '400ms' }} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#08080c] px-6 py-10">
      <div className="mx-auto max-w-4xl">
        <div className="flex items-center gap-4 mb-10">
          <div className={`h-3 w-3 rounded-full ${data.status === 'pass' ? 'bg-success' : 'bg-danger'} animate-pulse`} />
          <h1 className="text-2xl font-bold text-text-primary">Deployment Health</h1>
          <span className="ml-auto glass rounded-full px-3 py-1 text-xs text-text-secondary">
            v{data.version}
          </span>
        </div>

        <div className="grid gap-4 md:grid-cols-3 mb-6">
          {[
            { label: 'Uptime', value: formatUptime(data.uptime_seconds) },
            { label: 'Service', value: data.service },
            { label: 'Availability', value: data.service_availability },
          ].map((item) => (
            <div key={item.label} className="glass rounded-2xl p-6 animate-slide-up">
              <p className="text-sm text-text-secondary">{item.label}</p>
              <p className="mt-1 text-2xl font-bold text-text-primary">{item.value}</p>
            </div>
          ))}
        </div>

        <div className="glass rounded-2xl p-7 mb-6 animate-slide-up stagger-2">
          <h2 className="text-sm font-semibold text-text-primary mb-5">System Checks</h2>
          <div className="space-y-4">
            {[
              { label: 'ML Model', value: data.dependencies?.model === 'loaded' ? 'Loaded' : 'Unavailable', status: data.dependencies?.model === 'loaded' },
              { label: 'Configuration', value: data.dependencies?.config === 'valid' ? 'Valid' : 'Invalid', status: data.dependencies?.config === 'valid' },
              { label: 'Active Requests', value: String(data.active_requests), status: true },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between">
                <span className="text-sm text-text-secondary">{item.label}</span>
                <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                  item.status ? 'border-success/20 bg-success/10 text-success' : 'border-danger/20 bg-danger/10 text-danger'
                }`}>
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {data.dependencies && (
          <div className="glass rounded-2xl p-7 animate-slide-up stagger-3">
            <h2 className="text-sm font-semibold text-text-primary mb-5">Dependencies</h2>
            <div className="space-y-4">
              {[
                { label: 'Model', value: data.dependencies.model, status: data.dependencies.model === 'loaded' },
                { label: 'Vectorizer', value: data.dependencies.vectorizer, status: data.dependencies.vectorizer === 'loaded' },
                { label: 'Config', value: data.dependencies.config, status: data.dependencies.config === 'valid' },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <span className="text-sm text-text-secondary">{item.label}</span>
                  <span className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${
                    item.status ? 'border-success/20 bg-success/10 text-success' : 'border-danger/20 bg-danger/10 text-danger'
                  }`}>
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
