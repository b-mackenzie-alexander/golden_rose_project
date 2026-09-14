import { fireEvent, render, screen, within } from '@testing-library/react';
import { useState } from 'react';
import { describe, expect, it } from 'vitest';
import type { DraftObject } from '../api/intakeContracts';
import { AddressFields, IntakeFields } from './IntakeFields';
function Form({ kind }: { kind: 'worker' | 'employer' | 'address' }) {
  const [value, change] = useState<DraftObject>({});
  return (
    <>
      {kind === 'address' ? (
        <AddressFields value={value} change={change} />
      ) : (
        <IntakeFields kind={kind} value={value} change={change} />
      )}
      <output aria-label="Captured fictional test values">{JSON.stringify(value)}</output>
    </>
  );
}
function input(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } });
}
const captured = () => screen.getByLabelText('Captured fictional test values').textContent;
describe('typed partial fields', () => {
  it('captures worker other interests and explicit weekly availability, without guessed overnight', () => {
    render(<Form kind="worker" />);
    input('Full name', 'Fictional');
    input('Phone', '+1 555 555 0100');
    input('Other work interests', 'Fictional interest');
    input('Availability', 'weekly');
    input('IANA time zone', 'America/New_York');
    fireEvent.click(screen.getByRole('button', { name: 'Add weekly range' }));
    input('Weekday (Monday = 1, Sunday = 7)', '1');
    input('Start time', '20:00');
    input('End time', '04:00');
    input('Ends on', '1');
    input('Availability exception note', 'Fictional exception');
    expect(captured()).toContain('"end_day_offset":1');
    expect(captured()).toContain('"other_description":"Fictional interest"');
    fireEvent.click(screen.getByRole('button', { name: 'Remove range' }));
    expect(captured()).toContain('"ranges":[]');
    input('Availability', 'flexible');
    expect(captured()).not.toContain('ranges');
    input('Availability exception note', '');
    input('Other work interests', '');
    input('Phone', '');
    input('Full name', '');
    input('Availability', '');
    expect(captured()).toBe('{"interests":{}}');
  });
  it('captures partial employer demand and exact decimal offer inputs', () => {
    render(<Form kind="employer" />);
    input('Employer type', 'business');
    input('Employer name', 'Fictional Employer');
    input('Representative name', 'Fictional Representative');
    input('Number of workers', '2');
    input('Role title', 'Fictional role');
    input('Duties', 'Fictional duties');
    input('Requested schedule', 'specified');
    input('Requested start date (or use timed interval)', '2026-10-01');
    input('Start instant with UTC offset', '2026-10-01T08:00:00-04:00');
    input('End instant with UTC offset', '2026-10-01T16:00:00-04:00');
    input('Schedule IANA time zone', 'America/New_York');
    input('Schedule note', 'Fictional note');
    input('Minimum amount (decimal)', '0');
    expect(screen.getByText('Zero offer: confirm the supplied amount with staff.')).toBeInTheDocument();
    input('Minimum amount (decimal)', '12.34');
    input('Maximum amount (optional)', '15.00');
    input('Currency code (3 uppercase letters)', 'USD');
    input('Pay basis', 'hour');
    input('Offer terms', 'Fictional terms');
    fireEvent.click(screen.getByLabelText('Amount is per worker'));
    fireEvent.click(screen.getByLabelText('Negotiable'));
    expect(captured()).toContain('"minimum":"12.34"');
    expect(captured()).toContain('"worker_count":2');
    expect(captured()).toContain('"per_worker":true');
    input('Requested schedule', 'to_be_discussed');
    expect(captured()).not.toContain('starts_at');
    fireEvent.click(screen.getByLabelText('Amount is per worker'));
    fireEvent.click(screen.getByLabelText('Negotiable'));
    input('Number of workers', '');
    input('Employer type', '');
    input('Requested schedule', '');
    expect(captured()).not.toContain('per_worker');
  });
  it('offers pinned explicit country choices and partial address values', () => {
    render(<Form kind="address" />);
    input('Address line 1', 'Fictional line');
    input('Address line 2', 'Fictional unit');
    input('City / locality', 'Fictional locality');
    input('State / region', 'Fictional region');
    input('Postal code', '00000');
    const country = screen.getByLabelText('Country code (2 uppercase letters)');
    expect(within(country).getAllByRole('option')).toHaveLength(250);
    input('Country code (2 uppercase letters)', 'US');
    expect(captured()).toContain('"country":"US"');
    input('Address line 2', '');
    expect(captured()).not.toContain('line2');
  });
});
