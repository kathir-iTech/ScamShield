import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Shield, ArrowRight } from 'lucide-react';

export function EmptyAnalysisState() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-zinc-100 dark:bg-zinc-800">
        <Shield className="h-6 w-6 text-zinc-400" />
      </div>
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">Nothing to review yet</h2>
      <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">Analyse a suspicious message or screenshot to see your result.</p>
      <div className="mt-6 flex gap-3">
        <Button onClick={() => navigate('/analyze/text')}>
          Analyse a message <ArrowRight className="h-4 w-4" />
        </Button>
        <Button variant="secondary" onClick={() => navigate('/analyze/image')}>
          Upload a screenshot
        </Button>
      </div>
    </div>
  );
}
