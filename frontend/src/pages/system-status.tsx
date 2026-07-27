import { useHealth, useReady, useLive, useMetrics } from '@/hooks/use-scamshield';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { RetryButton } from '@/components/retry-button';
import { PageTransition } from '@/components/ui/page-transition';
import { diagnostics } from '@/utils/diagnostics';
import { getBuildTimestamp } from '@/utils/version';
import { Activity, Heart, Gauge, Server, HardDrive, Bug } from 'lucide-react';

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-zinc-100 py-1 text-sm dark:border-zinc-800">
      <span className="text-zinc-500 dark:text-zinc-400">{label}</span>
      <span className="font-medium text-zinc-900 dark:text-zinc-50">{value}</span>
    </div>
  );
}

export default function SystemStatus() {
  const healthQuery = useHealth();
  const readyQuery = useReady();
  const liveQuery = useLive();
  const metricsQuery = useMetrics();

  const refetchAll = () => {
    healthQuery.refetch();
    readyQuery.refetch();
    liveQuery.refetch();
    metricsQuery.refetch();
  };

  const h = healthQuery.data;
  const m = metricsQuery.data;
  const diagSummary = diagnostics.getSummary();

  return (
    <PageTransition>
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              System Status
            </h1>
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Backend health, readiness, and metrics
            </p>
          </div>
          <RetryButton onRetry={refetchAll} label="Refresh All" />
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Liveness</CardTitle>
              <Heart className="h-4 w-4 text-zinc-400" />
            </CardHeader>
            <CardContent>
              {liveQuery.isLoading ? (
                <Skeleton className="h-6 w-16" />
              ) : liveQuery.isError ? (
                <div className="flex items-center gap-2">
                  <Badge variant="destructive">DOWN</Badge>
                  <RetryButton onRetry={() => liveQuery.refetch()} />
                </div>
              ) : (
                <Badge variant="success">{liveQuery.data?.status?.toUpperCase() || 'ALIVE'}</Badge>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Readiness</CardTitle>
              <Activity className="h-4 w-4 text-zinc-400" />
            </CardHeader>
            <CardContent>
              {readyQuery.isLoading ? (
                <Skeleton className="h-6 w-24" />
              ) : readyQuery.isError ? (
                <div className="flex items-center gap-2">
                  <Badge variant="destructive">UNKNOWN</Badge>
                  <RetryButton onRetry={() => readyQuery.refetch()} />
                </div>
              ) : (
                <Badge
                  variant={
                    readyQuery.data?.status === 'READY' ? 'success' : 'destructive'
                  }
                >
                  {readyQuery.data?.status || 'UNKNOWN'}
                </Badge>
              )}
              {readyQuery.data?.errors && readyQuery.data.errors.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {readyQuery.data.errors.map((err, i) => (
                    <li key={i} className="text-xs text-red-600">
                      {err}
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Health</CardTitle>
              <Gauge className="h-4 w-4 text-zinc-400" />
            </CardHeader>
            <CardContent>
              {healthQuery.isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-6 w-24" />
                  <Skeleton className="h-4 w-32" />
                </div>
              ) : healthQuery.isError ? (
                <div className="flex items-center gap-2">
                  <Badge variant="destructive">DOWN</Badge>
                  <RetryButton onRetry={() => healthQuery.refetch()} />
                </div>
              ) : h ? (
                <div className="space-y-2">
                  <Badge
                    variant={
                      h.status === 'healthy' ? 'success' : 'destructive'
                    }
                  >
                    {h.status?.toUpperCase()}
                  </Badge>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    Model: {h.model_loaded ? 'Loaded' : 'Not loaded'}
                  </p>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    Uptime: {Math.floor(h.uptime_seconds / 60)}m{' '}
                    {h.uptime_seconds % 60}s
                  </p>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    Version: {h.build_version || h.version}
                  </p>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    Active requests: {h.active_requests}
                  </p>
                </div>
              ) : null}
            </CardContent>
          </Card>
        </div>

        {h && (
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">System Resources</CardTitle>
                <HardDrive className="h-4 w-4 text-zinc-400" />
              </CardHeader>
              <CardContent className="space-y-1">
                {h.disk_usage ? (
                  <>
                    <MetricRow label="Disk Total" value={`${h.disk_usage.total_gb} GB`} />
                    <MetricRow label="Disk Used" value={`${h.disk_usage.used_gb} GB`} />
                    <MetricRow label="Disk Free" value={`${h.disk_usage.free_gb} GB (${h.disk_usage.percent_free}%)`} />
                  </>
                ) : (
                  <p className="text-sm text-zinc-400">Disk info unavailable</p>
                )}
                {h.memory_usage ? (
                  <>
                    <MetricRow label="Memory Total" value={`${h.memory_usage.total_gb} GB`} />
                    <MetricRow label="Memory Available" value={`${h.memory_usage.available_gb} GB`} />
                    <MetricRow label="Memory Used" value={`${h.memory_usage.percent_used}%`} />
                  </>
                ) : (
                  <p className="text-sm text-zinc-400">Memory info unavailable</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Dependencies</CardTitle>
                <Server className="h-4 w-4 text-zinc-400" />
              </CardHeader>
              <CardContent className="space-y-1">
                {h.dependency_status ? (
                  <>
                    <MetricRow
                      label="ML Model"
                      value={h.dependency_status.model === 'loaded' ? 'Loaded' : 'Missing'}
                    />
                    <MetricRow
                      label="Vectorizer"
                      value={h.dependency_status.vectorizer === 'loaded' ? 'Loaded' : 'Missing'}
                    />
                    <MetricRow
                      label="Configuration"
                      value={h.dependency_status.config === 'valid' ? 'Valid' : 'Invalid'}
                    />
                  </>
                ) : (
                  <p className="text-sm text-zinc-400">Dependency info unavailable</p>
                )}
                <MetricRow label="Registered Routes" value={String(h.registered_routes)} />
                <MetricRow label="Service Mode" value={h.test_mode ? 'Test' : 'Production'} />
              </CardContent>
            </Card>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Request Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            {metricsQuery.isLoading ? (
              <div className="space-y-2">
                <div className="h-4 w-full animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" />
                <div className="h-4 w-3/4 animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" />
                <div className="h-4 w-1/2 animate-pulse rounded bg-zinc-200 dark:bg-zinc-700" />
              </div>
            ) : metricsQuery.isError ? (
              <div className="flex items-center gap-2">
                <p className="text-sm text-red-600">Failed to load metrics</p>
                <RetryButton onRetry={() => metricsQuery.refetch()} />
              </div>
            ) : m ? (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
                <div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Total Requests</p>
                  <p className="text-xl font-bold">
                    {m.total_requests.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Successful</p>
                  <p className="text-xl font-bold text-emerald-600">
                    {m.successful_requests.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Failed</p>
                  <p className="text-xl font-bold text-red-600">
                    {m.failed_requests.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Active Requests</p>
                  <p className="text-xl font-bold">
                    {m.active_requests}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Avg Latency</p>
                  <p className="text-xl font-bold">
                    {m.average_latency_ms.toFixed(0)} ms
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">P95 Latency</p>
                  <p className="text-xl font-bold">
                    {m.p95_latency_ms.toFixed(0)} ms
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Max Latency</p>
                  <p className="text-xl font-bold">
                    {m.maximum_latency_ms.toFixed(0)} ms
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Validation Failures</p>
                  <p className="text-xl font-bold">
                    {m.validation_failures.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">OCR Requests</p>
                  <p className="text-xl font-bold">
                    {m.ocr_requests.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">Text Requests</p>
                  <p className="text-xl font-bold">
                    {m.text_requests.toLocaleString()}
                  </p>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Frontend Diagnostics</CardTitle>
            <Bug className="h-4 w-4 text-zinc-400" />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">API Failures</p>
                <p className="text-xl font-bold">{diagSummary.apiFailures}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">Render Errors</p>
                <p className="text-xl font-bold">{diagSummary.renderErrors}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">Network Errors</p>
                <p className="text-xl font-bold">{diagSummary.networkErrors}</p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">App Version</p>
                <p className="text-xl font-bold">{diagSummary.appVersion || '...'}</p>
              </div>
            </div>
            <p className="mt-3 text-xs text-zinc-400">
              Build: {getBuildTimestamp() || 'N/A'} &middot; Events: {diagSummary.totalEvents}
            </p>
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  );
}
