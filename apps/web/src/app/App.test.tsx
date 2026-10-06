import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { vi } from 'vitest';

import { createEmployer, getEmployer, reviseEmployer, searchEmployers } from '../api/employerClient';
import { reloadCanonicalDocument } from '../browser/privacyLifecycle';
import { App, AppRoutes } from './App';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { runAxe } from '../test/axe';

vi.mock('../api/employerClient', () => ({
  createEmployer: vi.fn(),
  getEmployer: vi.fn(),
  reviseEmployer: vi.fn(),
  searchEmployers: vi.fn(),
}));

vi.mock(
  '../browser/privacyLifecycle',
  () => ({
    reloadCanonicalDocument: vi.fn(),
  }),
);

describe('App', () => {
  it('switches the real app between complete English and Spanish catalogs', async () => {
    const user = userEvent.setup();
    window.history.pushState({}, '', '/employers');

    render(<App />);

    expect(document.documentElement.lang).toBe('en');
    expect(screen.getByRole('heading', { name: 'Nuestro Corazón Dorado' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Find an employer' })).toBeInTheDocument();
    expect(screen.getByLabelText('Employer name')).toBeInTheDocument();
    expect(screen.getByLabelText('Draft employer display name')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));

    expect(document.documentElement.lang).toBe('es');
    expect(screen.getByRole('heading', { name: 'Nuestro Corazón Dorado' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Buscar un empleador' })).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Guía del flujo de trabajo' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Buscar primero' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Crear solo si hace falta' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Revisar y actualizar' })).toBeInTheDocument();
    expect(screen.getByText('Paso actual')).toBeInTheDocument();
    expect(screen.getByText('Busque primero antes de crear un nuevo empleador en borrador.')).toBeInTheDocument();
    expect(screen.getByText('Comience buscando un empleador antes de crear o revisar un borrador.')).toBeInTheDocument();
    expect(screen.getByLabelText('Nombre del empleador')).toBeInTheDocument();
    expect(screen.getByLabelText('Nombre visible del empleador en borrador')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Switch to English' }));

    expect(document.documentElement.lang).toBe('en');
    expect(screen.getByRole('heading', { name: 'Nuestro Corazón Dorado' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Find an employer' })).toBeInTheDocument();
    expect(screen.getByLabelText('Employer name')).toBeInTheDocument();
    expect(screen.getByLabelText('Draft employer display name')).toBeInTheDocument();
  });

  it('reloads the canonical document after a persisted restore', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const pageShowEvent = new Event('pageshow');
    Object.defineProperty(pageShowEvent, 'persisted', { configurable: true, value: true });
    window.dispatchEvent(pageShowEvent);

    expect(reloadCanonicalDocument).toHaveBeenCalledTimes(1);
  });

  it('provides focus hooks for every interactive control', async () => {
    const user = userEvent.setup();
    vi.mocked(searchEmployers).mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: 'a0a0a0a0-a0a0-40a0-80a0-a0a0a0a0a0a0',
            employerType: 'business',
            displayName: 'Focus Rose',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: 'opaque-focus-page',
      },
    });
    vi.mocked(getEmployer).mockResolvedValue({
      ok: true,
      value: {
        employerId: 'a0a0a0a0-a0a0-40a0-80a0-a0a0a0a0a0a0',
        employerType: 'business',
        displayName: 'Focus Rose',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 1,
        updatedAt: '2026-08-11T04:20:00Z',
      },
    });
    vi.mocked(createEmployer).mockResolvedValue({
      ok: true,
      value: {
        employerId: 'b0b0b0b0-b0b0-40b0-80b0-b0b0b0b0b0b0',
        employerType: 'household',
        displayName: 'Focus Create Rose',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
      },
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Focus');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Focus Rose' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'household');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Focus Create Rose');

    const controls = [
      screen.getByRole('link', { name: 'Employers' }),
      screen.getByRole('button', { name: 'Cambiar a español' }),
      screen.getByLabelText('Employer name'),
      screen.getByLabelText('Employer type'),
      screen.getByRole('button', { name: 'Search employers' }),
      screen.getByRole('button', { name: 'Focus Rose' }),
      screen.getByRole('button', { name: 'Load more employers' }),
      screen.getByLabelText('Draft employer type'),
      screen.getByLabelText('Draft employer display name'),
      screen.getByRole('button', { name: 'Create draft employer' }),
    ];

    for (const control of controls) {
      expect(control).toHaveClass('focus-ring');
    }
  });

  it('has no automated axe violations in both locales and passes_axe_in_wave_1_initial_populated_selected_success_error_and_bilingual_states', async () => {
    const user = userEvent.setup();
    const selectedDetail = {
      employerId: '90909090-9090-4090-8090-909090909090',
      employerType: 'business' as const,
      displayName: 'Axe Rose',
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 1,
      updatedAt: '2026-08-11T04:25:00Z',
    };
    const revisedDetail = {
      ...selectedDetail,
      employerType: 'household' as const,
      displayName: 'Axe Rose Revised',
      version: 2,
      updatedAt: '2026-08-11T04:30:00Z',
    };

    vi.mocked(searchEmployers).mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: selectedDetail.employerId,
            employerType: selectedDetail.employerType,
            displayName: selectedDetail.displayName,
            lifecycleStatus: selectedDetail.lifecycleStatus,
          },
        ],
        nextCursor: null,
      },
    });
    vi.mocked(getEmployer).mockResolvedValueOnce({ ok: true, value: selectedDetail }).mockResolvedValue({ ok: true, value: revisedDetail });
    vi.mocked(createEmployer).mockResolvedValue({
      ok: true,
      value: {
        employerId: '91919191-9191-4191-8191-919191919191',
        employerType: 'household',
        displayName: 'Create Axe Rose',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
      },
    });
    vi.mocked(reviseEmployer).mockResolvedValue({
      ok: true,
      value: {
        detail: revisedDetail,
        resultVersion: 2,
        replayed: false,
      },
    });
    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValue('93939393-9393-4393-8393-939393939393');

    const view = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(await runAxe(view.container)).toEqual([]);

    await user.type(screen.getByLabelText('Employer name'), 'Axe');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    expect(await runAxe(view.container)).toEqual([]);

    await user.click(screen.getByRole('button', { name: 'Axe Rose' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    expect(await runAxe(view.container)).toEqual([]);

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Axe Rose Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));
    await screen.findByRole('heading', { name: 'Draft employer revision saved' });
    expect(await runAxe(view.container)).toEqual([]);

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'household');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Create Axe Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));
    await screen.findByRole('heading', { name: 'Draft employer created' });
    expect(await runAxe(view.container)).toEqual([]);

    await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));
    await screen.findByRole('heading', { name: 'Buscar un empleador' });
    expect(document.documentElement.lang).toBe('es');
    expect(await runAxe(view.container)).toEqual([]);
    await user.click(screen.getByRole('button', { name: 'Switch to English' }));
    expect(document.documentElement.lang).toBe('en');
    expect(await runAxe(view.container)).toEqual([]);

    view.unmount();
    vi.mocked(searchEmployers).mockResolvedValue({ ok: false, failure: { kind: 'unavailable' } });

    const errorView = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Axe');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search is temporarily unavailable' });
    expect(await runAxe(errorView.container)).toEqual([]);

    randomUuidSpy.mockRestore();
  }, 60000);

  it('exposes one ordered semantic workspace', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getAllByRole('banner')).toHaveLength(1);
    expect(screen.getAllByRole('navigation')).toHaveLength(1);
    expect(screen.getAllByRole('main')).toHaveLength(1);

    const workspace = screen.getByRole('region', { name: 'Employers workspace' });
    const orderedHeadings = within(workspace).getAllByRole('heading');
    expect(orderedHeadings.map((heading) => heading.textContent).slice(0, 8)).toEqual([
      'Employer workspace',
      'Workspace overview',
      'Workflow guide',
      'Search first',
      'Create only if needed',
      'Review and revise',
      'Find an employer',
      'Create a draft employer',
    ]);

    expect(screen.getByRole('form', { name: 'Create a draft employer' })).toBeInTheDocument();
    expect(screen.getByRole('form', { name: 'Employer search' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Employers' })).toHaveAttribute('aria-current', 'page');
  });

  it('exposes constrained workspace layout hooks without an environment banner', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole('main')).toHaveClass('app-main');
    const workspace = screen.getByRole('region', { name: 'Employers workspace' });
    expect(workspace).toHaveClass('workspace-stack');
    expect(workspace).toHaveAttribute('data-layout', 'employer-workspace');
    const safetyCopy = screen.queryAllByText(/private|synthetic|develop/i);
    for (const copy of safetyCopy) {
      expect(copy).not.toHaveClass('environment-banner');
    }
    expect(document.querySelector('.environment-banner')).not.toBeInTheDocument();
  });

  it('keeps all primary controls at least 44px and avoids full viewport actions', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const controls = [
      screen.getByLabelText('Employer name'),
      screen.getByLabelText('Employer type'),
      screen.getByRole('button', { name: 'Search employers' }),
      screen.getByLabelText('Draft employer type'),
      screen.getByLabelText('Draft employer display name'),
      screen.getByRole('button', { name: 'Create draft employer' }),
    ];

    for (const control of controls) {
      expect(control).toHaveClass('control-44');
      expect(control).not.toHaveClass('viewport-wide-action');
    }
  });

  it('routes root dashboard, employers, and unknown paths safely', () => {
    const rootRoute = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole('link', { name: 'Home' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('heading', { name: /Good (morning|afternoon|evening)/ })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: "Today's priorities" })).toBeInTheDocument();
    rootRoute.unmount();

    const employersRoute = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole('link', { name: 'Employers' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('heading', { name: 'Find an employer' })).toBeInTheDocument();
    expect(screen.getByRole('form', { name: 'Employer search' })).toBeInTheDocument();
    employersRoute.unmount();

    const mapRoute = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/staff/map']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole('link', { name: 'Map' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('heading', { name: 'Activity map' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back to dashboard' })).toHaveAttribute('href', '/');
    mapRoute.unmount();

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/not-a-route']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.queryByRole('link', { name: 'Employers' })).not.toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('heading', { name: 'Page not found / Página no encontrada' })).toBeInTheDocument();
  });
});
