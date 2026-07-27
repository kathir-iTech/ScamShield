import { useHealth } from '@/hooks/use-scamshield';
import { PageTransition } from '@/components/ui/page-transition';
import { Activity, ShieldCheck, ShieldAlert } from 'lucide-react';

export default function SystemStatus() {
  const { data: health, isLoading, isError } = useHealth();

  return (
    <PageTransition>
      <div className="mx-auto max-w-xl px-6 py-16 sm:py-20 space-y-8">
        <div className="text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass">
            <Activity className="h-6 w-6 text-accent" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">Status</h1>
          <p className="mt-2 text-text-secondary/70">Service health at a glance.</p>
        </div>

        {isLoading && (
          <div className="glass rounded-2xl p-10 text-center animate-fade-in">
            <div className="mx-auto flex items-center justify-center gap-2">
              <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
              <span className="h-2 w-2 rounded-full bg-accent animate-pulse" style={{ animationDelay: '200ms' }} />
              <span className="h-2 w-2 rounded-full bg-accent animate-pulse" style={{ animationDelay: '400ms' }} />
            </div>
            <p className="mt-4 text-sm text-text-secondary">Checking service health...</p>
          </div>
        )}

        {health && (
          <>
            <div className="glass rounded-2xl p-7 animate-slide-up">
              <div className="flex items-center justify-center gap-4">
                <div className={`flex h-14 w-14 items-center justify-center rounded-xl ${
                  health.status === 'healthy' ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'
                }`}>
                  {health.status === 'healthy'
                    ? <ShieldCheck className="h-7 w-7" />
                    : <ShieldAlert className="h-7 w-7" />
                  }
                </div>
                <div>
                  <p className="text-lg font-semibold text-text-primary">
                    {health.status === 'healthy' ? 'All systems normal' : 'Service degraded'}
                  </p>
                  <p className="text-sm text-text-secondary">{health.status}</p>
                </div>
              </div>
            </div>

            <div className="glass rounded-2xl p-7 animate-slide-up stagger-2">
              <div className="space-y-5">
                {[
                  { label: 'Model', value: health.model_loaded ? 'Loaded' : 'Unavailable', status: health.model_loaded ? 'success' : 'danger' },
                  { label: 'Uptime', value: `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m`, status: 'neutral' },
                  { label: 'Version', value: health.version, status: 'neutral' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary">{item.label}</span>
                    <span className={`text-sm font-medium ${
                      item.status === 'success' ? 'text-success' :
                      item.status === 'danger' ? 'text-danger' :
                      'text-text-primary'
                    }`}>
                      {item.value}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        {isError && (
          <div className="glass rounded-2xl p-8 text-center animate-slide-up">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-danger/10 text-danger">
              <ShieldAlert className="h-7 w-7" />
            </div>
            <p className="text-base font-semibold text-text-primary">Service unreachable</p>
            <p className="mt-1 text-sm text-text-secondary">Check your connection or try again later.</p>
          </div>
        )}
      </div>
    </PageTransition>
  );
}
