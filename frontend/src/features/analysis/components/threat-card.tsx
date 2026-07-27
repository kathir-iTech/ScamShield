import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/status-badge';
import { riskStatus, decisionStatus, priorityStatus } from '@/design/status';
import { Section } from '@/components/ui/section';
import { memo } from 'react';

interface ThreatCardProps {
  threats: string[];
  detectedIndicators: string[];
  decisionLevel: string;
  recommendedPriority: string;
  riskBreakdown: {
    credential_theft: number;
    financial_loss: number;
    identity_theft: number;
    malware: number;
    social_engineering: number;
  };
}

const riskBreakdownLabels: Record<string, string> = {
  credential_theft: 'Credential Theft',
  financial_loss: 'Financial Loss',
  identity_theft: 'Identity Theft',
  malware: 'Malware',
  social_engineering: 'Social Engineering',
};

export const ThreatCard = memo(function ThreatCard({
  threats,
  detectedIndicators,
  decisionLevel,
  recommendedPriority,
  riskBreakdown,
}: ThreatCardProps) {
  const hasAny =
    threats.length > 0 ||
    detectedIndicators.length > 0 ||
    Object.values(riskBreakdown).some((v) => v > 0);

  if (!hasAny) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Threat Intelligence</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {threats.length > 0 && (
          <Section title="Threats">
            <div className="flex flex-wrap gap-2">
              {threats.map((t) => (
                <StatusBadge key={t} status={riskStatus('HIGH')} />
              ))}
            </div>
          </Section>
        )}

        {detectedIndicators.length > 0 && (
          <Section title="Indicators">
            <div className="flex flex-wrap gap-1">
              {detectedIndicators.map((ind) => (
                <StatusBadge key={ind} status={{ variant: 'neutral', icon: riskStatus(ind).icon, label: ind }} size="sm" showIcon={false} />
              ))}
            </div>
          </Section>
        )}

        <div className="flex flex-wrap gap-6">
          <div className="space-y-1">
            <p className="text-xs text-zinc-500 dark:text-zinc-400">Decision</p>
            <StatusBadge status={decisionStatus(decisionLevel)} />
          </div>
          <div className="space-y-1">
            <p className="text-xs text-zinc-500 dark:text-zinc-400">Priority</p>
            <StatusBadge status={priorityStatus(recommendedPriority)} />
          </div>
        </div>

        {Object.values(riskBreakdown).some((v) => v > 0) && (
          <Section title="Risk Breakdown">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
              {Object.entries(riskBreakdown).map(([key, value]) => (
                <div
                  key={key}
                  className="rounded-lg bg-zinc-50 p-3 text-center dark:bg-zinc-800/50"
                >
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    {riskBreakdownLabels[key] || key}
                  </p>
                  <p className="mt-1 text-lg font-bold text-zinc-900 dark:text-zinc-50">
                    {value}
                  </p>
                </div>
              ))}
            </div>
          </Section>
        )}
      </CardContent>
    </Card>
  );
});
