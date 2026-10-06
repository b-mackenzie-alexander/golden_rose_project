import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as intakeApi from '../api/intakeClient';
import type { IntakeKind, IntakeSummary } from '../api/intakeContracts';
import * as operationsApi from '../api/operationsProjectionClient';
import * as runtimeApi from '../api/runtimeEnvironmentClient';
import * as staffAccountApi from '../api/staffAccountClient';
import { AppRoutes } from '../app/App';
import { dashboardGreeting } from './dashboardGreeting';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { runAxe } from '../test/axe';

vi.mock('../api/intakeClient');
vi.mock('../api/operationsProjectionClient');
vi.mock('../api/staffAccountClient');
vi.mock('../api/runtimeEnvironmentClient', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api/runtimeEnvironmentClient')>();
  return { ...actual, getStaticOperationalFallbackPolicy: vi.fn() };
});

const summary = (
  kind: IntakeKind,
  intake_id: string,
  display_name: string,
  overrides: Partial<IntakeSummary> = {},
): IntakeSummary => ({
  intake_id,
  kind,
  version: 1,
  lifecycle: 'draft',
  display_name,
  complete: true,
  missing_fields: [],
  review_status: 'unreviewed',
  updated_at: new Date().toISOString(),
  ...overrides,
});

const workerSummaries = [
  summary('worker', '11111111-1111-4111-8111-111111111111', 'Dynamic Worker One', {
    complete: false,
    missing_fields: ['worker_residence'],
  }),
  summary('worker', '22222222-2222-4222-8222-222222222222', 'Dynamic Availability Worker', {
    complete: false,
    missing_fields: ['availability'],
  }),
  summary('worker', '33333333-3333-4333-8333-333333333333', 'Dynamic Reviewed Worker', {
    review_status: 'current',
  }),
];

const employerSummaries = [
  summary('employer', '44444444-4444-4444-8444-444444444444', 'Dynamic Employer One', {
    complete: false,
    missing_fields: ['worksite_address'],
  }),
  summary('employer', '55555555-5555-4555-8555-555555555555', 'Dynamic Reviewed Employer', {
    review_status: 'current',
  }),
];

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
    workerSlots: 2,
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

describe('Dashboard', () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
    vi.mocked(intakeApi.queryIntakes).mockImplementation((kind) => Promise.resolve({
      ok: true,
      value: {
        items: kind === 'worker' ? workerSummaries : employerSummaries,
        next_cursor: null,
      },
    }));
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue({
      ok: true,
      value: {
        requestItems: [
          {
            itemType: 'staffing_request',
            sourceIntakeId: '66666666-6666-4666-8666-666666666666',
            employerId: '77777777-7777-4777-8777-777777777777',
            employerName: 'Projected Employer',
            staffingRequestId: '88888888-8888-4888-8888-888888888888',
            requestStatus: 'pending_review',
            roleTitle: 'Home aide',
            workerCount: 2,
            version: 3,
            receivedAt: '2026-10-01T13:00:00Z',
            updatedAt: '2026-10-01T13:30:00Z',
          },
        ],
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
            startsAt: '2026-10-01T14:00:00Z',
            endsAt: '2026-10-01T18:00:00Z',
            timeZone: 'America/New_York',
            version: 2,
            updatedAt: '2026-10-01T13:45:00Z',
          },
        ],
        ...projectionExtras,
      },
    });
    vi.mocked(runtimeApi.getStaticOperationalFallbackPolicy).mockResolvedValue('allow');
    vi.mocked(staffAccountApi.getStaffSession).mockResolvedValue({
      ok: true,
      value: {
        actorId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
        roleName: 'owner',
        permissionNames: ['staff_account:read'],
        authContext: 'staff_oidc',
        account: {
          staffId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
          providerSubject: 'oidc:staff:owner',
          displayName: 'Beatrice Santos',
          roleName: 'owner',
          lifecycleStatus: 'active',
          mfaEnrolled: true,
          createdAt: '2026-10-06T12:00:00Z',
          createdBy: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
          updatedAt: '2026-10-06T12:00:00Z',
          updatedBy: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
          version: 1,
        },
        delegations: [],
      },
    });
  });

  it('formats dashboard greetings from the active account and local time of day', () => {
    expect(dashboardGreeting('Beatrice Santos', 'en', new Date('2026-10-06T11:59:00-04:00'))).toBe('Good morning, Beatrice Santos');
    expect(dashboardGreeting('Beatrice Santos', 'en', new Date('2026-10-06T12:00:00-04:00'))).toBe('Good afternoon, Beatrice Santos');
    expect(dashboardGreeting('Beatrice Santos', 'en', new Date('2026-10-06T16:59:00-04:00'))).toBe('Good afternoon, Beatrice Santos');
    expect(dashboardGreeting('Beatrice Santos', 'en', new Date('2026-10-06T17:00:00-04:00'))).toBe('Good evening, Beatrice Santos');
    expect(dashboardGreeting('Beatrice Santos', 'es', new Date('2026-10-06T17:00:00-04:00'))).toBe('Buenas noches, Beatrice Santos');
  });

  it('renders the staff workspace dashboard from the home route', async () => {
    const view = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole('heading', { name: 'Nuestro Corazón Dorado' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute('aria-current', 'page');
    expect(await screen.findByRole('heading', { name: /Beatrice Santos/ })).toBeInTheDocument();
    await screen.findAllByText('Dynamic Worker One');
    await screen.findAllByText('Projected Employer');
    expect(screen.getAllByRole('link').some((link) => (
      link.getAttribute('href') === '/staff/intakes/66666666-6666-4666-8666-666666666666/outputs/request' &&
      link.textContent.includes('Shift in review')
    ))).toBe(true);
    expect(screen.getAllByRole('link', { name: /Dynamic Worker One/ }).some((link) => (
      link.getAttribute('href') === '/staff/intakes/workers?reference=11111111-1111-4111-8111-111111111111&open=match'
    ))).toBe(true);
    expect(screen.getAllByRole('link', { name: /Dynamic Employer One/ }).some((link) => (
      link.getAttribute('href') === '/staff/intakes/employers?reference=44444444-4444-4444-8444-444444444444&open=match'
    ))).toBe(true);
    expect(screen.getAllByRole('link').some((link) => {
      const text = link.textContent;
      return link.getAttribute('href') === '/staff/intakes/workers?queue=review' && text.includes('2') && text.includes('Worker intakes');
    })).toBe(true);
    expect(screen.getByRole('heading', { name: "Today's priorities" })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: "Today's schedule" })).toBeInTheDocument();
    expect(screen.getAllByText('Home aide (1)').length).toBeGreaterThan(0);
    expect(screen.getByRole('heading', { name: 'Quick actions' })).toBeInTheDocument();
    expect(view.container.querySelector('.brand-rose')).toBeInTheDocument();
    expect(view.container.querySelector('.skyline-artwork')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'La comunidad nos mueve' })).toHaveClass('mission-statement-mark');
    expect(view.container.querySelector('.zone-map-artwork')).toBeInTheDocument();
    expect(view.container.querySelectorAll('.zone-map-artwork__borough')).toHaveLength(5);
    expect(view.container.querySelector('.zone-map-artwork')?.textContent).toContain('Brooklyn2');
    expect(view.container.querySelector('.zone-map-artwork')?.textContent).toContain('Manhattan0');
    expect(await runAxe(view.container)).toEqual([]);
  });

  it('switches dashboard shell and cards into Spanish', async () => {
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));

    expect(document.documentElement.lang).toBe('es');
    expect(screen.getByRole('heading', { name: 'Nuestro Corazón Dorado' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Inicio' })).toHaveAttribute('aria-current', 'page');
    expect(await screen.findByRole('heading', { name: /Beatrice Santos/ })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Prioridades de hoy' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Agenda de hoy' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Acciones rapidas' })).toBeInTheDocument();
  });

  it('renders operations-only dashboard projections in Spanish with employer fallback links', async () => {
    const user = userEvent.setup();
    vi.mocked(intakeApi.queryIntakes).mockResolvedValue({
      ok: true,
      value: { items: [], next_cursor: null },
    });
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue({
      ok: true,
      value: {
        requestItems: [
          {
            itemType: 'staffing_request',
            sourceIntakeId: null,
            employerId: '77777777-7777-4777-8777-777777777777',
            employerName: 'Projected Employer',
            staffingRequestId: '88888888-8888-4888-8888-888888888888',
            requestStatus: 'draft',
            roleTitle: 'Home aide',
            workerCount: 2,
            version: 3,
            receivedAt: '2026-10-01T13:00:00Z',
            updatedAt: '2026-10-01T13:30:00Z',
          },
        ],
        shiftItems: [
          {
            itemType: 'shift_need',
            sourceIntakeId: null,
            employerId: '77777777-7777-4777-8777-777777777777',
            employerName: 'Projected Employer',
            staffingRequestId: '88888888-8888-4888-8888-888888888888',
            shiftNeedId: '99999999-9999-4999-8999-999999999999',
            requestStatus: 'draft',
            shiftStatus: 'draft',
            roleTitle: 'Home aide',
            workerCount: 1,
            startsAt: '2026-10-01T14:00:00Z',
            endsAt: '2026-10-01T18:00:00Z',
            timeZone: 'America/New_York',
            version: 2,
            updatedAt: '2026-10-01T13:45:00Z',
          },
        ],
        ...projectionExtras,
      },
    });
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));

    expect(await screen.findByText('Turno en borrador')).toBeInTheDocument();
    expect(screen.getByText('Preparar solicitud')).toBeInTheDocument();
    expect(screen.getByText('Turnos registrados')).toBeInTheDocument();
    expect(screen.getAllByRole('link').filter((link) => (
      link.getAttribute('href') === '/staff/intakes/employers?reference=77777777-7777-4777-8777-777777777777&open=match'
    )).length).toBeGreaterThanOrEqual(2);
  });

  it('keeps dashboard fallbacks when projection loading rejects', async () => {
    vi.mocked(intakeApi.queryIntakes).mockRejectedValue(new TypeError('offline'));
    vi.mocked(operationsApi.getOperationsProjection).mockRejectedValue(new TypeError('offline'));
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByText('Ana Quispe').length).toBeGreaterThan(0);
    });
    expect(screen.getByRole('status')).toHaveTextContent('projection service is unavailable');
    expect(screen.getByText('Review new drafts')).toBeInTheDocument();
  });

  it('removes static dashboard fallbacks in production mode when reads fail', async () => {
    vi.mocked(intakeApi.queryIntakes).mockRejectedValue(new TypeError('offline'));
    vi.mocked(operationsApi.getOperationsProjection).mockRejectedValue(new TypeError('offline'));
    vi.mocked(runtimeApi.getStaticOperationalFallbackPolicy).mockResolvedValue('deny');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(await screen.findByText('No request, shift, or intake work is waiting in the projection.')).toBeInTheDocument();
    expect(screen.getByText('No projected shifts are scheduled for this view.')).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('static examples are disabled');
    expect(screen.getByText('No recent activity read is available.')).toBeInTheDocument();
    expect(screen.queryByText('Ana Quispe')).not.toBeInTheDocument();
    expect(screen.queryByText('Review new drafts')).not.toBeInTheDocument();
    expect(screen.queryByText('Team check-in')).not.toBeInTheDocument();
  });

  it('renders empty operational projection states without fallback queue or schedule rows', async () => {
    vi.mocked(intakeApi.queryIntakes).mockResolvedValue({
      ok: true,
      value: { items: [], next_cursor: null },
    });
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

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(await screen.findByText('No request, shift, or intake work is waiting in the projection.')).toBeInTheDocument();
    expect(screen.getByText('No projected shifts are scheduled for this view.')).toBeInTheDocument();
    expect(screen.queryByText('Urgent intake review')).not.toBeInTheDocument();
    expect(screen.queryByText('Team check-in')).not.toBeInTheDocument();
  });

  it('routes from the global dashboard search to reserved workflow areas', async () => {
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(within(screen.getByRole('banner')).getByRole('searchbox', { name: 'Global search' }), 'calendar');
    const calendarResult = screen.getAllByRole('button', { name: /Calendar/ }).find((button) => (
      button.textContent.includes("Today's schedule and interviews")
    ));
    if (calendarResult === undefined) {
      throw new Error('Calendar search result was not rendered.');
    }
    await user.click(calendarResult);

    expect(screen.getByRole('heading', { name: 'Calendar' })).toBeInTheDocument();
    expect(screen.getByText('January 27 - February 2, 2025')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: "Today's agenda" })).toBeInTheDocument();
  });

  it('routes from global search directly to matching employer intake data', async () => {
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(within(screen.getByRole('banner')).getByRole('searchbox', { name: 'Global search' }), 'Dynamic Employer');
    await user.click(await screen.findByRole('button', { name: /Dynamic Employer One/ }));

    await waitFor(() => {
      expect(intakeApi.queryIntakes).toHaveBeenCalledWith('employer', { name_query: 'Dynamic Employer' });
    });
    expect(screen.getByRole('heading', { name: 'Employer intakes' })).toBeInTheDocument();
    expect(screen.getByDisplayValue('44444444-4444-4444-8444-444444444444')).toBeInTheDocument();
  });

  it('routes from global search directly to an urgent work intent', async () => {
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(within(screen.getByRole('banner')).getByRole('searchbox', { name: 'Global search' }), 'urgent requests');
    const urgentShortcut = screen.getAllByRole('button', { name: /Urgent requests/ }).find((button) => (
      button.textContent.includes('Prioritized work queue')
    ));
    if (urgentShortcut === undefined) {
      throw new Error('Urgent requests shortcut was not rendered.');
    }
    await user.click(urgentShortcut);

    expect(screen.getByRole('heading', { name: 'Work queues' })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getAllByRole('link', { name: 'Open' }).some((link) => (
        link.getAttribute('href') === '/staff/intakes/66666666-6666-4666-8666-666666666666/outputs/request'
      ))).toBe(true);
    });
  });

  it('renders the staff calendar route with selectable static agenda data', async () => {
    const user = userEvent.setup();
    const view = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/staff/calendar']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole('link', { name: 'Calendar' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('heading', { name: 'Calendar' })).toBeInTheDocument();

    const thursdayButton = screen.getByText('Jan 30').closest('button');
    if (thursdayButton === null) {
      throw new Error('Thursday calendar button was not rendered.');
    }
    await user.click(thursdayButton);

    expect(await screen.findAllByText('Home aide (1)')).toHaveLength(2);
    expect(screen.getAllByText('Projected Employer').length).toBeGreaterThan(0);
    expect(await runAxe(view.container)).toEqual([]);
  });

  it('renders the work queues route with local queue filters', async () => {
    const user = userEvent.setup();
    const view = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/staff/queues']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole('link', { name: 'Work queues' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('heading', { name: 'Work queues' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Prioritized work' })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getAllByRole('link', { name: 'Open' }).some((link) => (
        link.getAttribute('href') === '/staff/intakes/66666666-6666-4666-8666-666666666666/outputs/request'
      ))).toBe(true);
    });
    expect(screen.getAllByText('Employer follow-up').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Required intake fields are still missing').length).toBeGreaterThan(0);

    await user.click(screen.getByRole('button', { name: 'Employer follow-ups' }));

    expect(screen.queryByText('Urgent intake review')).not.toBeInTheDocument();
    expect(screen.getAllByText('Employer follow-up').length).toBeGreaterThan(0);
    const employerRow = screen.getAllByText('Employer follow-up')[0]?.closest('article');
    if (!employerRow) throw new Error('Employer queue row was not rendered.');
    expect(within(employerRow).getByRole('link', { name: 'Open' })).toHaveAttribute(
      'href',
      '/staff/intakes/employers?reference=44444444-4444-4444-8444-444444444444&open=match',
    );
    expect(await runAxe(view.container)).toEqual([]);
  });

  it('renders map and reports preview routes without placeholders', async () => {
    const view = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/staff/map']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole('heading', { name: 'Activity map' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Zone snapshot' })).toBeInTheDocument();
    expect(screen.getByText(/Exact household and worksite locations remain restricted/)).toBeInTheDocument();
    expect(await screen.findByText('Projected worker slots')).toBeInTheDocument();
    expect(view.container.querySelector('.zone-map-artwork')?.textContent).toContain('Brooklyn2');
    expect(await runAxe(view.container)).toEqual([]);

    view.unmount();
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/staff/reports']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );
    expect(screen.getByRole('heading', { name: 'Reports' })).toBeInTheDocument();
    expect(await screen.findByText('Requests in projection')).toBeInTheDocument();
    expect(screen.getByText('2 pending review')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Export requires report permission' })).toBeDisabled();
  });

  it('removes static map and report metrics in production mode when projection reads fail', async () => {
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue({
      ok: false,
      failure: { kind: 'unavailable' },
    });
    vi.mocked(runtimeApi.getStaticOperationalFallbackPolicy).mockResolvedValue('deny');

    const view = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/staff/map']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(await screen.findByRole('status')).toHaveTextContent('static examples are disabled');
    const total = screen.getByText('Projected worker slots').closest('p');
    expect(total).toHaveTextContent('0 Projected worker slots');
    expect(view.container.querySelector('.zone-map-artwork')?.textContent).toContain('Brooklyn0');
    expect(view.container.querySelector('.zone-map-artwork')?.textContent).toContain('Manhattan0');

    view.unmount();
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/staff/reports']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(await screen.findByRole('status')).toHaveTextContent('static examples are disabled');
    expect(screen.getByText('Requests in projection')).toBeInTheDocument();
    expect(screen.getAllByText('Projection unavailable').length).toBeGreaterThan(0);
    expect(screen.queryByText('Worker drafts reviewed')).not.toBeInTheDocument();
    expect(screen.queryByText('Employer follow-ups')).not.toBeInTheDocument();
  });
});
