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

type BoroughActivity = {
  count: number;
  intensity: 'high' | 'low' | 'medium' | 'mediumHigh';
  label: string;
  name: 'Bronx' | 'Brooklyn' | 'Manhattan' | 'Queens' | 'Staten Island';
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

// Derived from NYC Department of City Planning Borough Boundaries GeoJSON and simplified for dashboard SVG rendering.
const boroughPaths: Record<BoroughActivity['name'], string[]> = {
  Bronx: [
    'M 359.1 32.3 L 366.7 35.2 L 371.5 27.8 L 370.1 30.0 L 376.9 32.5 L 378.6 40.0 L 404.2 47.9 L 398.6 58.8 L 395.1 57.0 L 398.7 61.1 L 404.3 50.7 L 409.2 51.7 L 407.5 55.8 L 409.7 57.4 L 405.0 59.9 L 400.1 74.1 L 397.6 64.2 L 395.7 65.7 L 391.8 63.0 L 393.3 69.7 L 390.6 71.8 L 391.8 76.1 L 393.7 75.2 L 390.0 77.0 L 391.9 86.9 L 394.7 89.0 L 392.4 92.0 L 396.3 91.1 L 401.7 98.2 L 398.5 100.7 L 396.3 97.6 L 397.5 100.9 L 405.4 104.5 L 405.3 106.8 L 391.1 99.6 L 383.2 101.9 L 382.4 106.3 L 379.2 105.3 L 376.4 88.3 L 377.9 80.5 L 376.0 87.8 L 377.7 95.1 L 374.2 102.0 L 369.0 99.3 L 372.6 100.8 L 372.8 106.5 L 368.5 106.5 L 367.0 102.3 L 357.1 97.9 L 361.9 104.9 L 359.8 108.8 L 346.5 104.9 L 337.3 112.5 L 325.7 103.7 L 325.3 83.4 L 340.1 53.6 L 338.0 51.1 L 333.9 53.7 L 329.8 51.3 L 337.4 25.3 L 359.1 32.3 Z',
    'M 350.2 110.9 L 359.5 116.6 L 359.9 119.8 L 350.0 119.3 L 347.9 115.3 L 350.2 110.9 Z',
    'M 406.3 66.2 L 411.3 75.0 L 410.0 82.9 L 403.9 71.1 L 406.3 66.2 Z',
  ],
  Brooklyn: [
    'M 313.2 155.2 L 327.4 164.0 L 330.0 170.1 L 325.1 176.2 L 326.8 177.9 L 326.5 173.3 L 330.5 171.5 L 331.5 177.3 L 341.5 187.5 L 345.9 197.5 L 361.7 188.3 L 368.9 211.2 L 364.6 216.4 L 368.0 226.2 L 362.3 229.1 L 355.5 218.1 L 361.9 230.4 L 358.3 231.5 L 348.9 222.0 L 356.8 232.0 L 353.1 238.2 L 346.4 242.0 L 334.0 235.3 L 345.9 242.8 L 346.2 247.9 L 349.0 249.2 L 347.3 250.4 L 349.7 250.2 L 343.8 254.6 L 338.9 245.8 L 342.9 254.4 L 336.2 255.8 L 335.9 247.6 L 332.9 253.0 L 338.8 257.5 L 352.9 254.6 L 357.0 270.0 L 355.3 273.5 L 346.4 276.0 L 344.4 267.9 L 337.4 269.1 L 335.0 259.3 L 326.4 255.8 L 335.7 267.0 L 329.8 269.4 L 328.1 267.6 L 330.4 265.3 L 327.4 267.1 L 325.5 262.5 L 326.3 268.5 L 336.3 269.1 L 336.8 271.1 L 334.1 271.2 L 337.4 272.3 L 313.7 271.4 L 325.5 272.7 L 326.4 276.5 L 286.3 281.4 L 280.7 277.4 L 281.0 273.6 L 294.0 274.5 L 295.4 272.3 L 292.2 272.8 L 293.0 270.2 L 287.4 271.3 L 290.8 267.1 L 287.3 268.8 L 288.4 263.5 L 267.2 251.8 L 264.0 243.4 L 265.6 229.3 L 271.6 226.0 L 270.9 222.4 L 273.3 224.0 L 273.2 219.5 L 275.5 220.9 L 274.4 218.5 L 277.4 218.5 L 278.7 213.5 L 282.6 214.5 L 282.1 211.7 L 285.5 212.4 L 283.2 210.5 L 287.7 210.8 L 285.8 209.3 L 288.2 205.5 L 285.8 208.6 L 283.6 209.6 L 284.4 206.0 L 277.9 210.5 L 276.6 205.4 L 278.2 210.4 L 281.7 207.3 L 279.0 203.2 L 276.9 205.0 L 276.6 199.5 L 286.9 191.7 L 290.5 181.1 L 299.7 179.9 L 301.2 184.7 L 304.0 184.4 L 302.8 182.3 L 304.7 184.0 L 301.8 178.6 L 305.8 181.8 L 304.5 176.0 L 308.8 165.6 L 311.2 166.0 L 308.7 159.0 L 313.2 155.2 Z',
    'M 361.5 245.8 L 356.3 247.0 L 355.3 244.7 L 362.8 237.7 L 361.5 245.8 Z',
    'M 364.6 270.7 L 360.5 271.1 L 362.9 264.8 L 365.7 267.7 L 364.6 270.7 Z',
    'M 375.0 248.3 L 379.8 249.7 L 375.5 255.7 L 372.2 253.8 L 375.0 252.7 L 375.0 248.3 Z',
  ],
  Manhattan: [
    'M 329.0 52.2 L 331.2 52.8 L 331.9 55.6 L 332.1 53.8 L 338.0 56.8 L 332.9 66.2 L 331.7 65.3 L 331.7 67.8 L 324.2 83.7 L 324.5 102.8 L 327.5 109.1 L 327.4 113.0 L 319.5 122.4 L 319.7 128.8 L 303.6 151.7 L 303.0 157.7 L 301.9 157.6 L 303.6 164.0 L 300.6 175.8 L 288.6 178.0 L 286.7 180.7 L 283.8 181.6 L 284.4 182.5 L 282.2 182.9 L 282.8 183.8 L 279.0 184.1 L 276.6 179.8 L 278.1 170.5 L 280.1 170.3 L 278.2 169.2 L 280.4 168.3 L 280.9 165.1 L 278.9 164.7 L 281.0 164.7 L 281.1 163.3 L 279.4 163.2 L 281.3 159.8 L 279.6 159.5 L 281.4 159.5 L 281.6 155.2 L 280.3 154.0 L 282.1 154.0 L 281.1 153.2 L 282.4 152.4 L 280.6 151.9 L 282.5 151.7 L 280.8 150.4 L 282.1 150.3 L 280.9 149.7 L 282.3 149.6 L 281.0 148.9 L 282.4 148.8 L 281.2 148.1 L 281.9 145.0 L 284.8 141.3 L 283.5 140.3 L 285.3 140.1 L 286.2 138.6 L 284.9 137.8 L 286.6 137.7 L 285.4 136.9 L 286.9 137.2 L 285.7 136.2 L 287.7 137.1 L 286.2 135.6 L 288.5 135.6 L 286.6 134.5 L 288.6 135.3 L 287.1 133.6 L 289.1 134.4 L 287.6 132.6 L 289.1 133.2 L 288.0 131.9 L 290.3 131.2 L 289.6 129.3 L 290.9 129.9 L 291.8 128.5 L 293.8 125.1 L 292.2 125.1 L 293.7 124.9 L 294.7 120.9 L 311.1 93.4 L 310.3 92.3 L 315.0 85.7 L 317.9 77.3 L 317.4 72.4 L 320.3 69.9 L 329.0 52.2 Z',
    'M 331.8 109.3 L 335.7 113.2 L 335.3 115.9 L 330.1 123.1 L 328.0 124.1 L 324.1 122.6 L 325.6 117.6 L 329.4 116.0 L 328.1 116.7 L 328.5 109.7 L 329.6 108.5 L 331.8 109.3 Z',
    'M 278.0 189.3 L 280.8 189.9 L 280.5 192.3 L 274.5 197.0 L 272.6 194.6 L 276.4 189.5 L 278.0 189.3 Z',
  ],
  Queens: [
    'M 388.7 109.2 L 403.3 113.7 L 404.3 118.3 L 410.6 116.5 L 409.7 113.7 L 413.3 112.6 L 416.8 118.5 L 413.6 118.5 L 419.9 129.4 L 431.5 142.3 L 425.6 134.1 L 427.9 122.9 L 455.9 146.6 L 456.7 155.2 L 452.3 163.6 L 439.6 167.9 L 442.4 220.0 L 433.3 223.8 L 433.1 232.8 L 425.8 223.2 L 429.9 227.9 L 429.3 232.4 L 420.0 236.9 L 417.1 244.0 L 416.2 241.2 L 414.3 244.4 L 416.2 241.2 L 411.8 238.4 L 408.6 243.8 L 411.0 248.6 L 405.1 253.1 L 399.8 249.9 L 409.6 236.3 L 406.2 233.2 L 401.3 235.6 L 404.7 232.0 L 388.3 222.3 L 388.0 214.0 L 393.9 213.6 L 387.0 214.1 L 387.2 223.0 L 382.8 220.3 L 383.3 214.2 L 382.9 222.3 L 380.8 223.0 L 377.9 212.4 L 380.0 224.9 L 372.4 225.9 L 372.4 220.5 L 368.7 220.6 L 364.6 215.4 L 368.9 211.2 L 361.7 188.3 L 345.9 197.5 L 341.5 187.5 L 331.5 177.3 L 329.7 167.6 L 332.4 166.7 L 318.0 156.4 L 322.1 152.4 L 317.3 156.1 L 308.6 155.5 L 324.2 132.2 L 323.4 127.1 L 327.7 127.4 L 338.3 116.7 L 346.2 120.6 L 342.4 124.6 L 347.0 121.7 L 348.6 123.2 L 349.8 129.6 L 352.9 129.2 L 352.1 125.1 L 362.0 119.3 L 359.4 124.2 L 369.2 130.6 L 364.9 134.7 L 371.7 140.1 L 378.2 135.2 L 373.3 134.7 L 370.7 125.4 L 372.5 123.1 L 366.8 121.1 L 370.5 118.7 L 370.0 114.4 L 378.9 111.1 L 379.2 118.1 L 381.7 118.5 L 384.5 115.2 L 383.1 112.6 L 388.7 109.2 Z',
    'M 419.1 248.1 L 422.0 252.0 L 430.9 249.8 L 435.0 256.4 L 433.1 261.2 L 435.2 262.8 L 392.6 271.0 L 340.0 291.8 L 320.9 302.0 L 321.7 292.2 L 329.1 287.3 L 337.1 284.1 L 343.0 286.4 L 348.0 282.1 L 356.5 281.9 L 371.8 272.0 L 388.2 268.6 L 394.8 263.5 L 397.0 265.6 L 395.8 263.1 L 398.9 264.2 L 398.6 259.6 L 407.9 256.3 L 406.0 262.6 L 412.4 251.6 L 414.8 252.1 L 414.5 255.5 L 410.8 260.4 L 414.4 257.4 L 418.2 260.4 L 417.8 251.7 L 414.8 249.9 L 419.1 248.1 Z',
    'M 387.1 229.7 L 391.9 252.4 L 388.3 262.7 L 381.5 263.0 L 382.0 260.4 L 388.2 258.7 L 388.7 249.6 L 388.1 252.4 L 385.9 248.2 L 381.1 248.0 L 383.8 240.7 L 382.2 241.5 L 381.4 230.1 L 385.7 232.1 L 387.1 229.7 Z',
  ],
  'Staten Island': [
    'M 241.1 222.8 L 247.1 225.2 L 246.3 236.2 L 249.1 237.3 L 246.4 236.4 L 246.0 238.7 L 258.0 258.9 L 246.1 274.9 L 228.4 293.7 L 218.4 299.8 L 210.3 311.3 L 208.3 306.9 L 211.9 306.7 L 215.6 302.0 L 212.5 298.3 L 207.2 301.7 L 207.8 305.5 L 187.3 318.8 L 183.2 318.7 L 177.4 325.7 L 175.2 323.4 L 170.4 324.3 L 164.8 330.6 L 146.7 335.5 L 143.4 327.3 L 146.2 321.1 L 152.2 318.2 L 147.6 301.1 L 157.4 291.8 L 164.2 292.5 L 167.9 289.7 L 172.1 266.7 L 176.1 261.1 L 173.1 252.6 L 174.2 236.2 L 177.7 230.9 L 186.0 225.1 L 186.2 227.5 L 189.1 225.2 L 189.9 228.6 L 193.8 227.2 L 201.3 231.1 L 241.1 222.8 Z',
  ],
};

const boroughLabelPositions: Record<BoroughActivity['name'], { x: number; y: number }> = {
  Bronx: { x: 442, y: 75 },
  Brooklyn: { x: 299, y: 252 },
  Manhattan: { x: 236, y: 152 },
  Queens: { x: 432, y: 194 },
  'Staten Island': { x: 159, y: 296 },
};

const boroughLabelWidths: Record<BoroughActivity['name'], number> = {
  Bronx: 92,
  Brooklyn: 112,
  Manhattan: 132,
  Queens: 98,
  'Staten Island': 148,
};

export function ZoneMapArtwork({ areas }: { areas: BoroughActivity[] }) {
  return (
    <svg aria-hidden="true" className="zone-map-artwork" focusable="false" preserveAspectRatio="xMidYMid slice" viewBox="105 18 405 330">
      <defs>
        <filter colorInterpolationFilters="sRGB" height="130%" id="zone-map-soften" width="130%" x="-15%" y="-15%">
          <feGaussianBlur in="SourceGraphic" result="blurred" stdDeviation="0.35" />
          <feComposite in="SourceGraphic" in2="blurred" operator="over" />
        </filter>
        <linearGradient id="zone-map-water-glow" x1="0" x2="1" y1="0" y2="1">
          <stop stopColor="#f6fbf9" />
          <stop offset="1" stopColor="#c8eaf2" />
        </linearGradient>
        <pattern height="34" id="zone-map-grid" patternUnits="userSpaceOnUse" width="34">
          <path className="zone-map-artwork__street-grid" d="M0 17H34M17 0V34" />
        </pattern>
      </defs>
      <rect className="zone-map-artwork__water" height="360" width="600" />
      <rect className="zone-map-artwork__grid" height="360" width="600" />
      <g className="zone-map-artwork__boroughs" filter="url(#zone-map-soften)">
        {areas.map((area) => (
          <g className="zone-map-artwork__borough" data-intensity={area.intensity} key={area.name}>
            {boroughPaths[area.name].map((path) => (
              <path d={path} key={path} />
            ))}
          </g>
        ))}
      </g>
      <g className="zone-map-artwork__parks">
        <path d="M330 46C359 44 379 60 389 86C374 98 350 99 323 87C314 72 315 55 330 46Z" />
        <path d="M194 256C217 247 243 251 258 270C249 295 218 308 185 301C174 282 177 267 194 256Z" />
        <path d="M407 220C432 213 455 220 470 241C451 258 422 260 397 246C393 234 396 226 407 220Z" />
      </g>
      <g className="zone-map-artwork__waterways">
        <path className="zone-map-artwork__waterway" d="M263 42C302 87 338 148 372 238" />
        <path className="zone-map-artwork__waterway" d="M320 127C352 151 384 176 416 199" />
        <path className="zone-map-artwork__waterway zone-map-artwork__waterway--west" d="M265 45C254 113 224 171 174 226" />
      </g>
      <g className="zone-map-artwork__roads">
        <path className="zone-map-artwork__road zone-map-artwork__road--major" d="M322 56C314 106 299 149 279 184M318 130C340 154 360 184 374 224M333 111C365 103 395 91 423 70" />
        <path className="zone-map-artwork__road" d="M275 201C309 191 341 186 371 190M259 228C291 234 322 249 352 271M118 305C152 290 188 283 224 286M388 238C419 235 448 224 475 206" />
        <path className="zone-map-artwork__road zone-map-artwork__road--secondary" d="M340 51C365 74 388 98 410 122M234 223C266 235 298 250 330 268M187 246C213 253 237 266 258 286M401 151C429 161 453 177 474 199" />
      </g>
      {areas.map((area) => {
        const position = boroughLabelPositions[area.name];
        const labelWidth = boroughLabelWidths[area.name];
        const badgeX = labelWidth / 2 - 19;
        const transform = `translate(${String(position.x)} ${String(position.y)})`;
        return (
          <g className="zone-map-artwork__label" key={area.name} transform={transform}>
            <rect height="34" rx="17" width={labelWidth} x={labelWidth / -2} y="-17" />
            <text className="zone-map-artwork__label-name" x={labelWidth / -2 + 14} y="5">{area.label}</text>
            <circle cx={badgeX} cy="0" r="14" />
            <text className="zone-map-artwork__label-count" x={badgeX} y="5">{area.count}</text>
          </g>
        );
      })}
    </svg>
  );
}
