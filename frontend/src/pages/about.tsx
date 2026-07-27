import { PageTransition } from '@/components/ui/page-transition';
import { Shield, Sparkles, Lock, Zap } from 'lucide-react';

export default function About() {
  const features = [
    { icon: Sparkles, title: 'AI-powered', desc: 'Machine learning and rules detect phishing, fraud, UPI scams, and more.' },
    { icon: Lock, title: 'Private by design', desc: 'Messages and images are processed in real time. We do not store or share anything.' },
    { icon: Zap, title: 'Free for everyone', desc: 'No accounts, no payments, no limits. Scam detection should be accessible to all.' },
    { icon: Shield, title: 'Fast results', desc: 'Get a clear risk assessment in seconds. Actionable and easy to understand.' },
  ];

  return (
    <PageTransition>
      <div className="mx-auto max-w-2xl px-6 py-16 sm:py-20">
        <div className="text-center mb-14">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass">
            <Shield className="h-6 w-6 text-accent" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">About ScamShield</h1>
          <p className="mt-3 text-text-secondary/70 leading-relaxed">
            ScamShield helps you identify scam messages before you act.
            <br />
            Free, private, no account needed.
          </p>
        </div>

        <div className="grid gap-4">
          {features.map((item, i) => (
            <div
              key={item.title}
              className="glass rounded-2xl p-6 animate-slide-up flex items-start gap-4"
              style={{ animationDelay: `${200 + i * 80}ms` }}
            >
              <div className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-accent/10">
                <item.icon className="h-5 w-5 text-accent" />
              </div>
              <div>
                <h2 className="text-sm font-semibold text-text-primary">{item.title}</h2>
                <p className="mt-1 text-sm text-text-secondary/80 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </PageTransition>
  );
}
