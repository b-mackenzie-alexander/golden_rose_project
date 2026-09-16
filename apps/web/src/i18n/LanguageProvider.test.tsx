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
    expect(screen.getByRole('heading', { name: 'Nuestro Corazón Dorado' })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cambiar a español' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Employers' })).toHaveAttribute('aria-current', 'page');

    await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));

    expect(document.documentElement.lang).toBe('es');
    expect(screen.getByRole('heading', { name: 'Nuestro Corazón Dorado' })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Principal' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Switch to English' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Empleadores' })).toHaveAttribute('aria-current', 'page');

    await user.click(screen.getByRole('button', { name: 'Switch to English' }));

    expect(document.documentElement.lang).toBe('en');
    expect(screen.getByRole('heading', { name: 'Nuestro Corazón Dorado' })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Primary' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cambiar a español' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Employers' })).toHaveAttribute('aria-current', 'page');
  });

  it('keeps exact English and Spanish revision keys in parity', () => {
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

    const requiredRevisionKeys = [
      'employerRevisionEditAction',
      'employerRevisionHeading',
      'employerRevisionWarning',
      'employerRevisionTypeLabel',
      'employerRevisionNameLabel',
      'employerRevisionSubmit',
      'employerRevisionNameError',
      'employerRevisionTypeError',
      'employerRevisionNoOpError',
      'employerRevisionValidationFailureHeading',
      'employerRevisionValidationFailureBody',
      'employerRevisionForbiddenFailureHeading',
      'employerRevisionForbiddenFailureBody',
      'employerRevisionNotFoundHeading',
      'employerRevisionNotFoundBody',
      'employerRevisionStaleHeading',
      'employerRevisionStaleBody',
      'employerRevisionStaleReload',
      'employerRevisionConflictHeading',
      'employerRevisionConflictBody',
      'employerRevisionConflictReload',
      'employerRevisionUnknownHeading',
      'employerRevisionUnknownBody',
      'employerRevisionUnknownRetry',
      'employerRevisionRefreshFailureHeading',
      'employerRevisionRefreshFailureBody',
      'employerRevisionSuccessHeading',
      'employerRevisionSuccessBody',
    ] as const;

    expect(Object.keys(englishMessages)).toEqual(expect.arrayContaining([...requiredRevisionKeys]));
    expect(Object.keys(spanishMessages)).toEqual(expect.arrayContaining([...requiredRevisionKeys]));
    expect(englishMessages.employerRevisionEditAction).toBe('Edit draft employer');
    expect(englishMessages.employerRevisionSubmit).toBe('Save draft employer revision');
    expect(englishMessages.employerRevisionUnknownRetry).toBe('Retry same revision attempt');
    expect(englishMessages.employerRevisionConflictReload).toBe('Reload current employer detail');
    expect(englishMessages.employerRevisionStaleReload).toBe('Reload current employer detail');
    expect(englishMessages.employerRevisionSuccessBody).toContain('current draft employer detail');
    expect(spanishMessages.employerRevisionEditAction).toContain('Editar');
    expect(spanishMessages.employerRevisionSubmit).toContain('Guardar');
    expect(spanishMessages.employerRevisionForbiddenFailureBody).toContain('sesión del personal');
    expect(spanishMessages.employerRevisionRefreshFailureBody).toContain('detalle actual del empleador');
    expect(spanishMessages.employerRevisionSuccessBody).toContain('detalle actual del empleador en borrador');

    for (const revisionKey of requiredRevisionKeys) {
      expect(spanishMessages[revisionKey]).not.toBe(revisionKey);
    }
  });
});
