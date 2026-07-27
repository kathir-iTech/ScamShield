import { PageTransition } from '@/components/ui/page-transition';
import { Shield } from 'lucide-react';

export default function Privacy() {
  return (
    <PageTransition>
      <div className="mx-auto max-w-2xl space-y-12">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 dark:bg-emerald-900/20">
            <Shield className="h-6 w-6 text-emerald-500" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Privacy Policy</h1>
          <p className="mt-1 text-sm text-zinc-500">Last updated: July 2026</p>
        </div>

        <div className="space-y-8 text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">What we collect</h2>
            <p className="mt-2">ScamShield processes text or images you submit for analysis. Content is analysed in real time and is not stored, logged, or retained after analysis.</p>
          </section>
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">How we use it</h2>
            <p className="mt-2">Submitted content is used only for scam detection. We do not use your data for training, marketing, or any other purpose.</p>
          </section>
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">Storage</h2>
            <p className="mt-2">We do not store submitted messages or images. Results are held temporarily in memory and discarded immediately.</p>
          </section>
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">Third parties</h2>
            <p className="mt-2">We do not share data with third parties. No analytics, tracking, or advertising services are used.</p>
          </section>
          <section>
            <h2 className="font-semibold text-zinc-900 dark:text-zinc-100">Contact</h2>
            <p className="mt-2">Questions? Contact <span className="text-emerald-600">support@scamshield.dev</span>.</p>
          </section>
        </div>
      </div>
    </PageTransition>
  );
}
