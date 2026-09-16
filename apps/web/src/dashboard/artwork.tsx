import type { ReactNode } from 'react';

export type IconName =
  | 'activity'
  | 'bell'
  | 'building'
  | 'calendar'
  | 'catalog'
  | 'check'
  | 'document'
  | 'employerIntake'
  | 'home'
  | 'map'
  | 'moon'
  | 'queue'
  | 'reports'
  | 'schedule'
  | 'search'
  | 'sun'
  | 'warning'
  | 'worker'
  | 'workers';

type IconSymbolProps = {
  className?: string;
  name: IconName;
};

const iconPaths: Record<IconName, ReactNode> = {
  activity: (
    <>
      <path d="M4 13h4l2-7 4 12 2-5h4" />
      <path d="M3 18h18" />
    </>
  ),
  bell: (
    <>
      <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z" />
      <path d="M10 21h4" />
    </>
  ),
  building: (
    <>
      <path d="M5 21V5l9-2v18" />
      <path d="M14 8h5v13" />
      <path d="M8 8h2M8 12h2M8 16h2M17 12h1M17 16h1" />
    </>
  ),
  calendar: (
    <>
      <path d="M5 4v3M19 4v3" />
      <rect height="16" rx="2" width="18" x="3" y="5" />
      <path d="M3 10h18M8 14h3M13 14h3M8 17h3" />
    </>
  ),
  catalog: (
    <>
      <path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3Z" />
      <path d="M8 4v13a3 3 0 0 0 3 3" />
      <path d="M10 8h5M10 12h5" />
    </>
  ),
  check: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="m8 12 2.5 2.5L16 9" />
    </>
  ),
  document: (
    <>
      <path d="M7 3h7l4 4v14H7Z" />
      <path d="M14 3v5h4" />
      <path d="M9 12h6M9 16h6" />
    </>
  ),
  employerIntake: (
    <>
      <path d="M6 21V4h8l4 4v13" />
      <path d="M14 4v5h4" />
      <path d="M9 12h5M9 16h3" />
      <path d="M4 21h16" />
    </>
  ),
  home: (
    <>
      <path d="m3 11 9-8 9 8" />
      <path d="M5 10v11h14V10" />
      <path d="M10 21v-6h4v6" />
    </>
  ),
  map: (
    <>
      <path d="m4 6 5-2 6 2 5-2v14l-5 2-6-2-5 2Z" />
      <path d="M9 4v14M15 6v14" />
    </>
  ),
  moon: <path d="M20 15.5A8.5 8.5 0 0 1 8.5 4a7 7 0 1 0 11.5 11.5Z" />,
  queue: (
    <>
      <path d="M5 7h2M11 7h8M5 12h2M11 12h8M5 17h2M11 17h8" />
      <path d="M3 5h.01M3 10h.01M3 15h.01" />
    </>
  ),
  reports: (
    <>
      <path d="M5 20V10M12 20V4M19 20v-7" />
      <path d="M3 20h18" />
    </>
  ),
  schedule: (
    <>
      <rect height="16" rx="2" width="18" x="3" y="5" />
      <path d="M8 3v4M16 3v4M3 10h18" />
      <path d="M8 15h4l2-2" />
    </>
  ),
  search: (
    <>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m16 16 5 5" />
    </>
  ),
  sun: (
    <>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </>
  ),
  warning: (
    <>
      <path d="m12 3 10 18H2Z" />
      <path d="M12 9v5M12 17h.01" />
    </>
  ),
  worker: (
    <>
      <circle cx="9" cy="8" r="3" />
      <path d="M3 20a6 6 0 0 1 12 0" />
      <path d="M16 11a3 3 0 1 0 0-6" />
      <path d="M17 20a5 5 0 0 0-3-4.6" />
    </>
  ),
  workers: (
    <>
      <circle cx="8" cy="8" r="3" />
      <circle cx="17" cy="8" r="3" />
      <path d="M2.5 20a5.5 5.5 0 0 1 11 0" />
      <path d="M13.5 20a5.5 5.5 0 0 1 8-4.9" />
    </>
  ),
};

export function IconSymbol({ className, name }: IconSymbolProps) {
  return (
    <svg aria-hidden="true" className={className ?? 'icon-symbol'} fill="none" focusable="false" viewBox="0 0 24 24">
      <g stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2">
        {iconPaths[name]}
      </g>
    </svg>
  );
}

export function BrandRose({ className }: { className?: string }) {
  return (
    <svg aria-hidden="true" className={className ?? 'brand-rose'} focusable="false" viewBox="0 0 92 82">
      <defs>
        <linearGradient id="brand-rose-left" x1="14" x2="46" y1="18" y2="66" gradientUnits="userSpaceOnUse">
          <stop stopColor="#C3824A" />
          <stop offset="1" stopColor="#8A3D1E" />
        </linearGradient>
        <linearGradient id="brand-rose-center" x1="40" x2="48" y1="8" y2="55" gradientUnits="userSpaceOnUse">
          <stop stopColor="#D9A46A" />
          <stop offset="1" stopColor="#A95D2F" />
        </linearGradient>
        <linearGradient id="brand-rose-right" x1="52" x2="76" y1="19" y2="60" gradientUnits="userSpaceOnUse">
          <stop stopColor="#A2251D" />
          <stop offset="1" stopColor="#6E170F" />
        </linearGradient>
      </defs>
      <g stroke="#FFF9F4" strokeLinejoin="round" strokeWidth="3.5">
        <path d="M43 70C24 64 13 48 16 24c20-1 33 13 31 35Z" fill="url(#brand-rose-left)" />
        <path d="M46 58C34 45 32 25 45 9c15 8 21 24 13 42Z" fill="url(#brand-rose-center)" />
        <path d="M47 70c-4-22 7-39 29-46 7 22-6 40-29 46Z" fill="url(#brand-rose-right)" />
        <path d="M27 22C32 10 45 3 59 8c-2 14-14 22-27 21Z" fill="#B36A35" />
      </g>
    </svg>
  );
}

export function SkylineArtwork() {
  return <span className="skyline-artwork" />;
}

export function MissionStatementMark() {
  return (
    <svg
      aria-label="La comunidad nos mueve"
      className="mission-statement-mark"
      focusable="false"
      role="img"
      viewBox="0 0 420 150"
    >
      <g fill="none" stroke="#9d3f22" strokeLinecap="round" strokeLinejoin="round">
        <text
          fill="#9d3f22"
          fontFamily="Snell Roundhand, Apple Chancery, Segoe Script, Brush Script MT, cursive"
          fontSize="44"
          fontStyle="italic"
          fontWeight="500"
          stroke="none"
          transform="rotate(-8 162 64)"
          x="34"
          y="70"
        >
          La comunidad
        </text>
        <text
          fill="#9d3f22"
          fontFamily="Snell Roundhand, Apple Chancery, Segoe Script, Brush Script MT, cursive"
          fontSize="40"
          fontStyle="italic"
          fontWeight="500"
          stroke="none"
          transform="rotate(-8 154 108)"
          x="92"
          y="112"
        >
          nos mueve
        </text>
        <path d="M334 56c9-21 36-14 27 11-5 13-19 24-29 34-9-12-22-25-22-38 0-13 15-18 24-7Z" strokeWidth="4.5" transform="rotate(-7 334 78)" />
        <path d="M20 92c18-9 38-19 58-36" strokeWidth="3" opacity="0.7" />
      </g>
    </svg>
  );
}

export function ZoneMapArtwork() {
  return (
    <svg aria-hidden="true" className="zone-map-artwork" focusable="false" viewBox="0 0 600 300">
      <path className="zone-map-artwork__water" d="M0 0h600v300H0Z" />
      <path className="zone-map-artwork__land" d="M70 272C114 194 98 86 194 50c62-23 123 24 162 59 48 43 98 38 174 15 37 65 10 134-55 160Z" />
      <path className="zone-map-artwork__land zone-map-artwork__land--secondary" d="M18 300C78 196 128 154 218 146c76-7 108 32 163 70 48 34 91 45 158 28l61 56Z" />
      <path className="zone-map-artwork__road" d="M92 252C168 180 246 139 340 82M148 52c66 62 120 126 162 194M246 286c44-82 98-148 198-198M62 156c104 18 198 46 288 84" />
      <path className="zone-map-artwork__park" d="M124 214c34-34 73-44 118-30 4 44-16 72-60 84-29-9-48-27-58-54Z" />
    </svg>
  );
}
