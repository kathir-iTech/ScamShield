interface Props {
  recommendedActions: string[];
  suggestedAction: string;
  recommendedAction: string;
  reviewRequired: boolean;
  manualReviewReason: string;
}

export function RecommendationCard({ recommendedActions, suggestedAction, recommendedAction, reviewRequired, manualReviewReason }: Props) {
  return (
    <div className="space-y-4">
      <p className="text-xs text-text-tertiary">What to do</p>
      <p className="text-base font-semibold text-text-primary">{suggestedAction || recommendedAction}</p>
      {reviewRequired && manualReviewReason && (
        <p className="text-sm text-warning">{manualReviewReason}</p>
      )}
      {recommendedActions.length > 0 && (
        <ul className="space-y-1.5">
          {recommendedActions.map((a, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-text-secondary/80">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
              {a}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
