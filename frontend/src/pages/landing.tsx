import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TrustBadge } from '@/components/ui/trust-badge';
import { ArrowRight } from 'lucide-react';
import { PageTransition } from '@/components/ui/page-transition';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <PageTransition>
      <div className="space-y-24">
        <section className="pt-16">
          <div className="mx-auto max-w-2xl text-center">
            <Badge className="mb-6 animate-fade-in">AI-Powered Protection</Badge>
            <h1 className="text-5xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
              <span className="block animate-slide-up stagger-1">Know if it&apos;s a scam</span>
              <span className="mt-2 block text-emerald-500 animate-slide-up stagger-2">
                before you act.
              </span>
            </h1>
            <p className="mt-6 text-lg text-zinc-500 dark:text-zinc-400 animate-slide-up stagger-3">
              Paste a suspicious message or upload a screenshot. Get an instant answer — no account needed.
            </p>
            <div className="mt-8 flex items-center justify-center gap-4 animate-slide-up stagger-4">
              <Button size="xl" onClick={() => navigate('/analyze/text')}>
                Analyse a message <ArrowRight className="h-4 w-4" />
              </Button>
              <Button size="xl" variant="secondary" onClick={() => navigate('/analyze/image')}>
                Upload a screenshot
              </Button>
            </div>
            <div className="mt-8 animate-fade-in stagger-5">
              <TrustBadge />
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-medium text-emerald-500">How it works</p>
          <div className="mt-8 grid grid-cols-3 gap-8">
            {[
              { step: '01', title: 'Submit', desc: 'Paste or upload.' },
              { step: '02', title: 'Analyse', desc: 'AI checks the content.' },
              { step: '03', title: 'Review', desc: 'See your result.' },
            ].map((s) => (
              <div key={s.step}>
                <p className="text-2xl font-bold text-emerald-500">{s.step}</p>
                <h3 className="mt-2 font-semibold text-zinc-900 dark:text-zinc-100">{s.title}</h3>
                <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{s.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mx-auto max-w-xl text-center">
          <h2 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">Got a suspicious message?</h2>
          <p className="mt-3 text-zinc-500 dark:text-zinc-400">Analyse it now. Stay protected.</p>
          <div className="mt-6">
            <Button size="lg" onClick={() => navigate('/analyze/text')}>
              Analyse a message <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </section>
      </div>
    </PageTransition>
  );
}
