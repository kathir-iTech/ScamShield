import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SAMPLE_CASES } from '@/features/demo/sample-cases';
import type { DemoCase } from '@/features/demo/types';
import type { AnalysisResponse } from '@/types';
import { Play, Sparkles } from 'lucide-react';

interface DemoPanelProps {
  onLoadCase: (result: AnalysisResponse, title: string) => void;
}

const DIFFICULTY_COLORS: Record<string, string> = {
  beginner: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  intermediate: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  advanced: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
};

export function DemoPanel({ onLoadCase }: DemoPanelProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const handleLoad = async (demoCase: DemoCase) => {
    setLoadingId(demoCase.id);
    setSelectedId(demoCase.id);
    await new Promise((r) => setTimeout(r, 800));
    onLoadCase(demoCase.result, demoCase.title);
    setLoadingId(null);
  };

  return (
    <div className="mx-auto max-w-4xl">
      <Card className="mb-8 border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-900/20">
        <CardContent className="flex items-start gap-4 p-6">
          <Sparkles className="mt-1 h-6 w-6 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <div>
            <h2 className="text-lg font-semibold text-emerald-900 dark:text-emerald-100">
              Demo Mode
            </h2>
            <p className="mt-1 text-sm text-emerald-700 dark:text-emerald-300">
              Explore ScamShield's investigation capabilities with pre-built sample cases.
              No backend required — everything runs in your browser.
              Each case includes realistic evidence, entities, threats, and connector data.
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {SAMPLE_CASES.map((demoCase) => {
          const isSelected = selectedId === demoCase.id;
          const isLoading = loadingId === demoCase.id;

          return (
            <Card
              key={demoCase.id}
              className={`cursor-pointer transition-all hover:shadow-md ${
                isSelected ? 'ring-2 ring-emerald-500' : ''
              }`}
              onClick={() => setSelectedId(demoCase.id)}
              role="button"
              tabIndex={0}
              aria-label={`Load ${demoCase.title}`}
              onKeyDown={(e) => { if (e.key === 'Enter') setSelectedId(demoCase.id); }}
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <span className="text-2xl">{demoCase.icon}</span>
                  <Badge className={DIFFICULTY_COLORS[demoCase.difficulty]}>
                    {demoCase.difficulty}
                  </Badge>
                </div>
                <CardTitle className="mt-2 text-sm">{demoCase.title}</CardTitle>
                <Badge variant="outline" className="text-[10px]">
                  {demoCase.category}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-3 pt-0">
                <p className="text-xs leading-relaxed text-zinc-500 dark:text-zinc-400">
                  {demoCase.description}
                </p>
                <Button
                  size="sm"
                  className="w-full"
                  variant={isSelected ? 'default' : 'outline'}
                  disabled={isLoading}
                  onClick={(e) => { e.stopPropagation(); handleLoad(demoCase); }}
                >
                  {isLoading ? (
                    <>Loading…</>
                  ) : (
                    <><Play className="mr-1.5 h-3.5 w-3.5" /> Load Case</>
                  )}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
