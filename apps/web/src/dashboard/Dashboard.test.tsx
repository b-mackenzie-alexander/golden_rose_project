import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';

import { AppRoutes } from '../app/App';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { runAxe } from '../test/axe';

describe('Dashboard', () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.documentElement.removeAttribute('data-theme');
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
    expect(screen.getAllByRole('link').some((link) => {
      const text = link.textContent;
      return link.getAttribute('href') === '/staff/intakes/workers' && text.includes('12') && text.includes('Worker intakes');
    })).toBe(true);
    expect(screen.getByRole('heading', { name: "Today's priorities" })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: "Today's schedule" })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Quick actions' })).toBeInTheDocument();
    expect(view.container.querySelector('.brand-rose')).toBeInTheDocument();
    expect(view.container.querySelector('.skyline-artwork')).toBeInTheDocument();
    expect(screen.getByRole('img', { name: 'La comunidad nos mueve' })).toHaveClass('mission-statement-mark');
    expect(view.container.querySelector('.zone-map-artwork')).toBeInTheDocument();
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
    expect(screen.getByText('This staff workspace route is now reserved in navigation and can be connected to its workflow data in a later implementation pass.')).toBeInTheDocument();
  });
});
