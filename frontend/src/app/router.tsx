import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { RootLayout } from '@/layouts/root-layout';
import { PageSkeleton } from '@/components/ui/page-skeleton';

const Landing = lazy(() => import('@/pages/landing'));
const TextAnalysis = lazy(() => import('@/pages/text-analysis'));
const ImageAnalysis = lazy(() => import('@/pages/image-analysis'));
const AnalysisResult = lazy(() => import('@/pages/analysis-result'));
const Investigation = lazy(() => import('@/pages/investigation'));
const Dashboard = lazy(() => import('@/pages/dashboard'));
const SystemStatus = lazy(() => import('@/pages/system-status'));
const NotFound = lazy(() => import('@/pages/not-found'));

const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<PageSkeleton variant="dashboard" />}>
            <Landing />
          </Suspense>
        ),
      },
      {
        path: 'dashboard',
        element: (
          <Suspense fallback={<PageSkeleton variant="dashboard" />}>
            <Dashboard />
          </Suspense>
        ),
      },
      {
        path: 'analyze/text',
        element: (
          <Suspense fallback={<PageSkeleton variant="analysis" />}>
            <TextAnalysis />
          </Suspense>
        ),
      },
      {
        path: 'analyze/image',
        element: (
          <Suspense fallback={<PageSkeleton variant="analysis" />}>
            <ImageAnalysis />
          </Suspense>
        ),
      },
      {
        path: 'analysis/result',
        element: (
          <Suspense fallback={<PageSkeleton variant="report" />}>
            <AnalysisResult />
          </Suspense>
        ),
      },
      {
        path: 'investigation',
        element: (
          <Suspense fallback={<PageSkeleton variant="report" />}>
            <Investigation />
          </Suspense>
        ),
      },
      {
        path: 'system',
        element: (
          <Suspense fallback={<PageSkeleton variant="system" />}>
            <SystemStatus />
          </Suspense>
        ),
      },
      {
        path: '*',
        element: (
          <Suspense fallback={<PageSkeleton variant="dashboard" />}>
            <NotFound />
          </Suspense>
        ),
      },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
