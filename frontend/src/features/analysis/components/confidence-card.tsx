import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { memo } from 'react';

interface ConfidenceCardProps {
  ml: number;
  rules: number;
  entities: number;
  explanation: number;
  overall: number;
}

const barColor = (val: number) => {
  if (val >= 80) return 'bg-emerald-500';
  if (val >= 50) return 'bg-amber-500';
  return 'bg-red-500';
};

const ConfidenceBar = memo(function ConfidenceBar({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span className="text-zinc-600 dark:text-zinc-400">{label}</span>
        <span className="font-medium text-zinc-900 dark:text-zinc-50">{value}</span>
      </div>
      <div
        className="h-2 w-full rounded-full bg-zinc-200 dark:bg-zinc-700"
        role="progressbar"
        aria-valuenow={Math.min(value, 100)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label}: ${value}%`}
      >
        <div
          className={`h-2 rounded-full transition-all ${barColor(value)}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  );
});

export const ConfidenceCard = memo(function ConfidenceCard({
  ml,
  rules,
  entities,
  explanation,
  overall,
}: ConfidenceCardProps) {
  const items = [
    { label: 'Machine Learning', value: ml },
    { label: 'Rule Engine', value: rules },
    { label: 'Entity Analysis', value: entities },
    { label: 'Explanation Engine', value: explanation },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Confidence Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-xs text-zinc-500 dark:text-zinc-400">Overall Confidence</p>
          <p className="text-lg font-bold text-zinc-900 dark:text-zinc-50">{overall}%</p>
        </div>
        <div className="space-y-3">
          {items.map((item) => (
            <ConfidenceBar key={item.label} label={item.label} value={item.value} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
});
