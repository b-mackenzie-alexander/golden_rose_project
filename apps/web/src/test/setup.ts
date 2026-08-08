import { configure } from '@testing-library/dom';
import '@testing-library/jest-dom/vitest';
import { createValueSafeElementError } from './valueSafeDiagnostics';

configure({
  getElementError() {
    return createValueSafeElementError();
  },
});
