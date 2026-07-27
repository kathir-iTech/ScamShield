import { useNavigate } from 'react-router-dom';
import { PageTransition } from '@/components/ui/page-transition';
import { Search, ArrowRight } from 'lucide-react';

export default function Investigation() {
  const navigate = useNavigate();

  return (
    <PageTransition>
      <div className="mx-auto max-w-xl px-6 py-20 sm:py-28 text-center">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass">
          <Search className="h-6 w-6 text-accent" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">Deep dive</h1>
        <p className="mt-2 text-text-secondary/70">
          Analyse a message first, then investigate the details here.
        </p>
        <div className="mt-8 flex justify-center">
          <button
            onClick={() => navigate('/analyze/text')}
            className="glass-button group relative inline-flex h-12 items-center gap-2 rounded-xl px-6 text-sm font-semibold text-white"
          >
            Analyse a message <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
          </button>
        </div>
      </div>
    </PageTransition>
  );
}
