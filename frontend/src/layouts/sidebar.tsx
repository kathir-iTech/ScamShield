import { NavLink } from 'react-router-dom';
import { cn } from '@/utils/cn';
import { FileText, Image, Activity, Shield, Search } from 'lucide-react';

const navItems = [
  { to: '/', icon: Shield, label: 'Home' },
  { to: '/analyze/text', icon: FileText, label: 'Text' },
  { to: '/analyze/image', icon: Image, label: 'Image' },
  { to: '/investigation', icon: Search, label: 'Deep Dive' },
  { to: '/system', icon: Activity, label: 'Status' },
];

export function Sidebar() {
  return (
    <aside className="group/sidebar flex h-full w-16 flex-col items-center border-r border-zinc-100 bg-white py-4 transition-all duration-200 hover:w-44 dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mb-6 flex items-center justify-center">
        <Shield className="h-6 w-6 text-emerald-500 shrink-0" />
      </div>
      <nav className="flex w-full flex-1 flex-col items-center gap-2 px-3" aria-label="Main navigation">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn(
                'flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 transition-all duration-200',
                isActive
                  ? 'bg-emerald-500 text-white shadow-sm'
                  : 'text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 dark:text-zinc-500 dark:hover:bg-zinc-800 dark:hover:text-zinc-300'
              )
            }
            aria-label={item.label}
          >
            <item.icon className="h-5 w-5 shrink-0" />
            <span className="invisible text-sm font-medium opacity-0 transition-all duration-200 group-hover/sidebar:visible group-hover/sidebar:opacity-100">
              {item.label}
            </span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
