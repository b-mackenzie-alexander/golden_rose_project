import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';

import { AppRoutes } from '../app/App';
import { LanguageProvider } from './LanguageProvider';
import { englishMessages, spanishMessages } from './messages';

describe('LanguageProvider', () => {
  it('switches all shell copy and document language', async () => {
    const user = userEvent.setup();

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(document.documentElement.lang).toBe('en');
    expect(screen.getByRole('heading', { name: 'Golden Rose Staff Workspace' })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cambiar a español' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Employers' })).toHaveAttribute('aria-current', 'page');

    await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));

    expect(document.documentElement.lang).toBe('es');
    expect(screen.getByRole('heading', { name: 'Espacio de trabajo del personal de Golden Rose' })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Principal' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Switch to English' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Empleadores' })).toHaveAttribute('aria-current', 'page');

    await user.click(screen.getByRole('button', { name: 'Switch to English' }));

    expect(document.documentElement.lang).toBe('en');
    expect(screen.getByRole('heading', { name: 'Golden Rose Staff Workspace' })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cambiar a español' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Employers' })).toHaveAttribute('aria-current', 'page');
  });

  it('keeps versioned English and Spanish catalogs complete', () => {
    const englishCatalog = englishMessages as Record<string, string> & {
      catalogVersion?: string;
      reviewStatus?: string;
    };
    const spanishCatalog = spanishMessages as Record<string, string> & {
      catalogVersion?: string;
      reviewStatus?: string;
    };

    expect(englishCatalog.catalogVersion).toBe('Proposed');
    expect(englishCatalog.reviewStatus).toBe('Proposed');
    expect(spanishCatalog.catalogVersion).toBe('Proposed');
    expect(spanishCatalog.reviewStatus).toBe('Proposed');

    const englishKeys = Object.keys(englishCatalog).filter((key) => !key.endsWith('Version') && key !== 'reviewStatus');
    const spanishKeys = Object.keys(spanishCatalog).filter((key) => !key.endsWith('Version') && key !== 'reviewStatus');

    expect(spanishKeys).toEqual(englishKeys);
    expect(spanishMessages.employerSearchInstructions).toContain('sintética');
    expect(englishMessages.employerCreateValidationFailureHeading).toBe('Create draft employer could not be completed');
    expect(englishMessages.employerCreateForbiddenFailureHeading).toBe(
      'Create draft employer is not available for this staff session',
    );
    expect(spanishMessages.employerCreateValidationFailureHeading).toContain('creación');
    expect(spanishMessages.employerCreateForbiddenFailureBody).toContain('permiso');

    for (const [messageKey, messageValue] of Object.entries(spanishMessages)) {
      expect(messageValue).not.toBe(messageKey);
    }
  });
});
