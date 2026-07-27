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
    <aside
      className="group/sidebar fixed left-3 top-3 bottom-3 z-40 hidden w-[56px] flex-col items-center rounded-2xl border border-glass-border bg-glass backdrop-blur-2xl py-4 will-change-[width] transition-all duration-300 hover:w-44 md:flex"
    >
      <div className="mb-6 flex items-center justify-center">
        <Shield className="h-5 w-5 shrink-0 text-accent" />
      </div>
      <nav className="flex w-full flex-1 flex-col items-center gap-1.5 px-2.5" aria-label="Main navigation">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              cn(
                'relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'text-accent'
                  : 'text-text-tertiary hover:text-text-secondary hover:bg-glass-hover'
              )
            }
            aria-label={item.label}
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <span className="absolute inset-0 rounded-xl bg-accent/10 border border-accent/20 animate-scale-in" />
                )}
                <item.icon className="relative z-10 h-4.5 w-4.5 shrink-0" />
                <span className="invisible relative z-10 text-sm font-medium opacity-0 transition-all duration-300 group-hover/sidebar:visible group-hover/sidebar:opacity-100">
                  {item.label}
                </span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
