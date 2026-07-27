import { useState, useMemo, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/status-badge';
import { riskStatus } from '@/design/status';
import { CopyButton } from '@/components/ui/copy-button';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { memo } from 'react';
import { cn } from '@/utils/cn';
import type { EntityItem } from '@/types';

interface EntityCardProps {
  entities: EntityItem[];
}

const entityGroupLabels: Record<string, string> = {
  url: 'URLs',
  shortened_url: 'Shortened URLs',
  suspicious_tld: 'Suspicious TLDs',
  email: 'Email Addresses',
  email_raw: 'Email Addresses',
  phone_indian: 'Indian Phone Numbers',
  phone_international: 'International Phone Numbers',
  upi_id: 'UPI IDs',
  otp_code: 'OTP Codes',
  bank_name: 'Bank Names',
  bank_account: 'Bank Accounts',
  ifsc_code: 'IFSC Codes',
  ip_address: 'IP Addresses',
  government_entity: 'Government Entities',
  currency_amount: 'Currency Amounts',
  domain: 'Domains',
  social_handle: 'Social Handles',
  tracking_id: 'Tracking IDs',
  transaction_id: 'Transaction IDs',
  qr_keyword: 'QR Code References',
};

function riskBorder(risk: string): string {
  switch (risk) {
    case 'HIGH': return 'border-red-300 bg-red-50 dark:border-red-700 dark:bg-red-900/20';
    case 'MEDIUM': return 'border-amber-300 bg-amber-50 dark:border-amber-700 dark:bg-amber-900/20';
    default: return 'border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800/50';
  }
}

const EntityGroup = memo(function EntityGroup({
  type,
  items,
  defaultOpen,
}: {
  type: string;
  items: EntityItem[];
  defaultOpen: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const toggle = useCallback(() => setOpen((p) => !p), []);

  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-700">
      <button
        type="button"
        onClick={toggle}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500 hover:bg-zinc-50 dark:text-zinc-400 dark:hover:bg-zinc-800/50"
        aria-expanded={open}
        aria-label={`${entityGroupLabels[type] || type} (${items.length})`}
      >
        <span>{entityGroupLabels[type] || type} ({items.length})</span>
        {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="flex flex-wrap gap-2 border-t border-zinc-200 px-3 py-2 dark:border-zinc-700">
              {items.map((item, i) => (
                <div
                  key={`${item.value}-${i}`}
                  className={cn(
                    'group relative inline-flex max-w-full items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium',
                    riskBorder(item.risk)
                  )}
                >
                  <span className="max-w-[180px] truncate" title={item.value}>
                    {item.value}
                  </span>
                  {item.risk === 'HIGH' && (
                    <StatusBadge status={riskStatus('HIGH')} size="sm" showIcon={false} className="text-[9px] px-1 py-0" />
                  )}
                  {item.risk === 'MEDIUM' && (
                    <StatusBadge status={riskStatus('MEDIUM')} size="sm" showIcon={false} className="text-[9px] px-1 py-0" />
                  )}
                  <CopyButton text={item.value} label={`Copy ${item.value}`} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
});

export const EntityCard = memo(function EntityCard({ entities }: EntityCardProps) {
  const grouped = useMemo(() => {
    const map: Record<string, EntityItem[]> = {};
    for (const e of entities) {
      const key = e.type;
      if (!map[key]) map[key] = [];
      map[key].push(e);
    }
    return Object.entries(map).sort(([, a], [, b]) => b.length - a.length);
  }, [entities]);

  if (entities.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Detected Entities ({entities.length})</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {grouped.map(([type, items], i) => (
          <EntityGroup key={type} type={type} items={items} defaultOpen={i < 2 || grouped.length <= 3} />
        ))}
      </CardContent>
    </Card>
  );
});
