import { useNavigate } from 'react-router-dom';
import { Shield, ArrowRight } from 'lucide-react';

export function EmptyAnalysisState() {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass">
        <Shield className="h-6 w-6 text-text-tertiary" />
      </div>
      <h2 className="text-lg font-semibold text-text-primary">Nothing to review yet</h2>
      <p className="mt-1 text-sm text-text-secondary">Analyse a suspicious message or screenshot to see your result.</p>
      <div className="mt-6 flex gap-3">
        <button
          onClick={() => navigate('/analyze/text')}
          className="glass-button inline-flex h-11 items-center gap-2 rounded-xl px-5 text-sm font-semibold text-white"
        >
          Analyse a message <ArrowRight className="h-4 w-4" />
        </button>
        <button
          onClick={() => navigate('/analyze/image')}
          className="glass inline-flex h-11 items-center gap-2 rounded-xl px-5 text-sm font-medium text-text-secondary hover:text-text-primary transition-all duration-200"
        >
          Upload a screenshot
        </button>
      </div>
    </div>
  );
}
