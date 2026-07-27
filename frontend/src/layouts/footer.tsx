import { Link } from 'react-router-dom';

export function Footer() {
  return (
    <footer className="border-t border-zinc-100 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-8 py-6">
        <p className="text-xs text-zinc-400">
          &copy; {new Date().getFullYear()} ScamShield
        </p>
        <nav className="flex gap-6" aria-label="Footer navigation">
          <Link to="/privacy" className="text-xs text-zinc-400 transition-colors hover:text-zinc-600 dark:hover:text-zinc-300">Privacy</Link>
          <Link to="/terms" className="text-xs text-zinc-400 transition-colors hover:text-zinc-600 dark:hover:text-zinc-300">Terms</Link>
          <Link to="/disclaimer" className="text-xs text-zinc-400 transition-colors hover:text-zinc-600 dark:hover:text-zinc-300">Disclaimer</Link>
          <Link to="/contact" className="text-xs text-zinc-400 transition-colors hover:text-zinc-600 dark:hover:text-zinc-300">Contact</Link>
        </nav>
      </div>
    </footer>
  );
}
