interface PageSkeletonProps {
  variant?: string;
}

const variantLabels: Record<string, string> = {
  dashboard: 'Loading dashboard',
  analysis: 'Loading text analysis page',
  report: 'Loading report page',
  system: 'Loading system status page',
};

export function PageSkeleton({ variant = 'dashboard' }: PageSkeletonProps) {
  return (
    <div
      className="mx-auto max-w-2xl space-y-6 pt-12"
      role="status"
      aria-busy="true"
      aria-label={variantLabels[variant] || 'Loading page'}
    >
      <div className="h-8 w-48 animate-shimmer rounded-xl" />
      <div className="h-4 w-72 animate-shimmer rounded-xl" />
      <div className="h-48 animate-shimmer rounded-2xl" />
    </div>
  );
}
