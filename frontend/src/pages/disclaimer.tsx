import { PageTransition } from '@/components/ui/page-transition';
import { Shield } from 'lucide-react';

export default function Disclaimer() {
  const sections = [
    { title: 'Not legal advice', content: 'Analysis results are for informational purposes only and do not constitute legal advice. Consult a qualified professional for legal matters.' },
    { title: 'No guarantee', content: 'Our AI detects common scam patterns but may not catch every threat. Use your judgment and verify through official channels.' },
    { title: 'Liability', content: 'ScamShield and its operators are not liable for losses or damages arising from use of the service.' },
    { title: 'Contact', content: 'Concerns? Contact support@scamshield.dev.' },
  ];

  return (
    <PageTransition>
      <div className="mx-auto max-w-2xl px-6 py-16 sm:py-20">
        <div className="text-center mb-14">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass">
            <Shield className="h-6 w-6 text-accent" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">Disclaimer</h1>
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
