import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import * as intakeApi from '../api/intakeClient';
import type { IntakeKind, IntakeSummary } from '../api/intakeContracts';
import { AppRoutes } from '../app/App';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { runAxe } from '../test/axe';

vi.mock('../api/intakeClient');

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
    expect(screen.getByRole('heading', { name: 'Good morning, Mariela' })).toBeInTheDocument();
    await screen.findAllByText('Dynamic Worker One');
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
    expect(screen.getByRole('heading', { name: 'Quick actions' })).toBeInTheDocument();
    expect(view.container.querySelector('.brand-rose')).toBeInTheDocument();
    expect(view.container.querySelector('.skyline-artwork')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'La comunidad nos mueve' })).toHaveClass('mission-statement-mark');
    expect(view.container.querySelector('.zone-map-artwork')).toBeInTheDocument();
    expect(view.container.querySelectorAll('.zone-map-artwork__borough')).toHaveLength(5);
    expect(view.container.querySelector('.zone-map-artwork')?.textContent).toContain('Staten Island3');
    expect(view.container.querySelector('.zone-map-artwork')?.textContent).toContain('Manhattan18');
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
    expect(screen.getByRole('heading', { name: 'Buenos días, Mariela' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Prioridades de hoy' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Agenda de hoy' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Acciones rapidas' })).toBeInTheDocument();
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
    await user.click(screen.getByRole('button', { name: /Urgent requests/ }));

    expect(screen.getByRole('heading', { name: 'Work queues' })).toBeInTheDocument();
    expect(screen.getByText('Urgent intake review')).toBeInTheDocument();
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
    expect(screen.getAllByText('Team check-in')).toHaveLength(2);
    expect(screen.getAllByText('Interview with Ana Quispe')).toHaveLength(2);

    const tuesdayButton = screen.getByText('Jan 28').closest('button');
    if (tuesdayButton === null) {
      throw new Error('Tuesday calendar button was not rendered.');
    }
    await user.click(tuesdayButton);

    expect(screen.getAllByText('Bright Horizons staffing call')).toHaveLength(2);
    expect(screen.getAllByText('Meet Carlos Mendoza')).toHaveLength(2);
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
    expect(screen.getByText('Urgent intake review')).toBeInTheDocument();
    expect(screen.getByText('Employer follow-up')).toBeInTheDocument();
    expect(screen.getByText('Missing restricted address blocks review')).toBeInTheDocument();
    const urgentRow = screen.getByText('Urgent intake review').closest('article');
    if (!urgentRow) throw new Error('Urgent queue row was not rendered.');
    expect(within(urgentRow).getByRole('link', { name: 'Open' })).toHaveAttribute(
      'href',
      '/staff/intakes/workers?reference=b7dea69e-9b10-43b3-95aa-d1cd01f6c453&open=match',
    );

    await user.click(screen.getByRole('button', { name: 'Employer follow-ups' }));

    expect(screen.queryByText('Urgent intake review')).not.toBeInTheDocument();
    expect(screen.getByText('Employer follow-up')).toBeInTheDocument();
    expect(screen.getByText('Update interest catalog')).toBeInTheDocument();
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
    expect(screen.getByText('Worker drafts reviewed')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Export requires report permission' })).toBeDisabled();
  });
});
