import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { InfoRow } from '@/components/ui/info-row';

interface TechnicalDetailsCardProps {
  mlConfidence: number;
  decisionScore: number;
  ruleScore: number;
  assessmentScore: number;
  evidenceCount: number;
  entityCount: number;
}

export function TechnicalDetailsCard({
  mlConfidence,
  decisionScore,
  ruleScore,
  assessmentScore,
  evidenceCount,
  entityCount,
}: TechnicalDetailsCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Technical Details</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="divide-y divide-zinc-100 dark:divide-zinc-800">
          <InfoRow label="ML Confidence" value={`${(mlConfidence * 100).toFixed(0)}%`} />
          <InfoRow label="Decision Score" value={String(decisionScore)} />
          <InfoRow label="Rule Score" value={ruleScore.toFixed(1)} />
          <InfoRow label="Assessment Score" value={`${assessmentScore}/100`} />
          <InfoRow label="Evidence Items" value={String(evidenceCount)} />
          <InfoRow label="Entities Found" value={String(entityCount)} />
        </div>
      </CardContent>
    </Card>
  );
}
