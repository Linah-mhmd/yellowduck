export function DuckIcon({ size = 24, className = '' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <path d="M12 3c-2.5 0-4.5 1.8-4.9 4.2C4.8 8.1 3 10.2 3 12.8 3 16.1 5.7 19 9 19h8c2.8 0 5-2.2 5-5 0-2.4-1.7-4.4-4-4.8C17.6 5.4 15 3 12 3Z" fill="#F5B800" stroke="#D4A017" strokeWidth="1.2"/>
      <circle cx="9.5" cy="11" r="1.2" fill="#0F172A"/>
      <path d="M6 14.5c1.2 1.4 2.8 2.2 4.5 2.2" stroke="#D4A017" strokeWidth="1.2" strokeLinecap="round"/>
      <path d="M17 10.5c1.2.4 2 1.5 2 2.8" stroke="#F59E0B" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  );
}

export function MenuIcon({ size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );
}

export function BellIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3a5 5 0 00-5 5v3.5l-1.5 2.5h13L13 11.5V8a5 5 0 00-1-3z" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"/>
      <path d="M10 18a2 2 0 004 0" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  );
}

export function UserIcon({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.8"/>
      <path d="M5 20c1.5-3.5 4.5-5.5 7-5.5s5.5 2 7 5.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  );
}

export function TargetIcon({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="8" stroke="#D4A017" strokeWidth="1.8"/>
      <circle cx="12" cy="12" r="4" stroke="#F5B800" strokeWidth="1.8"/>
      <circle cx="12" cy="12" r="1.5" fill="#F5B800"/>
    </svg>
  );
}

export function ChartIcon({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 19V5M4 19h16" stroke="#64748B" strokeWidth="1.8" strokeLinecap="round"/>
      <path d="M8 15l3-4 3 2 4-6" stroke="#F5B800" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export function NetworkIcon({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="6" cy="12" r="3" stroke="#F5B800" strokeWidth="1.8"/>
      <circle cx="18" cy="7" r="3" stroke="#F5B800" strokeWidth="1.8"/>
      <circle cx="18" cy="17" r="3" stroke="#F5B800" strokeWidth="1.8"/>
      <path d="M9 11l6-3M9 13l6 3" stroke="#D4A017" strokeWidth="1.8"/>
    </svg>
  );
}

export function PerformanceIcon({ size = 24 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <rect x="5" y="10" width="3" height="9" rx="1" fill="#F5B800"/>
      <rect x="10.5" y="6" width="3" height="13" rx="1" fill="#FFD93D"/>
      <rect x="16" y="3" width="3" height="16" rx="1" fill="#D4A017"/>
    </svg>
  );
}

export const FEATURE_ICONS = {
  target: TargetIcon,
  chart: ChartIcon,
  network: NetworkIcon,
  performance: PerformanceIcon,
};
