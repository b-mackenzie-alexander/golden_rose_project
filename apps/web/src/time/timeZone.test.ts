import { describe, expect, it } from 'vitest';
import { offsetInstantToLocalDateTime, zonedLocalDateTimeToOffsetInstant } from './timeZone';

describe('staff time zone conversion', () => {
  it('converts New York local form values with date-aware offsets', () => {
    expect(zonedLocalDateTimeToOffsetInstant('2026-01-15T09:30', 'America/New_York')).toBe(
      '2026-01-15T09:30:00-05:00',
    );
    expect(zonedLocalDateTimeToOffsetInstant('2026-07-15T09:30', 'America/New_York')).toBe(
      '2026-07-15T09:30:00-04:00',
    );
  });

  it('recovers local datetime inputs from offset-aware schedule instants', () => {
    expect(offsetInstantToLocalDateTime('2026-07-15T09:30:00-04:00')).toBe('2026-07-15T09:30');
    expect(offsetInstantToLocalDateTime('not-a-date')).toBeUndefined();
  });
});
