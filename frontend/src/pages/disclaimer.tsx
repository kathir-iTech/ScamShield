import { PageTransition } from '@/components/ui/page-transition';
import { Shield } from 'lucide-react';

export default function Disclaimer() {
  return (
    <PageTransition>
      <div className="mx-auto max-w-2xl space-y-12">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 dark:bg-emerald-900/20">
            <Shield className="h-6 w-6 text-emerald-500" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Disclaimer</h1>
        </div>

        <div className="space-y-8 text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">Not legal advice</h2>
            <p className="mt-2">Analysis results are for informational purposes only and do not constitute legal advice. Consult a qualified professional for legal matters.</p>
          </section>
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">No guarantee</h2>
            <p className="mt-2">Our AI detects common scam patterns but may not catch every threat. Use your judgment and verify through official channels.</p>
          </section>
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">Liability</h2>
            <p className="mt-2">ScamShield and its operators are not liable for losses or damages arising from use of the service.</p>
          </section>
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">Contact</h2>
            <p className="mt-2">Concerns? Contact <span className="text-emerald-600">support@scamshield.dev</span>.</p>
          </section>
        </div>
      </div>
    </PageTransition>
  );
}
