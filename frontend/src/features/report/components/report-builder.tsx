import { useState, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ReportSectionView } from '@/features/report/components/report-section-view';
import { generateReport } from '@/features/report/utils/generate-report';
import { exportJSON, exportMarkdown, exportText, copyToClipboard, printReport, shareReport } from '@/features/report/utils/export-report';
import {
  REPORT_TEMPLATE_LABELS,
  REPORT_TEMPLATE_DESCRIPTIONS,
  type ReportTemplate,
} from '@/features/report/types';
import type { AnalysisResponse } from '@/types';
import type { TimelineEvent } from '@/features/timeline/types';
import { FileText, Copy, Printer, Check, FileJson, FileType, Search, ChevronDown, ChevronRight, Share2 } from 'lucide-react';

interface ReportBuilderProps {
  result: AnalysisResponse;
  events: TimelineEvent[];
}

export function ReportBuilder({ result, events }: ReportBuilderProps) {
  const [template, setTemplate] = useState<ReportTemplate>('technical');
  const [copied, setCopied] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set());

  const report = useMemo(
    () => generateReport(result, template, events),
    [result, template, events]
  );

  const handleCopy = useCallback(async () => {
    const text = exportText(report);
    await copyToClipboard(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [report]);

  const handleDownloadJSON = useCallback(() => {
    const blob = exportJSON(report);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scamshield-report-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [report]);

  const handleDownloadMarkdown = useCallback(() => {
    const md = exportMarkdown(report);
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scamshield-report-${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }, [report]);

  const handlePrint = useCallback(() => {
    printReport(report, () => exportText(report));
  }, [report]);

  const handleShare = useCallback(() => {
    shareReport(report);
  }, [report]);

  const toggleSection = useCallback((type: string) => {
    setCollapsedSections((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }, []);

  const filteredSections = useMemo(() => {
    if (!searchQuery) return report.sections;
    const q = searchQuery.toLowerCase();
    return report.sections.map((section) => ({
      ...section,
      content: section.content.filter((line) => line.toLowerCase().includes(q)),
    })).filter((section) => section.content.length > 0);
  }, [report.sections, searchQuery]);

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
      <div className="space-y-4 lg:col-span-1 lg:sticky lg:top-6 lg:self-start">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Report Template</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 pt-0">
            {(Object.keys(REPORT_TEMPLATE_LABELS) as ReportTemplate[]).map((t) => (
              <button
                key={t}
                onClick={() => setTemplate(t)}
                className={`w-full rounded-lg border p-3 text-left transition-all ${
                  template === t
                    ? 'border-emerald-500 bg-emerald-50 dark:border-emerald-600 dark:bg-emerald-900/20'
                    : 'border-zinc-200 hover:border-zinc-300 dark:border-zinc-700 dark:hover:border-zinc-600'
                }`}
              >
                <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                  {REPORT_TEMPLATE_LABELS[t]}
                </p>
                <p className="mt-0.5 text-[11px] text-zinc-500 dark:text-zinc-400">
                  {REPORT_TEMPLATE_DESCRIPTIONS[t]}
                </p>
              </button>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Sections</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 pt-0">
            {report.sections.map((s, i) => (
              <button
                key={s.type}
                onClick={() => toggleSection(s.type)}
                className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs hover:bg-zinc-50 dark:hover:bg-zinc-800"
              >
                {collapsedSections.has(s.type) ? (
                  <ChevronRight className="h-3 w-3 shrink-0 text-zinc-400" />
                ) : (
                  <ChevronDown className="h-3 w-3 shrink-0 text-zinc-400" />
                )}
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-zinc-100 text-[10px] text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
                  {i + 1}
                </span>
                <span className="flex-1 text-left text-zinc-700 dark:text-zinc-300">{s.title}</span>
                <Badge variant="outline" className="text-[9px]">{s.content.length}</Badge>
              </button>
            ))}
          </CardContent>
        </Card>

        <div className="flex flex-col gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zinc-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search in report..."
              className="w-full rounded-lg border border-zinc-200 bg-white py-1.5 pl-8 pr-3 text-xs placeholder-zinc-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
            />
          </div>
          <Button variant="outline" size="sm" onClick={handleCopy} className="justify-start">
            {copied ? <Check className="mr-2 h-4 w-4 text-emerald-500" /> : <Copy className="mr-2 h-4 w-4" />}
            {copied ? 'Copied!' : 'Copy Report'}
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownloadJSON} className="justify-start">
            <FileJson className="mr-2 h-4 w-4" />
            Download JSON
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownloadMarkdown} className="justify-start">
            <FileType className="mr-2 h-4 w-4" />
            Download Markdown
          </Button>
          <Button variant="outline" size="sm" onClick={handlePrint} className="justify-start">
            <Printer className="mr-2 h-4 w-4" />
            Print / PDF
          </Button>
          <Button variant="outline" size="sm" onClick={handleShare} className="justify-start">
            <Share2 className="mr-2 h-4 w-4" />
            Share Report
          </Button>
        </div>
      </div>

      <div className="space-y-4 lg:col-span-3">
        <Card>
          <CardHeader className="border-b border-zinc-200 pb-3 dark:border-zinc-700">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">{report.title}</CardTitle>
                <p className="mt-0.5 text-xs text-zinc-500">
                  Generated {new Date(report.generatedAt).toLocaleString()}
                  &middot; {filteredSections.length} sections
                  &middot; {report.metadata.prediction.toUpperCase()}
                  {searchQuery && <span className="ml-2 text-emerald-500">Filtered by search</span>}
                </p>
              </div>
              <FileText className="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
            </div>
          </CardHeader>
          <CardContent className="space-y-4 pt-4">
            {filteredSections.length === 0 ? (
              <p className="py-8 text-center text-sm text-zinc-500">
                {searchQuery ? 'No sections match your search.' : 'No report content available.'}
              </p>
            ) : (
              filteredSections.map((section, i) => (
                <div key={section.type}>
                  <button
                    onClick={() => toggleSection(section.type)}
                    className="flex w-full items-center gap-2 py-1 text-xs text-zinc-400 hover:text-zinc-600"
                  >
                    {collapsedSections.has(section.type) ? (
                      <ChevronRight className="h-3 w-3" />
                    ) : (
                      <ChevronDown className="h-3 w-3" />
                    )}
                    {collapsedSections.has(section.type) ? 'Show section' : 'Hide section'}
                  </button>
                  {!collapsedSections.has(section.type) && (
                    <ReportSectionView section={section} index={i} />
                  )}
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
