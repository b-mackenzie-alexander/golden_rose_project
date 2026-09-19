export const DEFAULT_STAFF_TIME_ZONE = 'America/New_York';

const LOCAL_DATE_TIME_PATTERN = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/;
const OFFSET_INSTANT_PATTERN =
  /^(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})(?::\d{2}(?:\.\d{1,6})?)?(Z|[+-]\d{2}:\d{2})$/;

function localPartsInZone(instantMs: number, timeZone: string) {
  const parts = new Intl.DateTimeFormat('en-US', {
    calendar: 'iso8601',
    day: '2-digit',
    hour: '2-digit',
    hour12: false,
    minute: '2-digit',
    month: '2-digit',
    second: '2-digit',
    timeZone,
    year: 'numeric',
  }).formatToParts(new Date(instantMs));
  const value = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  const hour = value.hour === '24' ? '00' : value.hour;
  return {
    year: Number(value.year),
    month: Number(value.month),
    day: Number(value.day),
    hour: Number(hour),
    minute: Number(value.minute),
    second: Number(value.second),
  };
}

function offsetMinutes(instantMs: number, timeZone: string) {
  const parts = localPartsInZone(instantMs, timeZone);
  const localAsUtcMs = Date.UTC(
    parts.year,
    parts.month - 1,
    parts.day,
    parts.hour,
    parts.minute,
    parts.second,
  );
  return (localAsUtcMs - instantMs) / 60000;
}

function offsetLabel(minutes: number) {
  const sign = minutes >= 0 ? '+' : '-';
  const abs = Math.abs(minutes);
  return `${sign}${String(Math.floor(abs / 60)).padStart(2, '0')}:${String(abs % 60).padStart(2, '0')}`;
}

export function zonedLocalDateTimeToOffsetInstant(localValue: string, timeZone: string) {
  const match = localValue.match(LOCAL_DATE_TIME_PATTERN);
  if (!match) return null;
  const [, yearText, monthText, dayText, hourText, minuteText] = match;
  if (!yearText || !monthText || !dayText || !hourText || !minuteText) return null;
  const year = Number(yearText);
  const month = Number(monthText);
  const day = Number(dayText);
  const hour = Number(hourText);
  const minute = Number(minuteText);
  const localAsUtcMs = Date.UTC(year, month - 1, day, hour, minute, 0);
  const firstOffset = offsetMinutes(localAsUtcMs, timeZone);
  let instantMs = localAsUtcMs - firstOffset * 60000;
  const secondOffset = offsetMinutes(instantMs, timeZone);
  if (secondOffset !== firstOffset) instantMs = localAsUtcMs - secondOffset * 60000;
  const resolved = localPartsInZone(instantMs, timeZone);
  if (
    resolved.year !== year ||
    resolved.month !== month ||
    resolved.day !== day ||
    resolved.hour !== hour ||
    resolved.minute !== minute
  ) {
    return null;
  }
  return `${yearText}-${monthText}-${dayText}T${hourText}:${minuteText}:00${offsetLabel(secondOffset)}`;
}

export function offsetInstantToLocalDateTime(value: unknown) {
  if (typeof value !== 'string') return undefined;
  const match = value.match(OFFSET_INSTANT_PATTERN);
  if (!match?.[1] || !match[2]) return undefined;
  return `${match[1]}T${match[2]}`;
}
