import { createElement } from 'react';
import { render, screen } from '@testing-library/react';
import { expect, it } from 'vitest';
import { VALUE_SAFE_TESTING_LIBRARY_MESSAGE } from './valueSafeDiagnostics';

it('uses value-independent Testing Library diagnostics', () => {
  render(
    createElement(
      'div',
      null,
      createElement('label', { htmlFor: 'employer-name' }, 'Employer name'),
      createElement('input', { id: 'employer-name', defaultValue: 'Golden Lantern Staffing' }),
      createElement('p', null, 'Employer UUID: 11111111-1111-4111-8111-111111111111'),
      createElement('p', null, 'Cursor: opaque-cursor-privacy-001'),
      createElement('p', null, 'API response: synthetic employer detail body'),
    ),
  );

  try {
    screen.getByText('This text is intentionally absent');
  } catch (error) {
    expect(error).toBeInstanceOf(Error);
    const diagnosticError = error as Error;
    expect(diagnosticError.message).toContain(VALUE_SAFE_TESTING_LIBRARY_MESSAGE);
    expect(diagnosticError.message).not.toContain('Golden Lantern Staffing');
    expect(diagnosticError.message).not.toContain('11111111-1111-4111-8111-111111111111');
    expect(diagnosticError.message).not.toContain('opaque-cursor-privacy-001');
    expect(diagnosticError.message).not.toContain('synthetic employer detail body');
    expect(diagnosticError.stack).toContain('valueSafeDiagnostics.test.ts');
    return;
  }

  throw new Error('Expected Testing Library query to fail');
});
