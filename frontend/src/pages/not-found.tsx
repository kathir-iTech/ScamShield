import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ShieldAlert } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
      <ShieldAlert className="h-16 w-16 text-zinc-300 dark:text-zinc-600" />
      <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
        Page not found
      </h1>
      <p className="max-w-sm text-sm text-zinc-500 dark:text-zinc-400">
        The page you are looking for does not exist or has been moved.
      </p>
      <Link to="/">
        <Button>Back to Dashboard</Button>
      </Link>
    </div>
  );
}
