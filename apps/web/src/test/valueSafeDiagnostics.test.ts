import { createElement } from 'react';
import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { VALUE_SAFE_TESTING_LIBRARY_MESSAGE } from './valueSafeDiagnostics';

it('revision controls preserve value-independent Testing Library diagnostics', () => {
  render(
    createElement(
      'div',
      null,
      createElement('label', { htmlFor: 'revision-employer-name' }, 'Revision employer name'),
      createElement('input', { id: 'revision-employer-name', defaultValue: 'SYNTHETIC_REVISION_DISPLAY_NAME' }),
      createElement('label', { htmlFor: 'revision-employer-type' }, 'Revision employer type'),
      createElement('select', { id: 'revision-employer-type', defaultValue: 'household' }, createElement('option', { value: 'household' }, 'Household')),
      createElement('p', null, 'Revision command id: 22222222-2222-4222-8222-222222222222'),
      createElement('p', null, 'Expected version: SECRET_EXPECTED_VERSION_7'),
      createElement('p', null, 'Opaque cursor/body marker: opaque-revision-body-marker-001'),
      createElement('p', null, 'Recovery text: SYNTHETIC_REVISION_RECOVERY_SECRET'),
    ),
  );

  try {
    screen.getByRole('heading', { name: 'Missing revision diagnostic target' });
  } catch (error) {
    expect(error).toBeInstanceOf(Error);
    const diagnosticError = error as Error;
    expect(diagnosticError.message).toContain(VALUE_SAFE_TESTING_LIBRARY_MESSAGE);
    expect(diagnosticError.message).not.toContain('SYNTHETIC_REVISION_DISPLAY_NAME');
    expect(diagnosticError.message).not.toContain('22222222-2222-4222-8222-222222222222');
    expect(diagnosticError.message).not.toContain('SECRET_EXPECTED_VERSION_7');
    expect(diagnosticError.message).not.toContain('opaque-revision-body-marker-001');
    expect(diagnosticError.message).not.toContain('SYNTHETIC_REVISION_RECOVERY_SECRET');
    expect(diagnosticError.stack).toContain('valueSafeDiagnostics.test.ts');
    return;
  }

  throw new Error('Expected Testing Library query to fail');
});
