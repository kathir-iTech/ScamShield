import { Link } from 'react-router-dom';

export function Footer() {
  return (
    <footer className="border-t border-glass-border bg-glass backdrop-blur-2xl">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
        <p className="text-xs text-text-tertiary">
          &copy; {new Date().getFullYear()} ScamShield
        </p>
        <nav className="flex gap-5" aria-label="Footer navigation">
          <Link to="/privacy" className="text-xs text-text-tertiary transition-colors hover:text-text-secondary">Privacy</Link>
          <Link to="/terms" className="text-xs text-text-tertiary transition-colors hover:text-text-secondary">Terms</Link>
          <Link to="/disclaimer" className="text-xs text-text-tertiary transition-colors hover:text-text-secondary">Disclaimer</Link>
          <Link to="/contact" className="text-xs text-text-tertiary transition-colors hover:text-text-secondary">Contact</Link>
        </nav>
      </div>
    </footer>
  );
}
