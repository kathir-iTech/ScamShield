import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { AnalysisResponse } from '@/types';
import { Shield, ChevronDown, ChevronRight, Globe, BookOpen, Merge } from 'lucide-react';

interface ThreatIntelViewerProps {
  result: AnalysisResponse;
}

function IntelCard({ icon, label, count, children }: {
  icon: React.ReactNode;
  label: string;
  count?: number;
  children?: React.ReactNode;
}) {
  const [open, setOpen] = useState(true);
  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-700">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-3 py-2"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-xs font-medium text-zinc-700 dark:text-zinc-300">{label}</span>
          {count !== undefined && (
            <Badge variant="outline" className="text-[9px]">{count}</Badge>
          )}
        </div>
        {open ? <ChevronDown className="h-3.5 w-3.5 text-zinc-400" /> : <ChevronRight className="h-3.5 w-3.5 text-zinc-400" />}
      </button>
      {open && children && (
        <div className="border-t border-zinc-200 px-3 py-2 dark:border-zinc-700">
          {children}
        </div>
      )}
    </div>
  );
}

export function ThreatIntelViewer({ result }: ThreatIntelViewerProps) {
  const [expanded, setExpanded] = useState(true);

  const connectorMatches = useMemo(() => {
    if (!result.connector_matches || !Array.isArray(result.connector_matches)) return [];
    return result.connector_matches;
  }, [result.connector_matches]);

  const knowledgeMatches = useMemo(() => {
    if (!result.knowledge_matches || !Array.isArray(result.knowledge_matches)) return [];
    return result.knowledge_matches;
  }, [result.knowledge_matches]);

  const fusionResult = useMemo(() => {
    if (!result.threat_intel_fusion) return null;
    return result.threat_intel_fusion;
  }, [result.threat_intel_fusion]);

  const hasIntelData = connectorMatches.length > 0 || knowledgeMatches.length > 0 || fusionResult;

  if (!hasIntelData) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-purple-500" />
            <CardTitle className="text-sm">Threat Intelligence</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <p className="py-3 text-center text-xs text-zinc-500">No threat intelligence data available for this analysis.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-center justify-between"
          aria-expanded={expanded}
        >
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-purple-500" />
            <CardTitle className="text-sm">Threat Intelligence</CardTitle>
            {(connectorMatches.length > 0 || knowledgeMatches.length > 0) && (
              <Badge variant="outline" className="text-[9px]">
                {connectorMatches.length + knowledgeMatches.length} matches
              </Badge>
            )}
          </div>
          {expanded ? <ChevronDown className="h-4 w-4 text-zinc-400" /> : <ChevronRight className="h-4 w-4 text-zinc-400" />}
        </button>
      </CardHeader>
      {expanded && (
        <CardContent className="space-y-2 pt-0">
          {connectorMatches.length > 0 && (
            <IntelCard icon={<Globe className="h-4 w-4 text-cyan-500" />} label="Connector Results" count={connectorMatches.length}>
              {connectorMatches.map((match: unknown, i: number) => {
                const m = match as Record<string, unknown>;
                return (
                  <div key={i} className="mb-1.5 rounded bg-zinc-50 px-2 py-1.5 text-xs dark:bg-zinc-800/50">
                    <p className="font-medium text-zinc-700 dark:text-zinc-300">
                      {String(m.source_name || m.source || 'Unknown')}
                    </p>
                    {m.description ? (
                      <p className="mt-0.5 text-zinc-500">{String(m.description)}</p>
                    ) : null}
                    {m.risk ? (
                      <Badge variant={String(m.risk) === 'high' ? 'destructive' : String(m.risk) === 'medium' ? 'warning' : 'info'} className="mt-1 text-[9px]">
                        {String(m.risk)}
                      </Badge>
                    ) : null}
                  </div>
                );
              })}
            </IntelCard>
          )}

          {knowledgeMatches.length > 0 && (
            <IntelCard icon={<BookOpen className="h-4 w-4 text-orange-500" />} label="Knowledge Base Matches" count={knowledgeMatches.length}>
              {knowledgeMatches.map((match: unknown, i: number) => {
                const m = match as Record<string, unknown>;
                return (
                  <div key={i} className="mb-1.5 rounded bg-zinc-50 px-2 py-1.5 text-xs dark:bg-zinc-800/50">
                    <p className="font-medium text-zinc-700 dark:text-zinc-300">
                      {String(m.label || m.name || 'Match')}
                    </p>
                    {m.confidence !== undefined && (
                      <div className="mt-1 flex items-center gap-1.5">
                        <div className="h-1.5 w-16 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
                          <div className="h-full rounded-full bg-emerald-500" style={{ width: `${(Number(m.confidence) * 100).toFixed(0)}%` }} />
                        </div>
                        <span className="text-[10px] text-zinc-400">{(Number(m.confidence) * 100).toFixed(0)}%</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </IntelCard>
          )}

          {fusionResult && (
            <IntelCard icon={<Merge className="h-4 w-4 text-purple-500" />} label="Fusion Summary">
              {Object.entries(fusionResult).map(([key, value]) => (
                <div key={key} className="flex items-start gap-2 py-1 text-xs">
                  <span className="shrink-0 font-medium text-zinc-500 capitalize">{key.replace(/_/g, ' ')}:</span>
                  <span className="text-zinc-700 dark:text-zinc-300">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            </IntelCard>
          )}
        </CardContent>
      )}
    </Card>
  );
}
