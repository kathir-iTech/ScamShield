import { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { cn } from '@/utils/cn';
import { getAppVersion } from '@/utils/version';
import {
  LayoutDashboard,
  FileText,
  Image as ImageIcon,
  Activity,
  Shield,
  Search,
  Home,
} from 'lucide-react';

const navItems = [
  { to: '/', icon: Home, label: 'Home' },
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/analyze/text', icon: FileText, label: 'Text Analysis' },
  { to: '/analyze/image', icon: ImageIcon, label: 'Image Analysis' },
  { to: '/investigation', icon: Search, label: 'Investigation' },
  { to: '/system', icon: Activity, label: 'System Status' },
];

export function Sidebar() {
  const [version, setVersion] = useState('...');

  useEffect(() => {
    getAppVersion().then(setVersion).catch(() => setVersion('unknown'));
  }, []);

  return (
    <aside className="flex h-full w-64 flex-col border-r border-zinc-200 bg-white dark:border-zinc-700 dark:bg-zinc-900">
      <div className="flex items-center gap-2 border-b border-zinc-200 px-6 py-4 dark:border-zinc-700">
        <Shield className="h-6 w-6 text-emerald-600" />
        <span className="text-lg font-bold text-zinc-900 dark:text-zinc-50">
          ScamShield
        </span>
      </div>
      <nav className="flex-1 space-y-1 p-4" aria-label="Main navigation">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors border-l-2',
                isActive
                  ? 'border-emerald-600 bg-emerald-50 text-emerald-700 dark:border-emerald-400 dark:bg-emerald-900/30 dark:text-emerald-400'
                  : 'border-transparent text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-800'
              )
            }
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-zinc-200 p-4 dark:border-zinc-700">
        <p className="text-xs text-zinc-400 dark:text-zinc-500">
          ScamShield v{version}
        </p>
      </div>
    </aside>
  );
}
