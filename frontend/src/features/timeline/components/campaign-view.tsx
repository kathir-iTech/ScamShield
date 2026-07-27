import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TIMELINE_EVENT_COLORS, type CampaignGroup } from '@/features/timeline/types';
import { Users, Repeat, Target, ChevronRight } from 'lucide-react';

interface CampaignViewProps {
  campaigns: CampaignGroup[];
  onFilterByCampaign: (name: string) => void;
  onSelectEvent: (id: string) => void;
}

export function CampaignView({ campaigns, onFilterByCampaign, onSelectEvent }: CampaignViewProps) {
  if (campaigns.length === 0) {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">No campaign data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {campaigns.map((campaign) => {
        const riskColor =
          campaign.riskLevel === 'critical' ? '#dc2626'
            : campaign.riskLevel === 'high' ? '#ea580c'
              : campaign.riskLevel === 'medium' ? '#d97706'
                : campaign.riskLevel === 'low' ? '#059669'
                  : '#6b7280';

        return (
          <Card key={campaign.id} className="overflow-hidden">
            <CardHeader className="border-b border-zinc-100 pb-3 dark:border-zinc-800">
              <div className="flex items-start justify-between">
                <div className="min-w-0 flex-1">
                  <CardTitle className="truncate text-sm">{campaign.name}</CardTitle>
                  <div className="mt-1 flex items-center gap-2">
                    <Badge
                      variant={
                        campaign.riskLevel === 'critical' || campaign.riskLevel === 'high'
                          ? 'destructive'
                          : campaign.riskLevel === 'medium'
                            ? 'warning'
                            : campaign.riskLevel === 'low'
                              ? 'default'
                              : 'outline'
                      }
                      className="text-[10px]"
                    >
                      {campaign.riskLevel.toUpperCase()}
                    </Badge>
                    <span className="text-[10px] text-zinc-400">{campaign.eventCount} events</span>
                  </div>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-3 pt-3">
              {/* Confidence bar */}
              <div>
                <p className="mb-1 text-[10px] font-medium text-zinc-500 dark:text-zinc-400">Campaign Confidence</p>
                <div className="flex items-center gap-2">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
                    <div
                      className="h-full rounded-full"
                      style={{ width: `${(campaign.confidence * 100).toFixed(0)}%`, backgroundColor: riskColor }}
                    />
                  </div>
                  <span className="text-[11px] text-zinc-500">
                    {(campaign.confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Shared entities */}
              {campaign.sharedEntities.length > 0 && (
                <div>
                  <p className="mb-1 flex items-center gap-1 text-[10px] font-medium text-zinc-500 dark:text-zinc-400">
                    <Users className="h-3 w-3" />
                    Shared Entities ({campaign.sharedEntities.length})
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {campaign.sharedEntities.slice(0, 5).map((entity) => (
                      <span key={entity} className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                        {entity}
                      </span>
                    ))}
                    {campaign.sharedEntities.length > 5 && (
                      <span className="text-[10px] text-zinc-400">+{campaign.sharedEntities.length - 5}</span>
                    )}
                  </div>
                </div>
              )}

              {/* Repeated indicators */}
              {campaign.repeatedIndicators.length > 0 && (
                <div>
                  <p className="mb-1 flex items-center gap-1 text-[10px] font-medium text-zinc-500 dark:text-zinc-400">
                    <Repeat className="h-3 w-3" />
                    Repeated Indicators ({campaign.repeatedIndicators.length})
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {campaign.repeatedIndicators.slice(0, 4).map((indicator) => (
                      <span key={indicator} className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                        {indicator.length > 30 ? indicator.slice(0, 30) + '…' : indicator}
                      </span>
                    ))}
                    {campaign.repeatedIndicators.length > 4 && (
                      <span className="text-[10px] text-zinc-400">+{campaign.repeatedIndicators.length - 4}</span>
                    )}
                  </div>
                </div>
              )}

              {/* Recent events */}
              <div>
                <p className="mb-1 flex items-center gap-1 text-[10px] font-medium text-zinc-500 dark:text-zinc-400">
                  <Target className="h-3 w-3" />
                  Events
                </p>
                <div className="space-y-1">
                  {campaign.events.slice(0, 4).map((ev) => (
                    <button
                      key={ev.id}
                      onClick={() => onSelectEvent(ev.id)}
                      className="flex w-full items-center gap-2 rounded px-2 py-1 text-left text-[11px] hover:bg-zinc-100 dark:hover:bg-zinc-800"
                    >
                      <span
                        className="h-1.5 w-1.5 shrink-0 rounded-full"
                        style={{ backgroundColor: TIMELINE_EVENT_COLORS[ev.type] }}
                      />
                      <span className="flex-1 truncate text-zinc-600 dark:text-zinc-400">{ev.label}</span>
                    </button>
                  ))}
                  {campaign.events.length > 4 && (
                    <p className="text-center text-[10px] text-zinc-400">+{campaign.events.length - 4} more</p>
                  )}
                </div>
              </div>

              <Button
                variant="ghost"
                size="sm"
                className="w-full text-xs"
                onClick={() => onFilterByCampaign(campaign.name)}
              >
                <ChevronRight className="mr-1 h-3 w-3" />
                Filter timeline to this campaign
              </Button>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
