import { useState, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { X, ChevronLeft, ChevronRight, Lightbulb } from 'lucide-react';

interface WalkthroughStep {
  title: string;
  content: string;
  tab: 'graph' | 'timeline' | 'campaigns' | 'report';
}

const WALKTHROUGH_STEPS: WalkthroughStep[] = [
  {
    title: 'Evidence Graph',
    content: 'This interactive graph visualizes relationships between evidence, entities, threats, connectors, and knowledge matches. Each node is colored by type and sized by confidence. Drag to pan, scroll to zoom, and click nodes to inspect details.',
    tab: 'graph',
  },
  {
    title: 'Investigation Timeline',
    content: 'The timeline shows the chronological sequence of investigation events — from initial analysis through evidence discovery, threat identification, connector lookups, and final assessment. Use zoom and filters to focus on specific event types.',
    tab: 'timeline',
  },
  {
    title: 'Campaign Analysis',
    content: 'Campaigns group related events by scam category. View shared entities, repeated indicators, and campaign-level confidence. Click "Filter timeline" to see events belonging to a specific campaign.',
    tab: 'campaigns',
  },
  {
    title: 'Report Builder',
    content: 'Generate formatted reports in Technical, Executive, Law Enforcement, or Customer Friendly templates. Preview sections, copy to clipboard, or export as JSON, Markdown, or print as PDF.',
    tab: 'report',
  },
  {
    title: 'Fusion & Intelligence',
    content: 'The system fuses results from multiple sources — ML analysis, rule engine, knowledge base, and external connectors — to produce a unified verdict with confidence scoring, conflict resolution, and evidence ranking.',
    tab: 'graph',
  },
  {
    title: 'Final Assessment',
    content: 'Every investigation produces a final assessment with risk level, recommended actions, confidence breakdown, and priority. The investigation report captures all findings in a structured format.',
    tab: 'report',
  },
];

interface DemoWalkthroughProps {
  onClose: () => void;
  onNavigateTab: (tab: string) => void;
}

export function DemoWalkthrough({ onClose, onNavigateTab }: DemoWalkthroughProps) {
  const [step, setStep] = useState(0);
  const [visible, setVisible] = useState(true);

  const current = WALKTHROUGH_STEPS[step];
  const isLast = step === WALKTHROUGH_STEPS.length - 1;
  const isFirst = step === 0;

  const goNext = useCallback(() => {
    if (!isLast) {
      const next = WALKTHROUGH_STEPS[step + 1];
      onNavigateTab(next.tab);
      setStep(step + 1);
    } else {
      handleClose();
    }
  }, [step, isLast, onNavigateTab]);

  const goPrev = useCallback(() => {
    if (!isFirst) {
      const prev = WALKTHROUGH_STEPS[step - 1];
      onNavigateTab(prev.tab);
      setStep(step - 1);
    }
  }, [step, isFirst, onNavigateTab]);

  const handleClose = useCallback(() => {
    setVisible(false);
    setTimeout(onClose, 300);
  }, [onClose]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="relative w-full max-w-lg animate-in fade-in zoom-in">
        <button
          onClick={handleClose}
          className="absolute right-3 top-3 text-zinc-400 hover:text-zinc-600"
          aria-label="Close walkthrough"
        >
          <X className="h-5 w-5" />
        </button>

        <CardContent className="p-6">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900">
              <Lightbulb className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <p className="text-xs text-zinc-500">
                Step {step + 1} of {WALKTHROUGH_STEPS.length}
              </p>
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
                {current.title}
              </h3>
            </div>
          </div>

          <p className="text-sm leading-relaxed text-zinc-600 dark:text-zinc-300">
            {current.content}
          </p>

          {/* Progress dots */}
          <div className="mt-6 flex items-center justify-center gap-1.5">
            {WALKTHROUGH_STEPS.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 rounded-full transition-all ${
                  i === step ? 'w-6 bg-emerald-500' : 'w-1.5 bg-zinc-300 dark:bg-zinc-600'
                }`}
              />
            ))}
          </div>

          <div className="mt-6 flex items-center justify-between">
            <Button variant="ghost" size="sm" onClick={goPrev} disabled={isFirst}>
              <ChevronLeft className="mr-1 h-4 w-4" />
              Previous
            </Button>
            <Button size="sm" onClick={goNext}>
              {isLast ? 'Finish' : 'Next'}
              {!isLast && <ChevronRight className="ml-1 h-4 w-4" />}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
