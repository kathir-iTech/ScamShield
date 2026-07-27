import { type ButtonHTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/utils/cn';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-xl text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-30 active:scale-[0.97]',
  {
    variants: {
      variant: {
        primary: 'glass-button text-white',
        secondary: 'glass text-text-secondary hover:text-text-primary',
        outline: 'border border-glass-border bg-transparent hover:bg-glass-hover text-text-secondary hover:text-text-primary',
        destructive: 'bg-danger/20 text-danger border border-danger/20 hover:bg-danger/30',
        ghost: 'text-text-tertiary hover:text-text-secondary hover:bg-glass-hover',
      },
      size: {
        sm: 'h-9 rounded-lg px-4 text-xs',
        md: 'h-11 px-6',
        lg: 'h-13 px-8 text-base',
        xl: 'h-14 px-10 text-base',
        icon: 'h-11 w-11 rounded-xl',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size }), className)}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
