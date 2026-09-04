import { useState, useRef, useCallback } from 'react';
import { cn } from '@/utils/cn';

interface GlassInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
  placeholder?: string;
  maxLength?: number;
  className?: string;
}

export function GlassInput({
  value,
  onChange,
  onSubmit,
  placeholder = 'Paste a suspicious message to analyse...',
  maxLength = 5000,
  className,
}: GlassInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isFocused, setIsFocused] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const autoResize = useCallback(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 320)}px`;
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const text = e.dataTransfer.getData('text');
    if (text) {
      onChange(text);
    }
  }, [onChange]);

  const handlePaste = useCallback((e: React.ClipboardEvent) => {
    const text = e.clipboardData.getData('text');
    if (text) {
      setTimeout(() => {
        autoResize();
      }, 0);
    }
  }, [autoResize]);

  return (
    <div className={cn('group relative', className)}>
      {isDragging && (
        <div
          className="absolute inset-0 z-10 flex items-center justify-center rounded-2xl border-2 border-dashed border-accent/50 glass-strong animate-fade-in"
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <p className="text-lg font-medium text-accent">Drop message here</p>
        </div>
      )}
      <div
        className={cn(
          'relative overflow-hidden rounded-2xl transition-all duration-300',
          'glass-input',
          isFocused && 'shadow-[0_0_40px_rgba(10,132,255,0.08)]',
        )}
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      >
        {!value && !isFocused && (
          <div
            className="absolute left-5 top-5 right-5 pointer-events-none select-none"
            aria-hidden="true"
          >
            <p className="text-base text-text-secondary/50 leading-relaxed">
              {placeholder}
            </p>
          </div>
        )}
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            autoResize();
          }}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          onPaste={handlePaste}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              onSubmit?.();
            }
          }}
          maxLength={maxLength}
          className="relative z-[1] min-h-[140px] w-full resize-none bg-transparent px-5 py-5 text-base leading-relaxed text-text-primary placeholder-transparent focus:outline-none"
          aria-label="Message to analyse"
          rows={4}
        />
        <div className="flex justify-end px-5 pb-3">
          <span
            className={cn(
              'text-xs tabular-nums transition-colors duration-200',
              value.length > maxLength * 0.9 ? 'text-danger' : 'text-text-tertiary'
            )}
          >
            {value.length}/{maxLength}
          </span>
        </div>
      </div>
    </div>
  );
}
