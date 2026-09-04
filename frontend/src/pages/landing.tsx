import { useNavigate } from 'react-router-dom';
import { PageTransition } from '@/components/ui/page-transition';
import { ArrowRight, Sparkles, Shield, Lock, Zap } from 'lucide-react';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <PageTransition>
      <div className="mx-auto max-w-4xl px-6 py-20 sm:py-28">
        <section className="text-center">
          <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border border-glass-border bg-glass px-4 py-1.5 text-sm text-text-secondary animate-fade-in">
            <Sparkles className="h-3.5 w-3.5 text-accent" />
            AI-Powered Protection
          </div>

          <h1 className="text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
            <span className="block text-text-primary animate-slide-up stagger-1">
              Know if it's a scam
            </span>
            <span className="mt-3 block text-gradient-accent animate-slide-up stagger-2">
              before you act.
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-lg text-lg text-text-secondary/70 animate-slide-up stagger-3 leading-relaxed">
            Paste a suspicious message or upload a screenshot.
            <br />
            Get an instant answer.
            <br />
            No account needed.
          </p>

          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row animate-slide-up stagger-4">
            <button
              onClick={() => navigate('/analyze/text')}
              className="glass-button group relative inline-flex h-14 items-center gap-2.5 rounded-2xl px-8 text-base font-semibold text-white overflow-hidden"
            >
              Analyse a message
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
            </button>
            <button
              onClick={() => navigate('/analyze/image')}
              className="glass group relative inline-flex h-14 items-center gap-2.5 rounded-2xl px-8 text-base font-medium text-text-secondary hover:text-text-primary overflow-hidden"
            >
              Upload a screenshot
            </button>
          </div>

          <div className="mt-6 animate-slide-up stagger-4">
            <button
              onClick={() => navigate('/grandma-mode')}
              className="text-sm text-text-tertiary underline decoration-glass-border underline-offset-4 hover:text-accent"
            >
              Prefer to listen? Try Grandma Mode — big button, spoken results.
            </button>
          </div>

          <div className="mt-8 flex items-center justify-center gap-6 text-xs text-text-tertiary animate-fade-in stagger-5">
            <span className="flex items-center gap-1.5">
              <Lock className="h-3 w-3" /> Private
            </span>
            <span className="flex items-center gap-1.5">
              <Zap className="h-3 w-3" /> Instant
            </span>
            <span className="flex items-center gap-1.5">
              <Shield className="h-3 w-3" /> Free
            </span>
          </div>
        </section>

        <section className="mx-auto mt-28 max-w-2xl">
          <div className="grid grid-cols-3 gap-6">
            {[
              { step: '01', title: 'Submit', desc: 'Paste or upload.' },
              { step: '02', title: 'Analyse', desc: 'AI checks the content.' },
              { step: '03', title: 'Review', desc: 'See your result.' },
            ].map((s, i) => (
              <div
                key={s.step}
                className="glass rounded-2xl p-6 text-center animate-glass-enter"
                style={{ animationDelay: `${400 + i * 100}ms` }}
              >
                <p className="text-3xl font-bold text-accent/60">{s.step}</p>
                <h3 className="mt-3 text-sm font-semibold text-text-primary">{s.title}</h3>
                <p className="mt-1 text-xs text-text-tertiary">{s.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mx-auto mt-28 max-w-lg text-center">
          <div className="glass rounded-3xl p-10 animate-glass-enter stagger-8">
            <h2 className="text-2xl font-bold tracking-tight text-text-primary">
              Got a suspicious message?
            </h2>
            <p className="mt-3 text-text-secondary/70">
              Analyse it now. Stay protected.
            </p>
            <button
              onClick={() => navigate('/analyze/text')}
              className="glass-button group relative mt-6 inline-flex h-12 items-center gap-2 rounded-xl px-6 text-sm font-semibold text-white overflow-hidden"
            >
              Analyse a message
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
            </button>
          </div>
        </section>
      </div>
    </PageTransition>
  );
}
