import { PageTransition } from '@/components/ui/page-transition';
import { Shield } from 'lucide-react';

export default function Terms() {
  const sections = [
    { title: 'Acceptance', content: 'By using Wary, you agree to these terms. If you do not agree, please do not use the service.' },
    { title: 'Service', content: 'Wary provides AI-powered scam detection. The service is free and provided "as is".' },
    { title: 'Your responsibilities', content: 'Do not submit illegal content or use the service to harass others. Analysis is for informational purposes only.' },
    { title: 'Limitations', content: 'Wary assists in scam detection. We do not guarantee all scams will be detected. Always use your judgment.' },
    { title: 'Changes', content: 'We may update these terms. Continued use after changes constitutes acceptance.' },
  ];

  return (
    <PageTransition>
      <div className="mx-auto max-w-2xl px-6 py-16 sm:py-20">
        <div className="text-center mb-14">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass">
            <Shield className="h-6 w-6 text-accent" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">Terms of Service</h1>
          <p className="mt-2 text-sm text-text-tertiary">Last updated: July 2026</p>
        </div>

        <div className="space-y-4">
          {sections.map((section, i) => (
            <div key={section.title} className="glass rounded-2xl p-6 animate-slide-up" style={{ animationDelay: `${200 + i * 80}ms` }}>
              <h2 className="text-sm font-semibold text-text-primary mb-2">{section.title}</h2>
              <p className="text-sm text-text-secondary/80 leading-relaxed">{section.content}</p>
            </div>
          ))}
        </div>
      </div>
    </PageTransition>
  );
}
