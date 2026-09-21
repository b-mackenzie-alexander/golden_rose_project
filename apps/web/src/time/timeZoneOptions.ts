import { DEFAULT_STAFF_TIME_ZONE } from './timeZone';

export const timeZoneOptions = [
  [DEFAULT_STAFF_TIME_ZONE, 'Eastern time - New York', 'Hora del Este - Nueva York'],
  ['America/Chicago', 'Central time - Chicago', 'Hora Central - Chicago'],
  ['America/Denver', 'Mountain time - Denver', 'Hora de la Montaña - Denver'],
  ['America/Los_Angeles', 'Pacific time - Los Angeles', 'Hora del Pacifico - Los Angeles'],
  ['America/Phoenix', 'Arizona time - Phoenix', 'Hora de Arizona - Phoenix'],
  ['America/Anchorage', 'Alaska time - Anchorage', 'Hora de Alaska - Anchorage'],
  ['Pacific/Honolulu', 'Hawaii time - Honolulu', 'Hora de Hawai - Honolulu'],
  ['Etc/UTC', 'UTC', 'UTC'],
] as const;

const timeZoneAliases: Record<string, string> = {
  EST: DEFAULT_STAFF_TIME_ZONE,
  EDT: DEFAULT_STAFF_TIME_ZONE,
  'America/New York': DEFAULT_STAFF_TIME_ZONE,
  'New York': DEFAULT_STAFF_TIME_ZONE,
};

export function normalizedTimeZone(value: unknown) {
  if (typeof value !== 'string' || !value.trim()) return DEFAULT_STAFF_TIME_ZONE;
  const trimmed = value.trim();
  if (timeZoneOptions.some(([zone]) => zone === trimmed)) return trimmed;
  return timeZoneAliases[trimmed] ?? DEFAULT_STAFF_TIME_ZONE;
}
