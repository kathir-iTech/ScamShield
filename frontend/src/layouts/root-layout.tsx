import { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '@/layouts/sidebar';
import { Header } from '@/layouts/header';
import { Footer } from '@/layouts/footer';
import { ToastContainer } from '@/components/toast-container';
import { ErrorBoundary } from '@/components/error-boundary';
import { useToast } from '@/hooks/use-toast';

export function RootLayout() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const { toasts, removeToast } = useToast();

  useEffect(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      setTheme('dark');
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => {
      const next = prev === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme', next);
      document.documentElement.classList.toggle('dark', next === 'dark');
      return next;
    });
  };

  return (
    <div className="flex h-screen bg-zinc-50 dark:bg-zinc-950">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-[100] focus:rounded focus:bg-white focus:px-4 focus:py-2 focus:text-emerald-700 focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
      >
        Skip to main content
      </a>
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header theme={theme} onToggleTheme={toggleTheme} />
        <main id="main-content" className="flex-1 overflow-y-auto p-6">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
        <Footer />
      </div>
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}
