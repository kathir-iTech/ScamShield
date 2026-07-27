import {
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  AlertTriangle,
  Info,
  CheckCircle,
  type LucideIcon,
} from 'lucide-react';

export type StatusVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

export interface StatusConfig {
  variant: StatusVariant;
  icon: LucideIcon;
  label: string;
}

export function riskStatus(level: string): StatusConfig {
  const l = level.toLowerCase();
  if (l.includes('critical')) return { variant: 'danger', icon: ShieldX, label: level };
  if (l.includes('high')) return { variant: 'danger', icon: ShieldAlert, label: level };
  if (l.includes('medium')) return { variant: 'warning', icon: AlertTriangle, label: level };
  if (l.includes('low') && l.includes('very')) return { variant: 'info', icon: Info, label: level };
  if (l.includes('low')) return { variant: 'success', icon: ShieldCheck, label: level };
  return { variant: 'success', icon: ShieldCheck, label: level };
}

export function decisionStatus(level: string): StatusConfig {
  const l = level.toLowerCase();
  if (l === 'critical') return { variant: 'danger', icon: ShieldX, label: level };
  if (l.includes('high') && !l.includes('low')) return { variant: 'danger', icon: ShieldAlert, label: level };
  if (l === 'suspicious') return { variant: 'warning', icon: AlertTriangle, label: level };
  if (l === 'low' || l.includes('low ')) return { variant: 'info', icon: Info, label: level };
  return { variant: 'success', icon: CheckCircle, label: level };
}

export function priorityStatus(priority: string): StatusConfig {
  const p = priority.toLowerCase();
  if (p === 'urgent') return { variant: 'danger', icon: ShieldX, label: priority };
  if (p === 'high') return { variant: 'warning', icon: AlertTriangle, label: priority };
  if (p === 'normal') return { variant: 'info', icon: Info, label: priority };
  return { variant: 'neutral', icon: Info, label: priority };
}

export function assessmentStatus(band: string): StatusConfig {
  if (band.includes('immediate action')) return { variant: 'danger', icon: ShieldX, label: band };
  if (band.includes('investigation')) return { variant: 'warning', icon: AlertTriangle, label: band };
  if (band.includes('assessment required')) return { variant: 'info', icon: Info, label: band };
  return { variant: 'success', icon: CheckCircle, label: band };
}

export function severityStatus(severity: string): StatusConfig {
  const s = severity.toLowerCase();
  if (s === 'critical' || s === 'high') return { variant: 'danger', icon: ShieldX, label: severity };
  if (s === 'medium') return { variant: 'warning', icon: AlertTriangle, label: severity };
  if (s === 'low') return { variant: 'info', icon: Info, label: severity };
  return { variant: 'neutral', icon: Info, label: severity };
}

export function predictionStatus(prediction: string): StatusConfig {
  if (prediction === 'scam') return { variant: 'danger', icon: ShieldX, label: 'SCAM' };
  return { variant: 'success', icon: CheckCircle, label: 'SAFE' };
}
