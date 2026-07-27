import { Outlet } from 'react-router-dom';
import { Sidebar } from '@/layouts/sidebar';
import { Header } from '@/layouts/header';
import { Footer } from '@/layouts/footer';
import { ToastContainer } from '@/components/toast-container';
import { ErrorBoundary } from '@/components/error-boundary';
import { AnimatedBackground } from '@/components/ui/animated-background';
import { useToast } from '@/hooks/use-toast';

export function RootLayout() {
  const { toasts, removeToast } = useToast();

  return (
    <div className="flex min-h-screen flex-col bg-[#08080c] text-text-primary selection:bg-accent/30">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:glass-strong focus:px-5 focus:py-3 focus:text-accent focus:outline-none focus:ring-2 focus:ring-accent"
      >
        Skip to main content
      </a>
      <AnimatedBackground />
      <Sidebar />
      <div className="flex flex-1 flex-col md:ml-[72px]">
        <Header />
        <main id="main-content" className="flex-1">
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
