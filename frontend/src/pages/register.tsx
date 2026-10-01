import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { PageTransition } from '@/components/ui/page-transition';
import { useAuth } from '@/features/auth';
import { Check, Circle, UserPlus } from 'lucide-react';

const MIN_PASSWORD_LENGTH = 10;

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const hasLength = password.length >= MIN_PASSWORD_LENGTH;
  const hasLetterAndDigit = /[A-Za-z]/.test(password) && /\d/.test(password);
  const passwordValid = hasLength && hasLetterAndDigit;
  const canSubmit = email.trim().length > 0 && displayName.trim().length > 0 && passwordValid;

  const hints = [
    { valid: hasLength, label: `At least ${MIN_PASSWORD_LENGTH} characters` },
    { valid: hasLetterAndDigit, label: 'Contains a letter and a digit' },
  ];

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!canSubmit) {
      setError('Fill in every field and meet the password rules above.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await register(email.trim(), password, displayName.trim());
      navigate('/', { replace: true });
    } catch (err) {
      setError((err as Error).message || 'Could not create the account. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <PageTransition>
      <div className="mx-auto max-w-md px-6 py-16 sm:py-20">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl glass">
            <UserPlus className="h-6 w-6 text-accent" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">Create account</h1>
          <p className="mt-2 text-sm text-text-secondary/70">
            One account for the web app, the extension, and every future channel.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="glass rounded-2xl p-7 animate-slide-up" noValidate>
          <label className="block text-xs font-medium text-text-secondary">
            Display name
            <input
              type="text"
              name="display_name"
              autoComplete="name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="How should we address you?"
              className="mt-1.5 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none"
            />
          </label>

          <label className="mt-4 block text-xs font-medium text-text-secondary">
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

          <div className="mt-4">
            <label className="block text-xs font-medium text-text-secondary">
              Password
              <input
                type="password"
                name="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Choose a strong password"
                className="mt-1.5 w-full rounded-xl border border-glass-border bg-glass px-3 py-3 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none"
              />
            </label>
            <ul className="mt-2 space-y-1">
              {hints.map((hint) => (
                <li
                  key={hint.label}
                  className={`flex items-center gap-1.5 text-xs ${hint.valid ? 'text-success' : 'text-text-tertiary'}`}
                >
                  {hint.valid ? <Check className="h-3.5 w-3.5" /> : <Circle className="h-3.5 w-3.5" />}
                  {hint.label}
                </li>
              ))}
            </ul>
          </div>

          {error && (
            <p className="mt-4 rounded-xl border border-danger/30 bg-danger/10 p-3 text-sm text-danger" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting || !canSubmit}
            className="mt-5 inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-accent px-5 text-sm font-semibold text-white hover:bg-accent/90 disabled:opacity-40"
          >
            {submitting ? 'Creating account…' : 'Create account'}
          </button>

          <p className="mt-4 text-center text-sm text-text-tertiary">
            Already registered?{' '}
            <Link to="/login" className="font-medium text-accent hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </PageTransition>
  );
}
