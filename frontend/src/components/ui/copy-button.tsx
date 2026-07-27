import { useState, useCallback } from 'react';
import { Copy, Check } from 'lucide-react';
import { cn } from '@/utils/cn';

interface CopyButtonProps {
  text: string;
  label?: string;
  className?: string;
}

export function CopyButton({ text, label, className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard API not available
    }
  }, [text]);

  return (
    <button
      type="button"
      onClick={handleCopy}
      className={cn(
        'inline-flex items-center gap-1 rounded text-xs font-medium transition-colors',
        copied
          ? 'text-emerald-600 dark:text-emerald-400'
          : 'text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300',
        className
      )}
      aria-label={label ?? 'Copy to clipboard'}
    >
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      <span aria-live="polite" aria-atomic="true">{copied ? 'Copied' : 'Copy'}</span>
    </button>
  );
}
