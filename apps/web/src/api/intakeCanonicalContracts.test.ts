import { expect, it } from 'vitest';
import { finalizationOutputs, intakeLinks, linkBody, sameOutputs } from './intakeCanonicalContracts';
import type { FinalizationOutputs } from './intakeCanonicalContracts';

const ref = { id: '11111111-1111-4111-8111-111111111111', version: 1 };
const created = { ...ref, disposition: 'created' as const };
const reused = { ...ref, disposition: 'reused' as const };
const employer: FinalizationOutputs = { kind: 'employer', employer: reused, contact: reused,
  contact_details: reused, worksite: created, request: created, business_address: null };

it('accepts selective employer outputs and key-order independent comparison', () => {
  expect(finalizationOutputs(employer, 'employer')).toBe(true);
  expect(sameOutputs(employer, { ...employer, employer: { disposition: 'reused', version: 1, id: ref.id } })).toBe(true);
});

it.each([
  { request: reused }, { contact_details: created }, { employer: created },
  { worksite: { ...created, version: 2 } }, { business_address: undefined },
  { request: { ...created, id: '00000000-0000-0000-0000-000000000000' } },
])('rejects inconsistent employer outputs %#', (patch) => {
  expect(finalizationOutputs({ ...employer, ...patch }, 'employer')).toBe(false);
});

it.each([
  { employer_contact: ref }, { employer: ref, employer_contact: ref },
  { employer: ref, worker: ref }, { employer: { ...ref, version: 0 } },
])('rejects invalid employer dependency shapes %#', (links) => {
  expect(intakeLinks(links, 'employer')).toBe(false);
});

it('accepts parent-only and complete selected child links', () => {
  expect(intakeLinks({ employer: ref }, 'employer')).toBe(true);
  expect(intakeLinks({ employer: ref, employer_contact: ref, employer_contact_details: ref,
    worksite: ref, employer_address: ref }, 'employer')).toBe(true);
  expect(linkBody({ expected_version: 1, party: ref, contact: ref })).toBe(true);
  expect(linkBody({ expected_version: 1, party: null, contact: null })).toBe(true);
});

it.each([
  { expected_version: true, party: ref }, { expected_version: 2147483647, party: ref },
  { expected_version: 1, party: null, contact: ref }, { expected_version: 1 },
  { expected_version: 1, party: ref, candidate: {} },
])('rejects malformed link requests %#', (body) => {
  expect(linkBody(body)).toBe(false);
});
