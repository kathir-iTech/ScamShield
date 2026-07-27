import { PageTransition } from '@/components/ui/page-transition';
import { Shield } from 'lucide-react';

export default function Terms() {
  return (
    <PageTransition>
      <div className="mx-auto max-w-2xl space-y-12">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 dark:bg-emerald-900/20">
            <Shield className="h-6 w-6 text-emerald-500" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Terms of Service</h1>
          <p className="mt-1 text-sm text-zinc-500">Last updated: July 2026</p>
        </div>

        <div className="space-y-8 text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">Acceptance</h2>
            <p className="mt-2">By using ScamShield, you agree to these terms. If you do not agree, please do not use the service.</p>
          </section>
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">Service</h2>
            <p className="mt-2">ScamShield provides AI-powered scam detection. The service is free and provided &ldquo;as is&rdquo;.</p>
          </section>
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">Your responsibilities</h2>
            <p className="mt-2">Do not submit illegal content or use the service to harass others. Analysis is for informational purposes only.</p>
          </section>
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">Limitations</h2>
            <p className="mt-2">ScamShield assists in scam detection. We do not guarantee all scams will be detected. Always use your judgment.</p>
          </section>
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">Changes</h2>
            <p className="mt-2">We may update these terms. Continued use after changes constitutes acceptance.</p>
          </section>
        </div>
      </div>
    </PageTransition>
  );
}
