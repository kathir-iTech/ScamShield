import { InvestigationTimeline, CampaignView } from '@/features/timeline';
import type { TimelineEvent, CampaignGroup } from '@/features/timeline/types';
import { useState } from 'react';

interface LazyTimelineViewProps {
  events: TimelineEvent[];
  campaigns: CampaignGroup[];
}

export default function LazyTimelineView({ events, campaigns }: LazyTimelineViewProps) {
  const [showCampaigns, setShowCampaigns] = useState(false);

  return (
    <div className="h-full space-y-4 overflow-y-auto p-1">
      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowCampaigns(false)}
          className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
            !showCampaigns
              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
              : 'text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800'
          }`}
        >
          Timeline
        </button>
        <button
          onClick={() => setShowCampaigns(true)}
          className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
            showCampaigns
              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
              : 'text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800'
          }`}
        >
          Campaigns ({campaigns.length})
        </button>
      </div>
      {showCampaigns ? (
        <CampaignView campaigns={campaigns} onFilterByCampaign={() => setShowCampaigns(false)} onSelectEvent={() => {}} />
      ) : (
        <InvestigationTimeline events={events} />
      )}
    </div>
  );
}
