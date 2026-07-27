import { cn } from '@/utils/cn';

interface VerdictHeroProps {
  verdict: 'safe' | 'scam' | 'suspicious';
  title: string;
  confidence: number;
  description?: string;
  className?: string;
}

const verdictConfig = {
  safe: {
    icon: (
      <svg viewBox="0 0 80 80" fill="none" className="h-full w-full">
        <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="2" className="text-success/30" />
        <path d="M24 40L34 50L56 28" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" className="text-success" />
        <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="2" strokeDasharray="4 4" className="text-success/20" />
      </svg>
    ),
    accent: 'text-success',
    gradient: 'text-gradient-success',
    glow: 'shadow-[0_0_60px_rgba(48,209,88,0.15)]',
    borderAccent: 'border-success/20',
  },
  scam: {
    icon: (
      <svg viewBox="0 0 80 80" fill="none" className="h-full w-full">
        <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="2" className="text-danger/30" />
        <path d="M28 28L52 52M52 28L28 52" stroke="currentColor" strokeWidth="4" strokeLinecap="round" className="text-danger" />
        <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="2" strokeDasharray="4 4" className="text-danger/20" />
      </svg>
    ),
    accent: 'text-danger',
    gradient: 'text-gradient-danger',
    glow: 'shadow-[0_0_60px_rgba(255,69,58,0.15)]',
    borderAccent: 'border-danger/20',
  },
  suspicious: {
    icon: (
      <svg viewBox="0 0 80 80" fill="none" className="h-full w-full">
        <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="2" className="text-warning/30" />
        <path d="M40 24V44M40 52V54" stroke="currentColor" strokeWidth="4" strokeLinecap="round" className="text-warning" />
        <circle cx="40" cy="40" r="36" stroke="currentColor" strokeWidth="2" strokeDasharray="4 4" className="text-warning/20" />
      </svg>
    ),
    accent: 'text-warning',
    gradient: 'text-gradient',
    glow: 'shadow-[0_0_60px_rgba(255,159,10,0.15)]',
    borderAccent: 'border-warning/20',
  },
};

export function VerdictHero({ verdict, title, confidence, description, className }: VerdictHeroProps) {
  const cfg = verdictConfig[verdict];

  return (
    <div className={cn('text-center', className)}>
      <div
        className={cn(
          'mx-auto mb-8 h-24 w-24 animate-verdict-enter',
          cfg.glow,
        )}
      >
        {cfg.icon}
      </div>

      <h1
        className={cn(
          'animate-verdict-enter text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl',
          cfg.gradient,
        )}
        style={{ animationDelay: '0.1s' }}
      >
        {title}
      </h1>

      <div className="mt-6 flex items-center justify-center gap-3 animate-slide-up" style={{ animationDelay: '0.3s' }}>
        <div className="glass-strong rounded-full px-4 py-1.5">
          <span className={cn('text-sm font-semibold', cfg.accent)}>
            {confidence}% confidence
          </span>
        </div>
      </div>

      {description && (
        <p
          className="mx-auto mt-6 max-w-xl text-lg text-text-secondary/80 animate-slide-up leading-relaxed"
          style={{ animationDelay: '0.4s' }}
        >
          {description}
        </p>
      )}
    </div>
  );
}
