export const VALUE_SAFE_TESTING_LIBRARY_MESSAGE =
  'Testing Library query failed. Detailed DOM output is disabled for privacy.';

export function createValueSafeElementError() {
  return new Error(VALUE_SAFE_TESTING_LIBRARY_MESSAGE);
}
