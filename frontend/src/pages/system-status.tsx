import { useHealth } from '@/hooks/use-scamshield';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { PageTransition } from '@/components/ui/page-transition';
import { Activity, ShieldCheck, ShieldAlert } from 'lucide-react';

export default function SystemStatus() {
  const { data: health, isLoading, isError } = useHealth();

  return (
    <PageTransition>
      <div className="mx-auto max-w-xl space-y-8">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 dark:bg-emerald-900/20">
            <Activity className="h-6 w-6 text-emerald-500" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Status</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">Service health at a glance.</p>
        </div>

        {isLoading && (
          <Card>
            <CardContent className="py-8 text-center">
              <div className="mx-auto h-8 w-8 animate-thinking rounded-full bg-emerald-500/20" />
              <p className="mt-3 text-sm text-zinc-500">Checking service health...</p>
            </CardContent>
          </Card>
        )}

        {health && (
          <>
            <Card>
              <CardContent className="py-6">
                <div className="flex items-center justify-center gap-3">
                  <div className={`flex h-12 w-12 items-center justify-center rounded-full ${
                    health.status === 'healthy' ? 'bg-emerald-100 dark:bg-emerald-900/30' : 'bg-red-100 dark:bg-red-900/30'
                  }`}>
                    {health.status === 'healthy'
                      ? <ShieldCheck className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
                      : <ShieldAlert className="h-6 w-6 text-red-600 dark:text-red-400" />
                    }
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
                      {health.status === 'healthy' ? 'All systems normal' : 'Service degraded'}
                    </p>
                    <p className="text-sm text-zinc-500">{health.status}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="space-y-4 py-6">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-zinc-500">Model</span>
                  <Badge variant={health.model_loaded ? 'success' : 'destructive'}>
                    {health.model_loaded ? 'Loaded' : 'Unavailable'}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-zinc-500">Uptime</span>
                  <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                    {Math.floor(health.uptime_seconds / 3600)}h {Math.floor((health.uptime_seconds % 3600) / 60)}m
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-zinc-500">Version</span>
                  <span className="text-sm text-zinc-500">{health.version}</span>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {isError && (
          <Card>
            <CardContent className="py-6 text-center">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
                <ShieldAlert className="h-6 w-6 text-red-500" />
              </div>
              <p className="text-sm font-medium text-zinc-900 dark:text-zinc-50">Service unreachable</p>
              <p className="mt-1 text-sm text-zinc-500">Check your connection or try again later.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </PageTransition>
  );
}
