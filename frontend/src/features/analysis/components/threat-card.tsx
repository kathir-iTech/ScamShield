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
    <div className="space-y-4">
      <p className="text-xs text-text-tertiary">Threat Analysis</p>
      {threats.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {threats.map((t) => (
            <span key={t} className="rounded-full bg-danger/10 border border-danger/20 px-3 py-1 text-xs font-medium text-danger">
              {t}
            </span>
          ))}
        </div>
      )}
      {detectedIndicators.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {detectedIndicators.map((ind) => (
            <span key={ind} className="rounded-full bg-glass border border-glass-border px-2.5 py-0.5 text-xs text-text-secondary">
              {ind}
            </span>
          ))}
        </div>
      )}
      <div className="flex gap-6">
        <div>
          <p className="text-xs text-text-tertiary">Decision</p>
          <p className="text-sm font-medium text-text-primary">{decisionLevel}</p>
        </div>
        <div>
          <p className="text-xs text-text-tertiary">Priority</p>
          <p className="text-sm font-medium text-text-primary">{recommendedPriority}</p>
        </div>
      </div>
      {Object.values(riskBreakdown).some((v) => v > 0) && (
        <div className="grid grid-cols-5 gap-2">
          {Object.entries(riskBreakdown).map(([key, value]) => (
            <div key={key} className="rounded-xl bg-glass border border-glass-border p-3 text-center">
              <p className="text-xs text-text-tertiary">{riskLabels[key] || key}</p>
              <p className="mt-1 text-base font-bold text-text-primary">{value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
