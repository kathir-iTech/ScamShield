import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowRight, Shield, Brain, Eye, Gauge, GitBranch, BookOpen, GitFork } from 'lucide-react';

const FEATURES = [
  { icon: Brain, title: 'ML Classification', desc: 'LogisticRegression with TF-IDF vectorization trained on SMS spam data for accurate scam detection.' },
  { icon: Eye, title: 'Rule Engine', desc: '18 heuristic indicator patterns covering OTP fraud, UPI scams, KYC phishing, urgency demands, and more.' },
  { icon: Eye, title: 'OCR Analysis', desc: 'Tesseract-based image-to-text extraction for analyzing scam screenshots and images.' },
  { icon: Gauge, title: 'Confidence Engine', desc: 'Multi-factor confidence scoring combining ML, rules, entities, and explanation coherence.' },
  { icon: GitBranch, title: 'Reasoning Engine', desc: 'Transparent decision traces with evidence ranking, contradiction detection, and investigation reports.' },
  { icon: Shield, title: 'Connector Framework', desc: 'Pluggable connector system with Google Safe Browsing integration and multi-source threat fusion.' },
];

const METRICS = [
  { label: 'Accuracy', value: '83.3%' },
  { label: 'F1 Score', value: '90.1%' },
  { label: 'Benchmark Samples', value: '162' },
  { label: 'Tests Passing', value: '244' },
  { label: 'Scam Categories', value: '13' },
  { label: 'Entity Types', value: '11' },
];

const TECH_STACK = [
  { category: 'Backend', items: 'Python, FastAPI, scikit-learn, Tesseract OCR, joblib, Pydantic' },
  { category: 'Frontend', items: 'React 19, TypeScript 6, Vite, Tailwind CSS v4, Framer Motion, TanStack Query' },
  { category: 'Deployment', items: 'Docker, Docker Compose, Nginx, GitHub Actions' },
  { category: 'ML/AI', items: 'Logistic Regression, TF-IDF, Confidence Scoring, Evidence Ranking, Ablation Analysis' },
];

const FAQ = [
  { q: 'What is ScamShield?', a: 'An open-source AI engine that detects scam and phishing SMS messages using machine learning and heuristic rules.' },
  { q: 'Does it require internet?', a: 'No. The core engine runs fully offline with no external API dependencies. Optional connectors add cloud threat intel.' },
  { q: 'What scam types are supported?', a: '13 categories including bank KYC, lottery, job, UPI, investment, courier, government scheme, and crypto scams.' },
  { q: 'Can I train my own model?', a: 'Yes. The training pipeline is included. Run `python train.py` with your own dataset.' },
  { q: 'Is there a hosted demo?', a: 'Yes. Visit the deployed demo to test the system live with sample cases.' },
];

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-zinc-200 bg-gradient-to-b from-emerald-50 to-white px-4 pb-20 pt-16 dark:border-zinc-800 dark:from-zinc-900 dark:to-zinc-950">
        <div className="mx-auto max-w-5xl text-center">
          <Badge variant="outline" className="mb-4">v1.0.0 — Open Source Release</Badge>
          <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-5xl lg:text-6xl">
            AI-Powered{' '}
            <span className="bg-gradient-to-r from-emerald-600 to-emerald-400 bg-clip-text text-transparent">
              Scam Detection
            </span>
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-zinc-600 dark:text-zinc-400">
            An open-source engine that detects phishing, fraud, and scam SMS messages using machine learning,
            heuristic rules, and multi-source threat intelligence — all offline capable.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Button size="lg" onClick={() => navigate('/analyze/text')}>
              Try Live Demo <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate('/system')}>
              <Shield className="mr-2 h-4 w-4" /> System Status
            </Button>
            <Button size="lg" variant="ghost" onClick={() => window.open('https://github.com/scamshield/scamshield', '_blank')}>
              <GitFork className="mr-2 h-4 w-4" /> GitHub
            </Button>
          </div>
        </div>
      </section>

      {/* Metrics */}
      <section className="border-b border-zinc-200 px-4 py-12 dark:border-zinc-800">
        <div className="mx-auto max-w-5xl">
          <div className="grid grid-cols-3 gap-4 sm:grid-cols-6">
            {METRICS.map((m) => (
              <div key={m.label} className="text-center">
                <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{m.value}</p>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">{m.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="px-4 py-16" id="features">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-2 text-center text-sm font-medium text-emerald-600 dark:text-emerald-400">Features</h2>
          <h3 className="mb-8 text-center text-3xl font-bold text-zinc-900 dark:text-zinc-50">What ScamShield Does</h3>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <Card key={f.title} className="transition-shadow hover:shadow-md">
                <CardHeader>
                  <f.icon className="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
                  <CardTitle className="mt-2 text-sm">{f.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">{f.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture */}
      <section className="bg-zinc-50 px-4 py-16 dark:bg-zinc-900" id="architecture">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-2 text-center text-sm font-medium text-emerald-600 dark:text-emerald-400">Architecture</h2>
          <h3 className="mb-6 text-center text-3xl font-bold text-zinc-900 dark:text-zinc-50">System Design</h3>
          <Card>
            <CardContent className="p-6">
              <pre className="overflow-x-auto text-xs leading-loose text-zinc-600 dark:text-zinc-400">
{`┌─────────────┐    ┌────────────────────────────────────────────────┐
│   Client    │    │              Nginx Reverse Proxy               │
│ (Browser/   │───▶│  /api/* → backend:8000  │  /* → static files   │
│   curl)     │    └────────────────────────────────────────────────┘
└─────────────┘                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (:8000)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │  Health  │  │ Analyze  │  │  System  │  │   Connectors     │   │
│  │  Router  │  │  Router  │  │  Router  │  │   Framework      │   │
│  └──────────┘  └────┬─────┘  └──────────┘  └──────────────────┘   │
│                     │                                               │
│  ┌──────────────────▼──────────────────────────────────────────┐   │
│  │              Orchestrator Pipeline                          │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌──────┐ │   │
│  │  │   ML   │  │ Rules  │  │  OCR   │  │Reason  │  │Fusion│ │   │
│  │  │ Service│  │ Service│  │ Service│  │Engine  │  │Engine│ │   │
│  │  └────────┘  └────────┘  └────────┘  └────────┘  └──────┘ │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘`}
              </pre>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="px-4 py-16" id="stack">
        <div className="mx-auto max-w-5xl">
          <h2 className="mb-2 text-center text-sm font-medium text-emerald-600 dark:text-emerald-400">Technology</h2>
          <h3 className="mb-8 text-center text-3xl font-bold text-zinc-900 dark:text-zinc-50">Built With</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            {TECH_STACK.map((s) => (
              <Card key={s.category}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">{s.category}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">{s.items}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="bg-zinc-50 px-4 py-16 dark:bg-zinc-900" id="faq">
        <div className="mx-auto max-w-3xl">
          <h2 className="mb-2 text-center text-sm font-medium text-emerald-600 dark:text-emerald-400">FAQ</h2>
          <h3 className="mb-8 text-center text-3xl font-bold text-zinc-900 dark:text-zinc-50">Frequently Asked Questions</h3>
          <div className="space-y-4">
            {FAQ.map((item) => (
              <Card key={item.q}>
                <CardContent className="p-4">
                  <p className="font-medium text-zinc-900 dark:text-zinc-100">{item.q}</p>
                  <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{item.a}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-4 py-16">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">Ready to Detect Scams?</h2>
          <p className="mt-3 text-zinc-500 dark:text-zinc-400">Try the live demo or explore the source code on GitHub.</p>
          <div className="mt-6 flex flex-wrap justify-center gap-4">
            <Button size="lg" onClick={() => navigate('/analyze/text')}>
              Try Live Demo <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button size="lg" variant="outline" onClick={() => navigate('/investigation')}>
              <BookOpen className="mr-2 h-4 w-4" /> View Demo Cases
            </Button>
            <Button size="lg" variant="ghost" onClick={() => window.open('https://github.com/scamshield/scamshield', '_blank')}>
              <GitFork className="mr-2 h-4 w-4" /> Star on GitHub
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-200 px-4 py-8 dark:border-zinc-800">
        <div className="mx-auto flex max-w-5xl flex-col items-center justify-between gap-4 text-center sm:flex-row">
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            ScamShield v1.0.0 — Open source (MIT)
          </p>
          <div className="flex items-center gap-4 text-sm text-zinc-500 dark:text-zinc-400">
            <a href="https://github.com/scamshield/scamshield" className="hover:text-zinc-700 dark:hover:text-zinc-300" target="_blank" rel="noopener noreferrer">GitHub</a>
            <a href="/docs" className="hover:text-zinc-700 dark:hover:text-zinc-300">Docs</a>
            <a href="/system" className="hover:text-zinc-700 dark:hover:text-zinc-300">Status</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
