import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';

import { AppShell } from './AppShell';
import { LanguageProvider } from '../i18n/LanguageProvider';

describe('AppShell', () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
  });

  it('renders the dashboard shell navigation and language action', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppShell />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const banner = screen.getByRole('banner');
    expect(banner).toHaveClass('app-header');
    expect(within(banner).getByRole('button', { name: 'Cambiar a español' })).toHaveClass('language-action');
    expect(screen.getByRole('heading', { name: 'Nuestro Corazón Dorado' })).toHaveClass('app-brand');
    expect(screen.getByRole('navigation', { name: 'Primary' })).toHaveClass('primary-navigation');
    expect(screen.getByRole('link', { name: 'Employers' })).toHaveClass('nav-link');
    const accountGroup = document.querySelector('.nav-account-group');
    expect(accountGroup).toContainElement(screen.getByRole('link', { name: 'My account' }));
    expect(accountGroup).toContainElement(screen.getByRole('link', { name: 'Staff accounts' }));
    expect(accountGroup).not.toContainElement(screen.getByRole('link', { name: 'Map' }));
    expect(screen.getByRole('main')).toHaveClass('app-main');
  });

  it('renders the staff workspace landmarks', () => {
    render(
      <MemoryRouter initialEntries={['/employers']}>
        <AppShell />
      </MemoryRouter>,
    );

    expect(screen.getByRole('banner')).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Employers' })).toHaveAttribute('aria-current', 'page');
  });

  it('does not hardcode a named staff identity before session verification', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppShell />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const accountButton = screen.getByRole('button', { name: 'Open my staff account' });
    expect(accountButton).toHaveTextContent('Staff account');
    expect(accountButton).toHaveTextContent('Verify session');
    expect(accountButton).not.toHaveTextContent('Mariela Torres');
    expect(accountButton).not.toHaveTextContent('Operations team');
  });

  it('persists light and dark mode from the utility toggle', async () => {
    const user = userEvent.setup();
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppShell />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Switch to dark mode' }));

    expect(document.documentElement.dataset.theme).toBe('dark');
    expect(window.localStorage.getItem('golden-rose-theme')).toBe('dark');
    expect(screen.getByRole('button', { name: 'Switch to light mode' })).toHaveAttribute('aria-pressed', 'true');

    await user.click(screen.getByRole('button', { name: 'Switch to light mode' }));

    expect(document.documentElement.dataset.theme).toBe('light');
    expect(window.localStorage.getItem('golden-rose-theme')).toBe('light');
  });
});
