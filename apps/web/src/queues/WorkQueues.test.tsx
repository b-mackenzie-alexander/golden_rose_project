import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as intakeApi from '../api/intakeClient';
import type { IntakeKind, IntakeSummary } from '../api/intakeContracts';
import * as operationsApi from '../api/operationsProjectionClient';
import * as runtimeApi from '../api/runtimeEnvironmentClient';
import { LanguageProvider, useLanguage } from '../i18n/LanguageProvider';
import { WorkQueues } from './WorkQueues';

vi.mock('../api/intakeClient');
vi.mock('../api/operationsProjectionClient');
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

function TestLanguageToggle() {
  const { toggleLanguage } = useLanguage();
  return <button type="button" onClick={toggleLanguage}>Cambiar a español</button>;
}

function renderQueues() {
  return render(
    <LanguageProvider>
      <TestLanguageToggle />
      <MemoryRouter initialEntries={['/staff/queues']}>
        <WorkQueues />
      </MemoryRouter>
    </LanguageProvider>,
  );
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

describe('WorkQueues', () => {
  beforeEach(() => {
    vi.mocked(intakeApi.queryIntakes).mockImplementation((kind) => Promise.resolve({
      ok: true,
      value: {
        items: kind === 'worker'
          ? [
              summary('worker', '11111111-1111-4111-8111-111111111111', 'Worker Follow Up', {
                complete: false,
                missing_fields: ['worker_residence'],
              }),
            ]
          : [],
        next_cursor: null,
      },
    }));
    vi.mocked(operationsApi.getOperationsProjection).mockResolvedValue({
      ok: true,
      value: {
        requestItems: [
          {
            itemType: 'staffing_request',
            sourceIntakeId: '22222222-2222-4222-8222-222222222222',
            employerId: '33333333-3333-4333-8333-333333333333',
            employerName: 'Projected Employer',
            staffingRequestId: '44444444-4444-4444-8444-444444444444',
            requestStatus: 'draft',
            roleTitle: 'Home aide',
            workerCount: 2,
            version: 1,
            receivedAt: '2026-10-01T13:00:00Z',
            updatedAt: '2026-10-01T13:30:00Z',
          },
        ],
        shiftItems: [
          {
            itemType: 'shift_need',
            sourceIntakeId: '22222222-2222-4222-8222-222222222222',
            employerId: '33333333-3333-4333-8333-333333333333',
            employerName: 'Projected Employer',
            staffingRequestId: '44444444-4444-4444-8444-444444444444',
            shiftNeedId: '55555555-5555-4555-8555-555555555555',
            requestStatus: 'draft',
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
  });

  it('lists projected request and shift work ahead of intake fallback rows', async () => {
    renderQueues();

    await screen.findByText('Shift pending review');
    expect(screen.getByText(/Request and shift queue: 2 open item/)).toBeInTheDocument();
    expect(screen.getByText(/This does not assign workers or confirm coverage/)).toBeInTheDocument();
    expect(screen.getAllByText(/Projected Employer/).length).toBeGreaterThan(0);
    expect(screen.getByText('Prepare staffing request')).toBeInTheDocument();
    expect(screen.getByText('Required intake fields are still missing')).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'Open' }).some((link) => (
      link.getAttribute('href') === '/staff/intakes/22222222-2222-4222-8222-222222222222/outputs/request'
    ))).toBe(true);
  });

  it('filters projected urgent and employer rows in Spanish', async () => {
    const user = userEvent.setup();
    renderQueues();
    await screen.findByText('Shift pending review');
    await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));

    await screen.findByText('Turno pendiente de revision');
    await user.click(screen.getByRole('button', { name: 'Urgente' }));
    expect(screen.getByText('Turno pendiente de revision')).toBeInTheDocument();
    expect(screen.queryByText('Preparar solicitud de personal')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Seguimientos de empleadores' }));
    const projectedRows = screen.getAllByText(/Projected Employer/);
    expect(projectedRows.length).toBeGreaterThan(0);
    const row = projectedRows[0]?.closest('article');
    if (!row) throw new Error('Projected employer row was not rendered.');
    expect(within(row).getByRole('link', { name: 'Abrir' })).toHaveAttribute(
      'href',
      '/staff/intakes/22222222-2222-4222-8222-222222222222/outputs/request',
    );
  });

  it('falls back to static rows when projection and intake reads fail', async () => {
    vi.mocked(intakeApi.queryIntakes).mockResolvedValue({ ok: false, failure: 'failed' });
    vi.mocked(operationsApi.getOperationsProjection).mockRejectedValue(new TypeError('offline'));

    renderQueues();

    await waitFor(() => {
      expect(screen.getByText('Urgent intake review')).toBeInTheDocument();
    });
    expect(screen.getByRole('status')).toHaveTextContent('projection service is unavailable');
    expect(screen.getByText('Review employer drafts')).toBeInTheDocument();
    expect(screen.queryByText('Restaurante La Esperanza')).not.toBeInTheDocument();
  });

  it('does not show static queue rows in production mode when projection and intake reads fail', async () => {
    vi.mocked(intakeApi.queryIntakes).mockResolvedValue({ ok: false, failure: 'failed' });
    vi.mocked(operationsApi.getOperationsProjection).mockRejectedValue(new TypeError('offline'));
    vi.mocked(runtimeApi.getStaticOperationalFallbackPolicy).mockResolvedValue('deny');

    renderQueues();

    await waitFor(() => {
      expect(screen.getByText('No queue items match this view.')).toBeInTheDocument();
    });
    expect(screen.getByRole('status')).toHaveTextContent('static examples are disabled');
    expect(screen.queryByText('Urgent intake review')).not.toBeInTheDocument();
    expect(screen.queryByText('Employer follow-up')).not.toBeInTheDocument();
    expect(screen.getByText('Open queue items')).toBeInTheDocument();
  });

  it('keeps a successful empty projection visibly empty instead of showing fallback queue rows', async () => {
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

    renderQueues();

    await waitFor(() => {
      expect(screen.getByText('No queue items match this view.')).toBeInTheDocument();
    });
    expect(screen.getByText(/Request and shift queue: 0 open item/)).toBeInTheDocument();
    expect(screen.queryByText('Urgent intake review')).not.toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });

  it('uses employer fallback links and draft labels when operations have no source intake', async () => {
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
            employerId: '33333333-3333-4333-8333-333333333333',
            employerName: 'Fallback Employer',
            staffingRequestId: '44444444-4444-4444-8444-444444444444',
            requestStatus: 'pending_review',
            roleTitle: 'Cleaner',
            workerCount: 3,
            version: 1,
            receivedAt: '2026-10-01T13:00:00Z',
            updatedAt: '2026-10-01T13:30:00Z',
          },
        ],
        shiftItems: [
          {
            itemType: 'shift_need',
            sourceIntakeId: null,
            employerId: '33333333-3333-4333-8333-333333333333',
            employerName: 'Fallback Employer',
            staffingRequestId: '44444444-4444-4444-8444-444444444444',
            shiftNeedId: '55555555-5555-4555-8555-555555555555',
            requestStatus: 'draft',
            shiftStatus: 'draft',
            roleTitle: 'Cleaner',
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

    renderQueues();

    await screen.findByText('Draft shift need');
    expect(screen.getByText('Request in review')).toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'Open' }).filter((link) => (
      link.getAttribute('href') === '/staff/intakes/employers?reference=33333333-3333-4333-8333-333333333333&open=match'
    ))).toHaveLength(2);
  });

  it('summarizes follow-up and current intake queue branches', async () => {
    vi.mocked(intakeApi.queryIntakes).mockImplementation((kind) => Promise.resolve({
      ok: true,
      value: {
        items: kind === 'worker'
          ? [
              summary('worker', '11111111-1111-4111-8111-111111111111', 'Overdue Worker', {
                follow_up: {
                  owner_staff_id: 'staff-1',
                  next_follow_up_at: '2026-10-02T15:00:00Z',
                  overdue: true,
                },
                review_status: 'needs_follow_up',
              }),
              summary('worker', '22222222-2222-4222-8222-222222222222', 'Current Worker', {
                review_status: 'current',
              }),
              summary('worker', '33333333-3333-4333-8333-333333333333', 'Stale Worker', {
                review_status: 'stale',
              }),
            ]
          : [
              summary('employer', '44444444-4444-4444-8444-444444444444', 'Follow Up Employer', {
                follow_up: {
                  owner_staff_id: 'staff-2',
                  next_follow_up_at: '2026-10-03T16:00:00Z',
                  overdue: false,
                },
                review_status: 'needs_follow_up',
              }),
              summary('employer', '55555555-5555-4555-8555-555555555555', 'Reviewed Employer', {
                review_status: 'current',
              }),
            ],
        next_cursor: null,
      },
    }));
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

    renderQueues();

    await screen.findByText('Overdue Worker - 11111111-1111-4111-8111-111111111111');
    expect(screen.getByText('Follow-up is overdue')).toBeInTheDocument();
    expect(screen.getAllByText('Follow-up is the recorded next step').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Worker draft is waiting for review').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Open intake').length).toBeGreaterThan(0);
  });
});
