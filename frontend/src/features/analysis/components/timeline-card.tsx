import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { CheckCircle, Circle } from 'lucide-react';
import { motion } from 'framer-motion';

interface TimelineStep {
  label: string;
  completed: boolean;
}

const defaultSteps: TimelineStep[] = [
  { label: 'Message Analysed', completed: true },
  { label: 'Entities Extracted', completed: true },
  { label: 'Evidence Correlated', completed: true },
  { label: 'Assessment Generated', completed: true },
  { label: 'Report Produced', completed: true },
];

interface TimelineCardProps {
  steps?: TimelineStep[];
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const itemAnim = {
  hidden: { opacity: 0, x: -12 },
  show: { opacity: 1, x: 0, transition: { duration: 0.25 } },
};

export function TimelineCard({ steps = defaultSteps }: TimelineCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Investigation Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <div className="absolute left-4 top-0 h-full w-0.5 bg-zinc-200 dark:bg-zinc-700" />
          <motion.div
            className="space-y-6"
            variants={container}
            initial="hidden"
            animate="show"
          >
            {steps.map((step, i) => (
              <motion.div
                key={i}
                variants={itemAnim}
                className="relative flex items-start gap-4"
              >
                <div className="relative z-10 flex shrink-0">
                  {step.completed ? (
                    <CheckCircle className="h-8 w-8 text-emerald-500" />
                  ) : (
                    <Circle className="h-8 w-8 text-zinc-300 dark:text-zinc-600" />
                  )}
                </div>
                <div className="flex flex-col justify-center pt-1">
                  <p
                    className={`text-sm font-medium ${
                      step.completed
                        ? 'text-zinc-900 dark:text-zinc-50'
                        : 'text-zinc-400 dark:text-zinc-500'
                    }`}
                  >
                    {step.label}
                  </p>
                  {step.completed && (
                    <p className="text-xs text-zinc-400">Completed</p>
                  )}
                </div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </CardContent>
    </Card>
  );
}
