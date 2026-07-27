import { PageTransition } from '@/components/ui/page-transition';
import { Shield } from 'lucide-react';

export default function Privacy() {
  const sections = [
    { title: 'What we collect', content: 'ScamShield processes text or images you submit for analysis. Content is analysed in real time and is not stored, logged, or retained after analysis.' },
    { title: 'How we use it', content: 'Submitted content is used only for scam detection. We do not use your data for training, marketing, or any other purpose.' },
    { title: 'Storage', content: 'We do not store submitted messages or images. Results are held temporarily in memory and discarded immediately.' },
    { title: 'Third parties', content: 'We do not share data with third parties. No analytics, tracking, or advertising services are used.' },
    { title: 'Contact', content: 'Questions? Contact support@scamshield.dev.' },
  ];

  return (
    <PageTransition>
      <div className="mx-auto max-w-2xl px-6 py-16 sm:py-20">
        <div className="text-center mb-14">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass">
            <Shield className="h-6 w-6 text-accent" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">Privacy Policy</h1>
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
