import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent, CardHeader } from '@/components/ui/card';

export function GraphSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-4" aria-busy="true" aria-label="Loading graph view">
      <div className="space-y-4 lg:col-span-1">
        <Card><CardContent className="p-4"><Skeleton className="h-4 w-24 mb-3" /><Skeleton className="h-4 w-full mb-2" /><Skeleton className="h-4 w-3/4" /></CardContent></Card>
        <Card><CardContent className="p-4"><Skeleton className="h-4 w-20 mb-3" /><Skeleton className="h-6 w-full mb-2" /><Skeleton className="h-6 w-full" /></CardContent></Card>
      </div>
      <div className="flex flex-col gap-4 lg:col-span-2">
        <Card><CardContent className="p-3"><Skeleton className="h-9 w-full" /></CardContent></Card>
        <Skeleton className="h-[500px] w-full rounded-xl lg:h-[600px]" />
      </div>
      <div className="lg:col-span-1">
        <Card className="h-full"><CardContent className="flex items-center justify-center p-6"><Skeleton className="h-4 w-40" /></CardContent></Card>
      </div>
    </div>
  );
}

export function TimelineSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3" aria-busy="true" aria-label="Loading timeline view">
      <div className="flex flex-col gap-4 lg:col-span-2">
        <Card><CardContent className="p-3"><Skeleton className="h-9 w-full" /></CardContent></Card>
        <Card>
          <CardHeader><Skeleton className="h-5 w-32" /></CardHeader>
          <CardContent className="space-y-3 pt-0">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="flex items-start gap-4">
                <Skeleton className="h-3 w-3 rounded-full mt-1.5" />
                <Skeleton className="h-3 w-16 mt-1.5" />
                <div className="flex-1 space-y-1.5">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
      <div className="lg:col-span-1">
        <Card className="h-full"><CardContent className="flex items-center justify-center p-6"><Skeleton className="h-4 w-36" /></CardContent></Card>
      </div>
    </div>
  );
}

export function CampaignsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3" aria-busy="true" aria-label="Loading campaigns view">
      {[...Array(3)].map((_, i) => (
        <Card key={i}>
          <CardHeader className="border-b border-zinc-100 pb-3 dark:border-zinc-800">
            <Skeleton className="h-5 w-3/4 mb-2" />
            <Skeleton className="h-4 w-20" />
          </CardHeader>
          <CardContent className="space-y-3 pt-3">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-2 w-full" />
            <div className="flex gap-1"><Skeleton className="h-5 w-16" /><Skeleton className="h-5 w-20" /></div>
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-8 w-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function ReportSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-4" aria-busy="true" aria-label="Loading report builder">
      <div className="space-y-4 lg:col-span-1">
        <Card><CardContent className="p-4 space-y-2"><Skeleton className="h-4 w-28 mb-2" /><Skeleton className="h-20 w-full" /><Skeleton className="h-20 w-full" /><Skeleton className="h-20 w-full" /><Skeleton className="h-20 w-full" /></CardContent></Card>
        <Card><CardContent className="p-4 space-y-2"><Skeleton className="h-4 w-20 mb-2" /><Skeleton className="h-6 w-full" /><Skeleton className="h-6 w-full" /><Skeleton className="h-6 w-full" /></CardContent></Card>
      </div>
      <div className="lg:col-span-3">
        <Card>
          <CardHeader className="border-b border-zinc-200 pb-3 dark:border-zinc-700">
            <Skeleton className="h-6 w-48 mb-1" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent className="space-y-4 pt-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="rounded-lg border border-zinc-200 p-5 dark:border-zinc-700">
                <div className="flex items-center gap-3 mb-3"><Skeleton className="h-6 w-6 rounded-full" /><Skeleton className="h-5 w-40" /></div>
                <div className="space-y-1.5"><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-3/4" /><Skeleton className="h-4 w-1/2" /></div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
