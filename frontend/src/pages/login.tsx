import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { PageTransition } from '@/components/ui/page-transition';
import { useAuth } from '@/features/auth';
import { LogIn } from 'lucide-react';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const from = params.get('from') || '/';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('Enter your email and password.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await login(email.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setError((err as Error).message || 'Sign in failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-md px-6 py-16 sm:py-20">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass">
            <LogIn className="h-6 w-6 text-accent" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">Sign in</h1>
          <p className="mt-2 text-sm text-text-secondary/70">
            Access your saved analyses and feedback from any device.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="glass rounded-2xl p-7 animate-slide-up" noValidate>
          <label className="block text-xs font-medium text-text-secondary">
            Email
            <input
              type="email"
              name="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="mt-1.5 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none"
            />
          </label>

          <label className="mt-4 block text-xs font-medium text-text-secondary">
            Password
            <input
              type="password"
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Your password"
              className="mt-1.5 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none"
            />
          </label>

          {error && (
            <p className="mt-4 rounded-xl border border-danger/30 bg-danger/10 p-3 text-sm text-danger" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="mt-5 inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-accent px-5 text-sm font-semibold text-white hover:bg-accent/90 disabled:opacity-40"
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>

          <p className="mt-4 text-center text-sm text-text-tertiary">
            No account yet?{' '}
            <Link to="/register" className="font-medium text-accent hover:underline">
              Create one
            </Link>
          </p>
        </form>
      </div>
    </PageTransition>
  );
}
