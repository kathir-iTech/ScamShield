import { PageTransition } from '@/components/ui/page-transition';
import { Shield } from 'lucide-react';

export default function Contact() {
  return (
    <PageTransition>
      <div className="mx-auto max-w-xl px-6 py-16 sm:py-20">
        <div className="text-center mb-10">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass">
            <Shield className="h-6 w-6 text-accent" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">Contact</h1>
          <p className="mt-2 text-text-secondary/70">Get in touch with the team.</p>
        </div>

        <div className="glass rounded-2xl p-7 animate-slide-up">
          <p className="text-sm text-text-secondary/80 leading-relaxed">
            Contact us via the form above.
          </p>
          <p className="text-sm text-text-secondary/80 leading-relaxed">
            Found a scam message? Send it to our team and we'll review it.
          </p>
        </div>
      </div>
    </PageTransition>
  );
}
