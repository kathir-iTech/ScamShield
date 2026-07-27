import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/status-badge';
import { decisionStatus } from '@/design/status';
import { Shield, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';

interface RecommendationCardProps {
  recommendedActions: string[];
  suggestedAction: string;
  recommendedAction: string;
  reviewRequired: boolean;
  manualReviewReason: string;
}

export function RecommendationCard({
  recommendedActions,
  suggestedAction,
  recommendedAction,
  reviewRequired,
  manualReviewReason,
}: RecommendationCardProps) {
  const suggestedStatus = useMemo(() => decisionStatus(suggestedAction), [suggestedAction]);
  const recommendedStatus = useMemo(() => decisionStatus(recommendedAction), [recommendedAction]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Recommended Actions
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {reviewRequired && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-3 rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-800 dark:bg-amber-900/20"
          >
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" />
            <div>
              <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
                Manual Review Required
              </p>
              <p className="text-xs text-amber-700 dark:text-amber-400">
                {manualReviewReason}
              </p>
            </div>
          </motion.div>
        )}

        <div className="flex flex-wrap gap-6">
          <div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">Suggested Action</p>
            <div className="mt-1">
              <StatusBadge status={suggestedStatus} />
            </div>
          </div>
          <div>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">Recommended Action</p>
            <div className="mt-1">
              <StatusBadge status={recommendedStatus} />
            </div>
          </div>
        </div>

        {recommendedActions.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">
              Immediate Actions
            </p>
            <ul className="space-y-1.5">
              {recommendedActions.map((action, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05, duration: 0.2 }}
                  className="flex items-start gap-2 text-sm text-zinc-700 dark:text-zinc-300"
                >
                  <Shield className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                  {action}
                </motion.li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
