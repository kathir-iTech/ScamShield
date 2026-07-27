import { Providers } from '@/app/providers';
import { AnalysisProvider } from '@/features/analysis/context/analysis-context';
import { AppRouter } from '@/app/router';

export default function App() {
  return (
    <Providers>
      <AnalysisProvider>
        <AppRouter />
      </AnalysisProvider>
    </Providers>
  );
}
