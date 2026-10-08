import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, vi } from 'vitest';

import * as operationsApi from '../api/operationsProjectionClient';
import * as runtimeApi from '../api/runtimeEnvironmentClient';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { StaffCalendar } from './StaffCalendar';

vi.mock('../api/operationsProjectionClient');
vi.mock('../api/runtimeEnvironmentClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/runtimeEnvironmentClient')>();
  return { ...actual, getStaticOperationalFallbackPolicy: vi.fn() };
});

function renderCalendar() {
  return render(
    <LanguageProvider>
      <StaffCalendar />
    </LanguageProvider>,
  );
}

function getDayButton(day: string, date: string, count: string) {
  const button = screen.getAllByRole('button').find((candidate) => {
    const text = candidate.textContent;
    return text.includes(day) && text.includes(date) && text.includes(count);
  });
  if (!button) throw new Error(`Day button was not rendered for ${day} ${date}.`);
  return button;
}

const projectionExtras = {
  areaSummary: [
    { areaKey: 'bronx' as const, areaLabel: 'Bronx' as const, requestCount: 0, shiftCount: 0, workerSlots: 0, pendingReviewCount: 0 },
    { areaKey: 'brooklyn' as const, areaLabel: 'Brooklyn' as const, requestCount: 1, shiftCount: 1, workerSlots: 2, pendingReviewCount: 2 },
    { areaKey: 'manhattan' as const, areaLabel: 'Manhattan' as const, requestCount: 0, shiftCount: 0, workerSlots: 0, pendingReviewCount: 0 },
    { areaKey: 'queens' as const, areaLabel: 'Queens' as const, requestCount: 0, shiftCount: 0, workerSlots: 0, pendingReviewCount: 0 },
    { areaKey: 'staten_island' as const, areaLabel: 'Staten Island' as const, requestCount: 0, shiftCount: 0, workerSlots: 0, pendingReviewCount: 0 },
  ],
  reportSummary: {
    requestCount: 1,
    shiftCount: 1,
    workerSlots: 2,
    pendingReviewCount: 2,
    activeAreaCount: 1,
    unmappedRequestCount: 0,
  },
  calendarSummary: {
    projectedShiftCount: 1,
    workerSlots: 1,
    pendingReviewShiftCount: 1,
    coverageDayCount: 1,
    firstShiftStartsAt: '2026-09-29T14:00:00Z',
    lastShiftEndsAt: '2026-09-29T18:00:00Z',
  },
  queueSummary: {
    openItemCount: 2,
    draftCount: 1,
    pendingReviewCount: 1,
    highPriorityCount: 1,
    oldestItemUpdatedAt: '2026-09-29T13:30:00Z',
    newestItemUpdatedAt: '2026-09-29T13:45:00Z',
  },
};

function calendarDate(offsetDays: number) {
  const today = new Date();
  const date = new Date(today.getFullYear(), today.getMonth(), today.getDate() + offsetDays, 10, 0, 0, 0);
  return {
    dateLabel: new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(date),
    dayLabel: new Intl.DateTimeFormat('en-US', { weekday: 'short' }).format(date),
    iso: date.toISOString(),
  };
}

function currentMonthHeading() {
  return new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(new Date());
}

function firstPopulatedCalendarDay() {
  const button = screen.getAllByRole('button').find((candidate) => (
    candidate.classList.contains('calendar-day-button') &&
    !candidate.textContent.endsWith('0')
  ));
  if (!button) throw new Error('No populated calendar day was rendered.');
  return button;
}

describe('StaffCalendar', () => {
  beforeEach(() => {
    const projectedShiftDay = calendarDate(1);
    window.localStorage.clear();
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue({
      ok: true,
      value: {
        requestItems: [],
        shiftItems: [
          {
            itemType: 'shift_need',
            sourceIntakeId: '66666666-6666-4666-8666-666666666666',
            employerId: '77777777-7777-4777-8777-777777777777',
            employerName: 'Projected Employer',
            staffingRequestId: '88888888-8888-4888-8888-888888888888',
            shiftNeedId: '99999999-9999-4999-8999-999999999999',
            requestStatus: 'pending_review',
            shiftStatus: 'pending_review',
            roleTitle: 'Home aide',
            workerCount: 1,
            startsAt: projectedShiftDay.iso,
            endsAt: new Date(new Date(projectedShiftDay.iso).getTime() + 4 * 60 * 60 * 1000).toISOString(),
            timeZone: 'America/New_York',
            version: 2,
            updatedAt: '2026-09-29T13:45:00Z',
          },
        ],
        ...projectionExtras,
      },
    });
    vi.mocked(runtimeApi.getStaticOperationalFallbackPolicy).mockResolvedValue('allow');
  });

  it('starts with the current day and can switch to the current-year month view', async () => {
    const user = userEvent.setup();
    const today = calendarDate(0);
    const monthEnd = new Date();
    monthEnd.setMonth(monthEnd.getMonth() + 1, 0);

    renderCalendar();

    await waitFor(() => {
      expect(getDayButton(today.dayLabel, today.dateLabel, '0')).toBeInTheDocument();
    });
    expect(screen.queryByText('Jan 27')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Month' }));

    expect(screen.getAllByText(currentMonthHeading()).length).toBeGreaterThanOrEqual(1);
    const monthButtons = screen.getAllByRole('button').filter((button) => (
      button.classList.contains('calendar-day-button')
    ));
    expect(monthButtons.length).toBe(monthEnd.getDate());
    expect(monthButtons.some((button) => button.textContent.includes(String(monthEnd.getDate())))).toBe(true);
  });

  it('adds and removes a personal calendar event from the selected day', async () => {
    const projectedShiftDay = calendarDate(1);
    const user = userEvent.setup();
    let view = renderCalendar();
    await waitFor(() => {
      expect(getDayButton(projectedShiftDay.dayLabel, projectedShiftDay.dateLabel, '1')).toBeInTheDocument();
    });
    expect(screen.getByText('Projected shifts')).toBeInTheDocument();
    expect(screen.getByText('Projected worker slots')).toBeInTheDocument();
    expect(screen.getByText('Request-derived shifts only; personal events stay separate.')).toBeInTheDocument();
    await user.click(getDayButton(projectedShiftDay.dayLabel, projectedShiftDay.dateLabel, '1'));
    const form = screen.getByRole('heading', { name: 'Add event' }).closest('form');
    if (!form) throw new Error('Add event form was not rendered.');
    const eventForm = within(form);

    await user.type(eventForm.getByLabelText('Title'), 'Prepare demo script');
    await user.clear(eventForm.getByLabelText('Time'));
    await user.type(eventForm.getByLabelText('Time'), '15:15');
    await user.selectOptions(eventForm.getByLabelText('Duration'), '60 min');
    await user.selectOptions(eventForm.getByLabelText('Calendar'), 'personal');
    await user.type(eventForm.getByLabelText('Assigned to'), 'Mariela Torres');
    await user.type(eventForm.getByLabelText('Details'), 'Stakeholder presentation prep');
    await user.click(eventForm.getByRole('button', { name: 'Save event' }));

    expect(screen.getAllByText('Prepare demo script')).toHaveLength(2);
    expect(screen.getAllByText('Stakeholder presentation prep').length).toBeGreaterThanOrEqual(1);
    expect(getDayButton(projectedShiftDay.dayLabel, projectedShiftDay.dateLabel, '2')).toBeInTheDocument();

    view.unmount();
    view = renderCalendar();
    await waitFor(() => {
      expect(getDayButton(projectedShiftDay.dayLabel, projectedShiftDay.dateLabel, '2')).toBeInTheDocument();
    });
    await user.click(getDayButton(projectedShiftDay.dayLabel, projectedShiftDay.dateLabel, '2'));
    expect(screen.getAllByText('Prepare demo script')).toHaveLength(2);

    await user.click(screen.getByRole('button', { name: 'Edit event' }));
    const editForm = screen.getByRole('heading', { name: 'Edit event' }).closest('form');
    if (!editForm) throw new Error('Edit event form was not rendered.');
    const editableEventForm = within(editForm);
    await user.clear(editableEventForm.getByLabelText('Title'));
    await user.type(editableEventForm.getByLabelText('Title'), 'Finalize demo script');
    await user.click(editableEventForm.getByRole('button', { name: 'Update event' }));
    expect(screen.getByRole('status')).toHaveTextContent('Event updated');
    expect(screen.queryByText('Prepare demo script')).not.toBeInTheDocument();
    expect(screen.getAllByText('Finalize demo script')).toHaveLength(2);

    await user.click(screen.getByRole('button', { name: 'Remove event' }));
    expect(screen.getByRole('status')).toHaveTextContent('Event removed');
    expect(screen.queryByText('Finalize demo script')).not.toBeInTheDocument();
    expect(getDayButton(projectedShiftDay.dayLabel, projectedShiftDay.dateLabel, '1')).toBeInTheDocument();

    view.unmount();
    renderCalendar();
    await waitFor(() => {
      expect(getDayButton(projectedShiftDay.dayLabel, projectedShiftDay.dateLabel, '1')).toBeInTheDocument();
    });
    await user.click(getDayButton(projectedShiftDay.dayLabel, projectedShiftDay.dateLabel, '1'));
    expect(screen.queryByText('Finalize demo script')).not.toBeInTheDocument();
  });

  it('requires company calendar permission before removing company events', async () => {
    const user = userEvent.setup();
    renderCalendar();
    const form = screen.getByRole('heading', { name: 'Add event' }).closest('form');
    if (!form) throw new Error('Add event form was not rendered.');
    const eventForm = within(form);

    await user.type(eventForm.getByLabelText('Title'), 'Company briefing');
    await user.selectOptions(eventForm.getByLabelText('Calendar'), 'company');
    await user.click(eventForm.getByRole('button', { name: 'Save event' }));

    expect(screen.getAllByText('Company briefing')).toHaveLength(2);
    const gatedButtons = screen.getAllByRole('button', { name: 'Company calendar permission required' });
    expect(gatedButtons).toHaveLength(2);
    expect(gatedButtons.every((button) => button.hasAttribute('disabled'))).toBe(true);
  });

  it('shows fallback calendar events with a projection notice when shift reads fail', async () => {
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue({
      ok: false,
      failure: { kind: 'forbidden' },
    });

    renderCalendar();

    expect(await screen.findByRole('status')).toHaveTextContent('not authorized to read projected shifts');
    await userEvent.click(firstPopulatedCalendarDay());
    expect(screen.getAllByText(/Team check-in|Call Restaurante La Esperanza|Interview with Ana Quispe|Review pending intakes|Follow-up with Maria Lopez|Bright Horizons staffing call|Meet Carlos Mendoza|Worker intake review block|Clean Homes LLC confirmation|Interview with Carlos Mendoza/).length).toBeGreaterThan(0);
  });

  it('does not show seeded calendar events in production mode when shift reads fail', async () => {
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue({
      ok: false,
      failure: { kind: 'forbidden' },
    });
    vi.mocked(runtimeApi.getStaticOperationalFallbackPolicy).mockResolvedValue('deny');

    renderCalendar();

    expect(await screen.findByRole('status')).toHaveTextContent('static examples are disabled');
    expect(screen.getByText('Open slots')).toBeInTheDocument();
    expect(screen.queryByText('Team check-in')).not.toBeInTheDocument();
    expect(screen.queryByText('Call Restaurante La Esperanza')).not.toBeInTheDocument();
  });

  it('keeps a successful empty shift projection empty instead of showing seeded events', async () => {
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue({
      ok: true,
      value: {
        requestItems: [],
        shiftItems: [],
        areaSummary: projectionExtras.areaSummary.map((area) => ({
          ...area,
          requestCount: 0,
          shiftCount: 0,
          workerSlots: 0,
          pendingReviewCount: 0,
        })),
        reportSummary: {
          requestCount: 0,
          shiftCount: 0,
          workerSlots: 0,
          pendingReviewCount: 0,
          activeAreaCount: 0,
          unmappedRequestCount: 0,
        },
        calendarSummary: {
          projectedShiftCount: 0,
          workerSlots: 0,
          pendingReviewShiftCount: 0,
          coverageDayCount: 0,
          firstShiftStartsAt: null,
          lastShiftEndsAt: null,
        },
        queueSummary: {
          openItemCount: 0,
          draftCount: 0,
          pendingReviewCount: 0,
          highPriorityCount: 0,
          oldestItemUpdatedAt: null,
          newestItemUpdatedAt: null,
        },
      },
    });

    renderCalendar();

    await waitFor(() => {
      expect(screen.getByText('Open slots')).toBeInTheDocument();
    });
    expect(screen.getByText('Projected shifts')).toBeInTheDocument();
    expect(screen.getByText('Projected worker slots')).toBeInTheDocument();
    expect(screen.getAllByText('0').length).toBeGreaterThanOrEqual(3);
    expect(screen.queryByText('Team check-in')).not.toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});
