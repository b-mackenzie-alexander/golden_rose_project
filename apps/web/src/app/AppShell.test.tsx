import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router';

import { AppShell } from './AppShell';
import { LanguageProvider } from '../i18n/LanguageProvider';

describe('AppShell', () => {
  it('renders compact product header navigation and language action', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppShell />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const banner = screen.getByRole('banner');
    expect(banner).toHaveClass('app-header');
    expect(within(banner).getByRole('heading', { name: 'Golden Rose Staff Workspace' })).toHaveClass('app-brand');
    expect(within(banner).getByRole('navigation', { name: 'Primary' })).toHaveClass('primary-navigation');
    expect(within(banner).getByRole('link', { name: 'Employers' })).toHaveClass('nav-link');
    expect(within(banner).getByRole('button', { name: 'Cambiar a español' })).toHaveClass('language-action');
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
});
