import { useNavigate } from 'react-router-dom';
import { PageTransition } from '@/components/ui/page-transition';
import { Button } from '@/components/ui/button';
import { Search, ArrowRight } from 'lucide-react';

export default function Investigation() {
  const navigate = useNavigate();

  return (
    <PageTransition>
      <div className="mx-auto flex max-w-xl flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-zinc-100 dark:bg-zinc-800">
          <Search className="h-6 w-6 text-zinc-400" />
        </div>
        <h1 className="text-xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Deep dive</h1>
        <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
          Analyse a message first, then investigate the details here.
        </p>
        <div className="mt-6 flex gap-3">
          <Button onClick={() => navigate('/analyze/text')}>
            Analyse a message <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </PageTransition>
  );
}
