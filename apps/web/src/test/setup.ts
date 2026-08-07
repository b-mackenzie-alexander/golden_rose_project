import { configure, prettyDOM } from '@testing-library/dom';
import '@testing-library/jest-dom/vitest';

function redactDiagnosticText(value: string) {
  return value.replace(/SYNTHETIC_(?:EMPLOYER|API)_[A-Z_]+/g, '[REDACTED]');
}

configure({
  getElementError(message, container) {
    return new Error(
      redactDiagnosticText([message, prettyDOM(container)].filter(Boolean).join('\n\n')),
    );
  },
});
