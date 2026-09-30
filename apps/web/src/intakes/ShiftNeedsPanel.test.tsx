import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { createShiftNeed, listShiftNeeds, submitShiftNeedForReview, submitStaffingRequestForReview } from '../api/shiftNeedClient';
import type { ShiftNeed } from '../api/shiftNeedClient';
import { LanguageProvider, useLanguage } from '../i18n/LanguageProvider';
import { runAxe } from '../test/axe';
import { ShiftNeedsPanel } from './ShiftNeedsPanel';

vi.mock('../api/shiftNeedClient', () => ({
  createShiftNeed: vi.fn(),
  listShiftNeeds: vi.fn(),
  submitShiftNeedForReview: vi.fn(),
  submitStaffingRequestForReview: vi.fn(),
}));

const employerId = '11111111-1111-4111-8111-111111111111';
const requestId = '22222222-2222-4222-8222-222222222222';
const shiftNeedId = '33333333-3333-4333-8333-333333333333';
const shift: ShiftNeed = {
  shiftNeedId,
  employerId,
  staffingRequestId: requestId,
  requestVersionAtCreation: 2,
  shiftStatus: 'draft',
  roleTitle: 'Home aide',
  workerCount: 1,
  startsAt: '2026-10-01T13:00:00Z',
  endsAt: '2026-10-01T17:00:00Z',
  timeZone: 'America/New_York',
  notes: null,
  version: 1,
  createdAt: '2026-09-29T12:00:00Z',
  updatedAt: '2026-09-29T12:00:00Z',
};

beforeEach(() => {
  vi.mocked(listShiftNeeds).mockResolvedValue({ ok: true, value: [] });
  vi.mocked(createShiftNeed).mockReset();
  vi.mocked(submitShiftNeedForReview).mockReset();
  vi.mocked(submitStaffingRequestForReview).mockReset();
  vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('44444444-4444-4444-8444-444444444444');
});

afterEach(() => {
  vi.restoreAllMocks();
});

function mount() {
  return render(
    <LanguageProvider>
      <ShiftNeedsPanel employerId={employerId} requestId={requestId} requestVersion={2} requestStatus="draft" roleTitle="Home aide" workerCount={3} />
    </LanguageProvider>,
  );
}

function SpanishHarness() {
  const { toggleLanguage } = useLanguage();
  return <>
    <button type="button" onClick={toggleLanguage}>Espanol</button>
    <ShiftNeedsPanel employerId={employerId} requestId={requestId} requestVersion={2} requestStatus="draft" roleTitle="Home aide" workerCount={3} />
  </>;
}

it('creates a draft shift need with validation and no active-demand claims', async () => {
  const user = userEvent.setup();
  vi.mocked(createShiftNeed).mockResolvedValue({ ok: true, value: { commandId: '44444444-4444-4444-8444-444444444444', resultRecordVersion: 1, eventType: 'shift_need.created', current: shift } });
  mount();

  await screen.findByText('No shift needs have been created for this request.');
  expect(screen.getByText(/does not open demand, match workers, confirm coverage, or create referrals/)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Create draft shift need' })).toBeDisabled();

  await user.type(screen.getByLabelText('Start'), '2026-10-01T09:00');
  await user.type(screen.getByLabelText('End'), '2026-10-01T13:00');
  await user.type(screen.getByLabelText('Reason'), 'Employer supplied concrete schedule');
  await user.type(screen.getByLabelText('Notes'), 'Bring intake packet');
  expect(screen.getByRole('button', { name: 'Create draft shift need' })).toBeEnabled();
  await user.click(screen.getByRole('button', { name: 'Create draft shift need' }));

  expect(createShiftNeed).toHaveBeenCalledWith(expect.objectContaining({
    employerId,
    requestId,
    expectedRequestVersion: 2,
    roleTitle: 'Home aide',
    workerCount: 3,
    reasonText: 'Employer supplied concrete schedule',
    commandId: '44444444-4444-4444-8444-444444444444',
  }));
  expect(await screen.findByText('Draft shift need recorded. Request review is still required before this becomes active demand.')).toBeInTheDocument();
  expect(screen.getByText('1 workers')).toBeInTheDocument();
});

it('shows stale conflicts as recoverable refresh guidance', async () => {
  const user = userEvent.setup();
  vi.mocked(createShiftNeed).mockResolvedValue({ ok: false, failure: { kind: 'stale' } });
  mount();
  await screen.findByText('No shift needs have been created for this request.');

  await user.clear(screen.getByLabelText('Workers needed'));
  await user.type(screen.getByLabelText('Workers needed'), '2');
  await user.type(screen.getByLabelText('Start'), '2026-10-01T09:00');
  await user.type(screen.getByLabelText('End'), '2026-10-01T13:00');
  await user.type(screen.getByLabelText('Reason'), 'Employer supplied concrete schedule');
  await user.click(screen.getByRole('button', { name: 'Create draft shift need' }));

  expect(await screen.findByText('The request changed before the shift was saved. Refresh current facts and try again.')).toBeInTheDocument();
});

it('lists existing shift needs with notes and handles refresh errors', async () => {
  const user = userEvent.setup();
  vi.mocked(listShiftNeeds)
    .mockResolvedValueOnce({ ok: true, value: [{ ...shift, notes: 'Bring intake packet' }] })
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'forbidden' } });
  mount();

  expect((await screen.findAllByText('Home aide')).length).toBeGreaterThan(0);
  expect(screen.getAllByText('Bring intake packet').length).toBeGreaterThan(0);

  await user.click(screen.getByRole('button', { name: 'Refresh shift needs' }));

  expect(await screen.findByText('You do not have permission to manage shift needs for this request.')).toBeInTheDocument();
});

it('recovers from initial list failures and refreshes into a populated list', async () => {
  const user = userEvent.setup();
  vi.mocked(listShiftNeeds)
    .mockResolvedValueOnce({ ok: false, failure: { kind: 'unavailable' } })
    .mockResolvedValueOnce({ ok: true, value: [{ ...shift, notes: 'Bring intake packet' }] });
  mount();

  expect(await screen.findByText('Shift needs are unavailable. Try again.')).toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Refresh shift needs' }));

  expect(await screen.findByText('Bring intake packet')).toBeInTheDocument();
});

it('submits a draft shift then submits the request for review without active-demand claims', async () => {
  const user = userEvent.setup();
  const onRequestReviewSubmitted = vi.fn();
  vi.mocked(listShiftNeeds).mockResolvedValue({ ok: true, value: [shift] });
  vi.mocked(submitShiftNeedForReview).mockResolvedValue({
    ok: true,
    value: {
      commandId: '44444444-4444-4444-8444-444444444444',
      resultRecordVersion: 2,
      eventType: 'shift_need.submitted_for_review',
      current: { ...shift, shiftStatus: 'pending_review', version: 2, updatedAt: '2026-09-29T12:05:00Z' },
    },
  });
  vi.mocked(submitStaffingRequestForReview).mockResolvedValue({
    ok: true,
    value: {
      commandId: '44444444-4444-4444-8444-444444444444',
      resultRecordVersion: 3,
      eventType: 'staffing_request.submitted_for_review',
      current: { staffingRequestId: requestId, employerId, version: 3, requestStatus: 'pending_review' },
    },
  });

  render(
    <LanguageProvider>
      <ShiftNeedsPanel employerId={employerId} requestId={requestId} requestVersion={2} requestStatus="draft" roleTitle="Home aide" workerCount={3} onRequestReviewSubmitted={onRequestReviewSubmitted} />
    </LanguageProvider>,
  );

  expect(await screen.findByRole('button', { name: 'Submit shift for review' })).toBeEnabled();
  expect(screen.getByRole('button', { name: 'Submit request for review' })).toBeDisabled();
  await user.click(screen.getByRole('button', { name: 'Submit shift for review' }));

  expect(submitShiftNeedForReview).toHaveBeenCalledWith(expect.objectContaining({
    employerId,
    requestId,
    shiftNeedId,
    expectedVersion: 1,
  }));
  expect(await screen.findByText('Shift need submitted for staff review evidence. It is not active demand yet.')).toBeInTheDocument();
  expect(screen.getByText('Pending review')).toBeInTheDocument();

  await user.click(screen.getByRole('button', { name: 'Submit request for review' }));
  expect(submitStaffingRequestForReview).toHaveBeenCalledWith(expect.objectContaining({
    employerId,
    requestId,
    expectedVersion: 2,
  }));
  expect(await screen.findByText('Staffing request submitted for review evidence. Demand remains inactive until a later authorized workflow opens it.')).toBeInTheDocument();
  expect(onRequestReviewSubmitted).toHaveBeenCalledTimes(1);
});

it('keeps lifecycle failures recoverable and leaves pending requests inactive', async () => {
  const user = userEvent.setup();
  vi.mocked(listShiftNeeds).mockResolvedValue({ ok: true, value: [{ ...shift, shiftStatus: 'pending_review', version: 2 }] });
  vi.mocked(submitStaffingRequestForReview).mockResolvedValueOnce({ ok: false, failure: { kind: 'validation' } });

  const first = render(
    <LanguageProvider>
      <ShiftNeedsPanel employerId={employerId} requestId={requestId} requestVersion={2} requestStatus="draft" roleTitle="Home aide" workerCount={3} />
    </LanguageProvider>,
  );

  await screen.findByText('Pending review');
  await user.click(screen.getByRole('button', { name: 'Submit request for review' }));

  expect(await screen.findByText('Review the shift details and try again.')).toBeInTheDocument();
  expect(submitStaffingRequestForReview).toHaveBeenCalledTimes(1);
  first.unmount();

  vi.mocked(listShiftNeeds).mockResolvedValueOnce({ ok: true, value: [{ ...shift, shiftStatus: 'pending_review', version: 2 }] });
  render(
    <LanguageProvider>
      <ShiftNeedsPanel employerId={employerId} requestId={requestId} requestVersion={3} requestStatus="pending_review" roleTitle="Home aide" workerCount={3} />
    </LanguageProvider>,
  );

  expect(await screen.findByText('Pending review')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Submit request for review' })).toBeDisabled();
});

it('shows shift submit failures as recoverable guidance', async () => {
  const user = userEvent.setup();
  vi.mocked(listShiftNeeds).mockResolvedValue({ ok: true, value: [shift] });
  vi.mocked(submitShiftNeedForReview).mockResolvedValue({ ok: false, failure: { kind: 'stale' } });
  mount();

  await user.click(await screen.findByRole('button', { name: 'Submit shift for review' }));

  expect(await screen.findByText('The request changed before the shift was saved. Refresh current facts and try again.')).toBeInTheDocument();
  expect(submitShiftNeedForReview).toHaveBeenCalledTimes(1);
});

it('shows field-local validation for impossible draft shift details', async () => {
  const user = userEvent.setup();
  mount();
  await screen.findByText('No shift needs have been created for this request.');

  await user.clear(screen.getByLabelText('Role title'));
  await user.clear(screen.getByLabelText('Workers needed'));
  await user.type(screen.getByLabelText('Workers needed'), '4');
  await user.type(screen.getByLabelText('Start'), '2026-10-01T13:00');
  await user.type(screen.getByLabelText('End'), '2026-10-01T09:00');
  await user.clear(screen.getByLabelText('Time zone'));

  expect(screen.getAllByText('This field is required.').length).toBeGreaterThanOrEqual(2);
  expect(screen.getByText('Enter a whole number between 1 and the request worker count.')).toBeInTheDocument();
  expect(screen.getByText('End time must be after start time.')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Create draft shift need' })).toBeDisabled();
});

it('renders Spanish copy and remains accessible', async () => {
  const user = userEvent.setup();
  const view = render(<LanguageProvider><SpanishHarness /></LanguageProvider>);
  await screen.findByText('No shift needs have been created for this request.');

  await user.click(screen.getByRole('button', { name: 'Espanol' }));

  expect(screen.getByRole('heading', { name: 'Turnos en borrador' })).toBeInTheDocument();
  expect(screen.getByText(/no empareja trabajadores/)).toBeInTheDocument();
  expect(await runAxe(view.container)).toEqual([]);
});
