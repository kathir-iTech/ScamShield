import { useHealth, useReady } from '@/hooks/use-scamshield';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { RetryButton } from '@/components/retry-button';
import { PageTransition } from '@/components/ui/page-transition';
import { Shield, CheckCircle, XCircle, Activity, List } from 'lucide-react';

function StatCard({
  title,
  value,
  icon: Icon,
  isLoading,
  error,
  onRetry,
}: {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  isLoading: boolean;
  error: boolean;
  onRetry?: () => void;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-zinc-400" />
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-8 w-20" />
        ) : error ? (
          <div className="flex items-center gap-2">
            <span className="text-sm text-red-600">Failed to load</span>
            {onRetry && <RetryButton onRetry={onRetry} />}
          </div>
        ) : (
          <div className="text-2xl font-bold">{value}</div>
        )}
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const healthQuery = useHealth();
  const readyQuery = useReady();

  const isLoading = healthQuery.isLoading || readyQuery.isLoading;
  const hasError = healthQuery.isError || readyQuery.isError;

  return (
    <PageTransition>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            Dashboard
          </h1>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            Overview of scam categories and detection capabilities
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <StatCard
            title="Service Status"
            value={healthQuery.data?.status === 'healthy' ? 'Healthy' : 'Degraded'}
            icon={healthQuery.data?.status === 'healthy' ? CheckCircle : XCircle}
            isLoading={isLoading}
            error={hasError}
            onRetry={() => healthQuery.refetch()}
          />
          <StatCard
            title="Analysis Engine"
            value={readyQuery.data?.status || 'Unknown'}
            icon={Shield}
            isLoading={isLoading}
            error={hasError}
            onRetry={() => readyQuery.refetch()}
          />
          <StatCard
            title="Service Uptime"
            value={
              healthQuery.data
                ? `${Math.floor(healthQuery.data.uptime_seconds / 60)}m`
                : 'N/A'
            }
            icon={Activity}
            isLoading={healthQuery.isLoading}
            error={healthQuery.isError}
            onRetry={() => healthQuery.refetch()}
          />
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <List className="h-4 w-4" />
                Supported Scam Categories
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {[
                  'Bank KYC Scam',
                  'Lottery Scam',
                  'Job Scam',
                  'UPI Scam',
                  'Investment Scam',
                  'Courier Scam',
                  'Government Scheme',
                  'Electricity Bill',
                  'Customs Scam',
                  'Loan Scam',
                  'Fake Customer Care',
                  'QR Code Scam',
                  'Crypto Scam',
                ].map((cat) => (
                  <Badge key={cat} variant="outline">
                    {cat}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <List className="h-4 w-4" />
                Supported Entity Types
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {[
                  'URL',
                  'Shortened URL',
                  'Email',
                  'Phone',
                  'UPI ID',
                  'OTP Code',
                  'IP Address',
                  'Bank Account',
                  'IFSC Code',
                  'Social Handle',
                  'Tracking ID',
                ].map((ent) => (
                  <Badge key={ent} variant="outline">
                    {ent}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <List className="h-4 w-4" />
                Assessment Bands
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {[
                  'Suitable for normal communication',
                  'Further assessment required',
                  'Suitable for security investigation',
                  'Suitable for immediate action',
                ].map((band) => (
                  <Badge key={band} variant="outline">
                    {band}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>How It Works</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-inside list-disc space-y-1 text-sm text-zinc-600 dark:text-zinc-400">
              <li>AI analysis of messages for scam patterns</li>
              <li>Rule-based detection of common fraud indicators</li>
              <li>Identifies suspicious phone numbers, URLs, UPI IDs, and more</li>
              <li>Comprehensive risk scoring with supporting evidence</li>
              <li>Text extraction from uploaded screenshots</li>
              <li>Secure processing of all submitted content</li>
              <li>Reliable analysis even when some checks are unavailable</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  );
}
