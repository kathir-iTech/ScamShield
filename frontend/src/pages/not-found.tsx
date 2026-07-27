import { useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="flex h-full flex-col items-center justify-center gap-5 px-6 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-2xl glass">
        <ShieldAlert className="h-10 w-10 text-text-tertiary" />
      </div>
      <h1 className="text-3xl font-bold tracking-tight text-text-primary">
        Page not found
      </h1>
      <p className="max-w-sm text-sm text-text-secondary/70">
        The page you're looking for doesn't exist.
      </p>
      <button
        onClick={() => navigate('/')}
        className="glass-button relative inline-flex h-11 items-center gap-2 rounded-xl px-5 text-sm font-semibold text-white"
      >
        <ArrowLeft className="h-4 w-4" />
        Go home
      </button>
    </div>
  );
}
