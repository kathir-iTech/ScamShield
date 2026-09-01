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

function toPct(v: number): number {
  if (v == null || isNaN(v)) return 0;
  // Backend/pipeline may send 0-100 or 0-1; normalize to 0-100 for display
  return v > 1 ? Math.min(100, v) : v * 100;
}

export function ConfidenceCard(props: Props) {
  const data: Breakdown = { ml: props.ml, rules: props.rules, entities: props.entities, explanation: props.explanation, overall: props.overall };

  return (
    <div className="space-y-4">
      <p className="text-xs text-text-tertiary">Confidence Breakdown</p>
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.key}>
            <div className="flex items-center justify-between text-sm">
              <span className="text-text-secondary">{item.label}</span>
              <span className="font-medium text-text-primary">{toPct(data[item.key as keyof Breakdown]).toFixed(0)}%</span>
            </div>
            <div className="mt-1 h-1.5 w-full rounded-full bg-glass-border">
              <div className="h-1.5 rounded-full bg-accent" style={{ width: `${toPct(data[item.key as keyof Breakdown])}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
