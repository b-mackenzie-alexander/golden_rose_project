import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router';

import { AppShell } from './AppShell';

describe('AppShell', () => {
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
