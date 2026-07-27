export function Footer() {
  return (
    <footer className="border-t border-zinc-200 px-6 py-3 dark:border-zinc-700">
      <p className="text-center text-xs text-zinc-400 dark:text-zinc-500">
        ScamShield &copy; {new Date().getFullYear()} &mdash; AI-Powered Scam Detection
      </p>
    </footer>
  );
}
