import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
  it('keeps middle-initial edits in the middle field while last name is empty', async () => {
    const user = userEvent.setup();
    render(<Form kind="worker" />);
    await user.type(screen.getByLabelText('First name'), 'Fictional');
    await user.type(screen.getByLabelText('Middle initial'), 'quincy');
    expect(screen.getByLabelText('Middle initial')).toHaveValue('Q');
    expect(screen.getByLabelText('Last name')).toHaveValue('');
    expect(captured()).toContain('"full_name":"Fictional Q"');
    await user.clear(screen.getByLabelText('Middle initial'));
    expect(screen.getByLabelText('Middle initial')).toHaveValue('');
    expect(screen.getByLabelText('Last name')).toHaveValue('');
    await user.type(screen.getByLabelText('Last name'), 'Person');
    await user.type(screen.getByLabelText('Middle initial'), 'R');
    expect(screen.getByLabelText('Middle initial')).toHaveValue('R');
    expect(screen.getByLabelText('Last name')).toHaveValue('Person');
    expect(captured()).toContain('"full_name":"Fictional R Person"');
  });
  it('marks worker detail fields with inline errors after a failed save', () => {
    render(<IntakeFields kind="worker" value={{}} change={() => {}} showValidation />);
    expect(screen.getByTitle('Enter the worker’s first name.')).toHaveTextContent('?');
    expect(screen.getByTitle('Enter the worker’s last name.')).toHaveTextContent('?');
    expect(screen.getByRole('textbox', { name: /First name/ })).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByRole('textbox', { name: /Last name/ })).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByRole('textbox', { name: /Phone/ })).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByText('Choose at least one common agency position or enter another work interest.')).toBeInTheDocument();
    expect(screen.getByText('Choose Unknown, Flexible, or Specific days.')).toBeInTheDocument();
  });
  it('captures worker manual interests and explicit day availability, without guessed overnight', () => {
    render(<Form kind="worker" />);
    input('First name', 'Fictional');
    input('Phone', '+1 555 555 0100');
    input('Other work interest 1', 'Cooking');
    input('Other work interest 2', 'Lawncare');
    input('Availability', 'weekly');
    expect(screen.getByRole('combobox', { name: 'Time zone' })).toHaveValue('America/New_York');
    fireEvent.click(screen.getByRole('button', { name: 'Add time block' }));
    input('Day', '1');
    input('Start time', '20:00');
    input('End time', '04:00');
    input('Ends on', '1');
    input('Availability exception note', 'Fictional exception');
    expect(captured()).toContain('"end_day_offset":1');
    expect(captured()).toContain('"other_description":"Cooking; Lawncare"');
    expect(captured()).toContain('"time_zone":"America/New_York"');
    input('Time zone', 'Etc/UTC');
    expect(captured()).toContain('"time_zone":"Etc/UTC"');
    fireEvent.click(screen.getByRole('button', { name: 'Remove range' }));
    expect(captured()).toContain('"ranges":[]');
    input('Availability', 'flexible');
    expect(captured()).not.toContain('ranges');
    input('Availability exception note', '');
    input('Other work interest 1', '');
    input('Other work interest 1', '');
    input('Phone', '');
    input('First name', '');
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
    expect(captured()).toContain('"requested_start_date":"2026-10-01"');
    input('Start date and time', '2026-10-01T08:00');
    input('End date and time', '2026-10-01T16:00');
    input('Schedule time zone', 'America/New_York');
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
    expect(captured()).toContain('"starts_at":"2026-10-01T08:00:00-04:00"');
    expect(captured()).toContain('"ends_at":"2026-10-01T16:00:00-04:00"');
    expect(captured()).toContain('"time_zone":"America/New_York"');
    expect(captured()).not.toContain('requested_start_date');
    input('Requested schedule', 'to_be_discussed');
    expect(captured()).not.toContain('starts_at');
    fireEvent.click(screen.getByLabelText('Amount is per worker'));
    fireEvent.click(screen.getByLabelText('Negotiable'));
    input('Number of workers', '');
    input('Employer type', '');
    input('Requested schedule', '');
    expect(captured()).not.toContain('per_worker');
  });
  it('defaults address country to the agency service country without asking staff', () => {
    render(<Form kind="address" />);
    input('Address line 1', 'Fictional line');
    input('Address line 2', 'Fictional unit');
    input('City / locality', 'Fictional locality');
    input('State / region', 'new york');
    input('Postal code', '100011234');
    expect(captured()).toContain('"country":"US"');
    expect(captured()).toContain('"region":"NY"');
    expect(captured()).toContain('"postal_code":"10001-1234"');
    expect(screen.queryByLabelText('Country code (2 uppercase letters)')).not.toBeInTheDocument();
    input('Address line 2', '');
    expect(captured()).not.toContain('line2');
  });
});
