import type { ReportSection } from '@/features/report/types';

interface ReportSectionViewProps {
  section: ReportSection;
  index: number;
  compact?: boolean;
}

export function ReportSectionView({ section, index, compact }: ReportSectionViewProps) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-700 dark:bg-zinc-900">
      <div className="mb-3 flex items-center gap-3">
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-100 text-xs font-bold text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300">
          {index + 1}
        </span>
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{section.title}</h3>
        {section.severity && (
          <span className={`ml-auto rounded-full px-2 py-0.5 text-[10px] font-medium ${
            section.severity === 'critical' || section.severity === 'high'
              ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
              : section.severity === 'medium'
                ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
          }`}>
            {section.severity}
          </span>
        )}
      </div>

      <div className="space-y-1.5">
        {section.content.map((line, i) => (
          <p key={i} className={`text-sm leading-relaxed ${
            line.startsWith('  •') || line.startsWith('    •')
              ? 'pl-4 text-zinc-600 dark:text-zinc-400'
              : line.startsWith('  ')
                ? 'pl-2 text-zinc-600 dark:text-zinc-400'
                : 'font-medium text-zinc-800 dark:text-zinc-200'
          }`}>
            {line}
          </p>
        ))}
      </div>

      {section.confidence !== undefined && !compact && (
        <div className="mt-3 flex items-center gap-2">
          <span className="text-xs text-zinc-500">Confidence</span>
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-700">
            <div className="h-full rounded-full bg-emerald-500" style={{ width: `${(section.confidence * 100).toFixed(0)}%` }} />
          </div>
          <span className="text-xs text-zinc-400">{(section.confidence * 100).toFixed(0)}%</span>
        </div>
      )}
    </div>
  );
}
