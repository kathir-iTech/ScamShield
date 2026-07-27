import { Card, CardContent } from '@/components/ui/card';

interface Breakdown {
  ml: number;
  rules: number;
  entities: number;
  explanation: number;
  overall: number;
}

interface Props {
  ml: number;
  rules: number;
  entities: number;
  explanation: number;
  overall: number;
}

const items = [
  { key: 'ml', label: 'ML Model' },
  { key: 'rules', label: 'Rules' },
  { key: 'entities', label: 'Entities' },
  { key: 'explanation', label: 'Explanation' },
  { key: 'overall', label: 'Overall' },
];

export function ConfidenceCard(props: Props) {
  const data: Breakdown = { ml: props.ml, rules: props.rules, entities: props.entities, explanation: props.explanation, overall: props.overall };

  return (
    <Card>
      <CardContent className="space-y-4 py-6">
        <p className="text-xs text-zinc-400">Confidence Breakdown</p>
        <div className="space-y-3">
          {items.map((item) => (
            <div key={item.key}>
              <div className="flex items-center justify-between text-sm">
                <span className="text-zinc-600 dark:text-zinc-400">{item.label}</span>
                <span className="font-medium text-zinc-900 dark:text-zinc-100">{(data[item.key as keyof Breakdown] * 100).toFixed(0)}%</span>
              </div>
              <div className="mt-1 h-1.5 w-full rounded-full bg-zinc-100 dark:bg-zinc-800">
                <div className="h-1.5 rounded-full bg-emerald-500" style={{ width: `${data[item.key as keyof Breakdown] * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
