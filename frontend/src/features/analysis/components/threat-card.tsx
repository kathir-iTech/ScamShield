import { Card, CardContent } from '@/components/ui/card';

const riskLabels: Record<string, string> = {
  credential_theft: 'Credential Theft',
  financial_loss: 'Financial Loss',
  identity_theft: 'Identity Theft',
  malware: 'Malware',
  social_engineering: 'Social Engineering',
};

interface Props {
  threats: string[];
  detectedIndicators: string[];
  decisionLevel: string;
  recommendedPriority: string;
  riskBreakdown: Record<string, number>;
}

export function ThreatCard({ threats, detectedIndicators, decisionLevel, recommendedPriority, riskBreakdown }: Props) {
  const hasAny = threats.length > 0 || detectedIndicators.length > 0 || Object.values(riskBreakdown).some((v) => v > 0);
  if (!hasAny) return null;

  return (
    <Card>
      <CardContent className="space-y-5 py-6">
        <p className="text-xs text-zinc-400">Threat Analysis</p>
        {threats.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {threats.map((t) => <span key={t} className="rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700 dark:bg-red-900/20 dark:text-red-400">{t}</span>)}
          </div>
        )}
        {detectedIndicators.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {detectedIndicators.map((ind) => <span key={ind} className="rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">{ind}</span>)}
          </div>
        )}
        <div className="flex gap-6">
          <div>
            <p className="text-xs text-zinc-400">Decision</p>
            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{decisionLevel}</p>
          </div>
          <div>
            <p className="text-xs text-zinc-400">Priority</p>
            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{recommendedPriority}</p>
          </div>
        </div>
        {Object.values(riskBreakdown).some((v) => v > 0) && (
          <div className="grid grid-cols-5 gap-2">
            {Object.entries(riskBreakdown).map(([key, value]) => (
              <div key={key} className="rounded-xl bg-zinc-50 p-3 text-center dark:bg-zinc-800/50">
                <p className="text-xs text-zinc-400">{riskLabels[key] || key}</p>
                <p className="mt-1 text-base font-bold text-zinc-900 dark:text-zinc-50">{value}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
