import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Section } from '@/components/ui/section';

interface ReportSummaryCardProps {
  report: Record<string, unknown>;
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined) return 'N/A';
  if (typeof value === 'string') return value;
  if (typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) {
    if (value.length === 0) return 'None';
    return value.map((v) => (typeof v === 'object' ? JSON.stringify(v, null, 2) : String(v))).join('\n');
  }
  return JSON.stringify(value, null, 2);
}

const REPORT_SECTION_ORDER = [
  'executive_summary',
  'investigation_findings',
  'findings',
  'business_analysis',
  'technical_analysis',
  'risk_summary',
  'user_guidance',
  'guidance',
];

function isKnownSection(key: string): boolean {
  return REPORT_SECTION_ORDER.includes(key) || REPORT_SECTION_ORDER.some((s) => key.includes(s));
}

export function ReportSummaryCard({ report }: ReportSummaryCardProps) {
  if (!report || Object.keys(report).length === 0) return null;

  const entries = Object.entries(report).sort(([a], [b]) => {
    const ai = REPORT_SECTION_ORDER.indexOf(a);
    const bi = REPORT_SECTION_ORDER.indexOf(b);
    if (ai !== -1 && bi !== -1) return ai - bi;
    if (ai !== -1) return -1;
    if (bi !== -1) return 1;
    return a.localeCompare(b);
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Investigation Report</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {entries.map(([key, value]) => {
          const rendered = renderValue(value);
          if (!rendered || rendered === 'N/A' || rendered === 'None') return null;

          const label = key
            .replace(/_/g, ' ')
            .replace(/\b\w/g, (c) => c.toUpperCase());

          return (
            <Section key={key} title={label} as={isKnownSection(key) ? 'section' : 'div'}>
              {Array.isArray(value) && value.length > 0 && typeof value[0] === 'object' ? (
                <div className="space-y-3">
                  {(value as Record<string, unknown>[]).map((item, i) => (
                    <div
                      key={i}
                      className="rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm dark:border-zinc-700 dark:bg-zinc-800/50"
                    >
                      {Object.entries(item).map(([k, v]) => (
                        <div key={k} className="flex gap-2 py-0.5 text-sm">
                          <span className="shrink-0 text-xs font-medium text-zinc-400">
                            {k.replace(/_/g, ' ')}:
                          </span>
                          <span className="text-zinc-700 dark:text-zinc-300">
                            {renderValue(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ) : typeof value === 'string' && value.length > 0 ? (
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-700 dark:text-zinc-300">
                  {rendered}
                </p>
              ) : (
                <pre className="whitespace-pre-wrap font-mono text-xs text-zinc-600 dark:text-zinc-400">
                  {rendered.length > 500 ? rendered.slice(0, 500) + '...' : rendered}
                </pre>
              )}
            </Section>
          );
        })}
      </CardContent>
    </Card>
  );
}
