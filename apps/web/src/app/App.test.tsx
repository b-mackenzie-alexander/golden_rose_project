import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { vi } from 'vitest';

import { createEmployer, getEmployer, searchEmployers } from '../api/employerClient';
import { AppRoutes } from './App';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { runAxe } from '../test/axe';

vi.mock('../api/employerClient', () => ({
  createEmployer: vi.fn(),
  getEmployer: vi.fn(),
  searchEmployers: vi.fn(),
}));

describe('App', () => {
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
    await user.selectOptions(screen.getByLabelText('Create employer type'), 'household');
    await user.type(screen.getByLabelText('Create employer name'), 'Focus Create Rose');

    const controls = [
      screen.getByRole('link', { name: 'Employers' }),
      screen.getByRole('button', { name: 'Cambiar a español' }),
      screen.getByLabelText('Employer name'),
      screen.getByLabelText('Employer type'),
      screen.getByRole('button', { name: 'Search employers' }),
      screen.getByRole('button', { name: 'Focus Rose' }),
      screen.getByRole('button', { name: 'Load more employers' }),
      screen.getByLabelText('Create employer type'),
      screen.getByLabelText('Create employer name'),
      screen.getByRole('button', { name: 'Create draft employer' }),
    ];

    for (const control of controls) {
      expect(control).toHaveClass('focus-ring');
    }
  });

  it('has no automated axe violations in both locales', async () => {
    const user = userEvent.setup();
    vi.mocked(searchEmployers).mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '90909090-9090-4090-8090-909090909090',
            employerType: 'business',
            displayName: 'Axe Rose',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    vi.mocked(getEmployer).mockResolvedValue({
      ok: true,
      value: {
        employerId: '90909090-9090-4090-8090-909090909090',
        employerType: 'business',
        displayName: 'Axe Rose',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
      },
    });
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
    await user.click(screen.getByRole('button', { name: 'Axe Rose' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.selectOptions(screen.getByLabelText('Create employer type'), 'household');
    await user.type(screen.getByLabelText('Create employer name'), 'Create Axe Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));
    await screen.findByRole('heading', { name: 'Draft employer created' });

    expect(await runAxe(view.container)).toEqual([]);

    await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));
    await screen.findByRole('heading', { name: 'Buscar un empleador' });

    expect(await runAxe(view.container)).toEqual([]);
  });

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
    expect(orderedHeadings.map((heading) => heading.textContent)).toEqual([
      'Search for an employer',
      'Create a draft employer',
    ]);

    expect(screen.getByRole('form', { name: 'Create a draft employer' })).toBeInTheDocument();
    expect(screen.getByRole('form', { name: 'Employer search' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Employers' })).toHaveAttribute('aria-current', 'page');
  });

  it('routes root employers and unknown paths safely', () => {
    const rootRoute = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole('link', { name: 'Employers' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('heading', { name: 'Search for an employer' })).toBeInTheDocument();
    expect(screen.getByRole('form', { name: 'Employer search' })).toBeInTheDocument();
    rootRoute.unmount();

    const employersRoute = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole('link', { name: 'Employers' })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('heading', { name: 'Search for an employer' })).toBeInTheDocument();
    expect(screen.getByRole('form', { name: 'Employer search' })).toBeInTheDocument();
    employersRoute.unmount();

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
