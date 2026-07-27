import { PageTransition } from '@/components/ui/page-transition';
import { Shield } from 'lucide-react';

export default function About() {
  return (
    <PageTransition>
      <div className="mx-auto max-w-2xl space-y-12">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 dark:bg-emerald-900/20">
            <Shield className="h-6 w-6 text-emerald-500" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">About ScamShield</h1>
          <p className="mt-3 text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed">
            ScamShield helps you identify scam messages before you act. Free, private, no account needed.
          </p>
        </div>

        <div className="space-y-8">
          {[
            { title: 'AI-powered', desc: 'Machine learning and rules detect phishing, fraud, UPI scams, and more.' },
            { title: 'Private by design', desc: 'Messages and images are processed in real time. We do not store or share anything.' },
            { title: 'Free for everyone', desc: 'No accounts, no payments, no limits. Scam detection should be accessible to all.' },
            { title: 'Fast results', desc: 'Get a clear risk assessment in seconds. Actionable and easy to understand.' },
          ].map((item) => (
            <div key={item.title}>
              <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{item.title}</h2>
              <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </PageTransition>
  );
}
