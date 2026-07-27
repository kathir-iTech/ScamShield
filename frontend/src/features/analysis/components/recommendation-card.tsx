import { Card, CardContent } from '@/components/ui/card';

interface Props {
  recommendedActions: string[];
  suggestedAction: string;
  recommendedAction: string;
  reviewRequired: boolean;
  manualReviewReason: string;
}

export function RecommendationCard({ recommendedActions, suggestedAction, recommendedAction, reviewRequired, manualReviewReason }: Props) {
  return (
    <Card>
      <CardContent className="space-y-4 py-6">
        <p className="text-xs text-zinc-400">What to do</p>
        <p className="text-base font-semibold text-zinc-900 dark:text-zinc-50">{suggestedAction || recommendedAction}</p>
        {reviewRequired && manualReviewReason && (
          <p className="text-sm text-amber-600 dark:text-amber-400">{manualReviewReason}</p>
        )}
        {recommendedActions.length > 0 && (
          <ul className="space-y-1.5">
            {recommendedActions.map((a, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-zinc-600 dark:text-zinc-400">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                {a}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
