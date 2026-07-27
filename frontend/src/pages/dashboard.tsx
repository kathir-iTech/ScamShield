import { useHealth, useReady } from '@/hooks/use-scamshield';
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
    <div className="glass rounded-2xl p-6">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-text-secondary">{title}</p>
        <Icon className="h-4 w-4 text-text-tertiary" />
      </div>
      {isLoading ? (
        <Skeleton className="h-8 w-20" />
      ) : error ? (
        <div className="flex items-center gap-2">
          <span className="text-sm text-danger">Failed to load</span>
          {onRetry && <RetryButton onRetry={onRetry} />}
        </div>
      ) : (
        <div className="text-2xl font-bold text-text-primary">{value}</div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const healthQuery = useHealth();
  const readyQuery = useReady();

  const isLoading = healthQuery.isLoading || readyQuery.isLoading;
  const hasError = healthQuery.isError || readyQuery.isError;

  const categories = [
    'Bank KYC Scam', 'Lottery Scam', 'Job Scam', 'UPI Scam',
    'Investment Scam', 'Courier Scam', 'Government Scheme',
    'Electricity Bill', 'Customs Scam', 'Loan Scam',
    'Fake Customer Care', 'QR Code Scam', 'Crypto Scam',
  ];

  const entities = [
    'URL', 'Shortened URL', 'Email', 'Phone', 'UPI ID',
    'OTP Code', 'IP Address', 'Bank Account', 'IFSC Code',
    'Social Handle', 'Tracking ID',
  ];

  const bands = [
    'Suitable for normal communication',
    'Further assessment required',
    'Suitable for security investigation',
    'Suitable for immediate action',
  ];

  return (
    <PageTransition>
      <div className="mx-auto max-w-4xl px-6 py-10 sm:py-14 space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary">Dashboard</h1>
          <p className="mt-2 text-text-secondary/70">Overview of scam categories and detection capabilities</p>
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
            value={healthQuery.data ? `${Math.floor(healthQuery.data.uptime_seconds / 60)}m` : 'N/A'}
            icon={Activity}
            isLoading={healthQuery.isLoading}
            error={healthQuery.isError}
            onRetry={() => healthQuery.refetch()}
          />
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[
            { title: 'Supported Scam Categories', items: categories },
            { title: 'Supported Entity Types', items: entities },
            { title: 'Assessment Bands', items: bands },
          ].map((section, i) => (
            <div key={section.title} className="glass rounded-2xl p-6 animate-slide-up" style={{ animationDelay: `${200 + i * 80}ms` }}>
              <div className="flex items-center gap-2 mb-4">
                <List className="h-4 w-4 text-accent" />
                <h2 className="text-sm font-semibold text-text-primary">{section.title}</h2>
              </div>
              <div className="flex flex-wrap gap-2">
                {section.items.map((item) => (
                  <span key={item} className="rounded-full border border-glass-border bg-glass px-3 py-1 text-xs text-text-secondary">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="glass rounded-2xl p-7 animate-slide-up stagger-4">
          <h2 className="text-sm font-semibold text-text-primary mb-4">How It Works</h2>
          <ul className="space-y-2">
            {[
              'AI analysis of messages for scam patterns',
              'Rule-based detection of common fraud indicators',
              'Identifies suspicious phone numbers, URLs, UPI IDs, and more',
              'Comprehensive risk scoring with supporting evidence',
              'Text extraction from uploaded screenshots',
              'Secure processing of all submitted content',
              'Reliable analysis even when some checks are unavailable',
            ].map((item, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-text-secondary/80">
                <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-accent/50" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </PageTransition>
  );
}
