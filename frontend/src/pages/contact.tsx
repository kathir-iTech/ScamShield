import { PageTransition } from '@/components/ui/page-transition';
import { Card, CardContent } from '@/components/ui/card';
import { Mail, Shield } from 'lucide-react';

export default function Contact() {
  return (
    <PageTransition>
      <div className="mx-auto max-w-xl space-y-8">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 dark:bg-emerald-900/20">
            <Shield className="h-6 w-6 text-emerald-500" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">Contact</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">Get in touch with the team.</p>
        </div>

        <Card>
          <CardContent className="space-y-4 py-6">
            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-emerald-500" />
              <div>
                <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">Email</p>
                <a href="mailto:support@scamshield.dev" className="text-sm text-emerald-600 hover:underline">support@scamshield.dev</a>
              </div>
            </div>
            <p className="text-sm text-zinc-500 dark:text-zinc-400 leading-relaxed">
              Found a scam message? Send it to our team and we&apos;ll review it.
            </p>
          </CardContent>
        </Card>
      </div>
    </PageTransition>
  );
}
