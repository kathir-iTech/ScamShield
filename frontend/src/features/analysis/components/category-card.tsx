import { Card, CardContent } from '@/components/ui/card';

interface Props {
  scamCategory: string;
  summary: string;
  reasons: string[];
  businessReason: string;
  technicalReason: string;
}

export function CategoryCard({ scamCategory, summary, reasons, businessReason, technicalReason }: Props) {
  return (
    <Card>
      <CardContent className="space-y-4 py-6">
        <p className="text-xs text-zinc-400">Category</p>
        <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{scamCategory}</p>
        <p className="text-sm text-zinc-600 dark:text-zinc-400">{summary}</p>
        {reasons.length > 0 && (
          <div>
            <p className="text-xs text-zinc-400">Why</p>
            <ul className="mt-1 list-inside list-disc space-y-0.5 text-sm text-zinc-600 dark:text-zinc-400">
              {reasons.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        )}
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-xl bg-zinc-50 p-4 dark:bg-zinc-800/50">
            <p className="text-xs text-zinc-400">Business</p>
            <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">{businessReason}</p>
          </div>
          <div className="rounded-xl bg-zinc-50 p-4 dark:bg-zinc-800/50">
            <p className="text-xs text-zinc-400">Technical</p>
            <p className="mt-1 text-sm text-zinc-700 dark:text-zinc-300">{technicalReason}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
