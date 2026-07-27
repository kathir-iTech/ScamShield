import { Sun, Moon, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface HeaderProps {
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
}

export function Header({ theme, onToggleTheme }: HeaderProps) {
  return (
    <header className="flex h-16 items-center justify-between border-b border-zinc-200 bg-white px-6 dark:border-zinc-700 dark:bg-zinc-900">
      <div>
        <span className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          ScamShield Console
        </span>
        <p className="text-xs text-zinc-500 dark:text-zinc-400">
          AI-Powered Scam Detection Platform
        </p>
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleTheme}
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
          {theme === 'light' ? (
            <Moon className="h-5 w-5" />
          ) : (
            <Sun className="h-5 w-5" />
          )}
        </Button>
        <a
          href="https://github.com/anomalyco/opencode"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="GitHub repository"
        >
          <Button variant="ghost" size="icon">
            <ExternalLink className="h-5 w-5" />
          </Button>
        </a>
      </div>
    </header>
  );
}
