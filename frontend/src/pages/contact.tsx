import { PageTransition } from '@/components/ui/page-transition';
import { Mail, Shield } from 'lucide-react';

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
          <div className="flex items-center gap-4 mb-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/10">
              <Mail className="h-5 w-5 text-accent" />
            </div>
            <div>
              <p className="text-sm font-medium text-text-primary">Email</p>
              <a href="mailto:support@scamshield.dev" className="text-sm text-accent hover:text-accent-hover transition-colors">
                support@scamshield.dev
              </a>
            </div>
          </div>
          <p className="text-sm text-text-secondary/80 leading-relaxed">
            Found a scam message? Send it to our team and we'll review it.
          </p>
        </div>
      </div>
    </PageTransition>
  );
}
