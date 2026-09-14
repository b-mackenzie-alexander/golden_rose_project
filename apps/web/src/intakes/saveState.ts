import type { DraftObject, IntakeKind } from '../api/intakeContracts';

export type SaveStatus =
  | 'refresh'
  | 'loading'
  | 'saved'
  | 'unsaved'
  | 'saving'
  | 'unknown'
  | 'failed'
  | 'unavailable';
export type Command = Readonly<{ key: string; path: string; body: DraftObject; generation: number }>;
export type Section = {
  value: DraftObject;
  generation: number;
  confirmedGeneration: number;
  readPending?: boolean;
  status: SaveStatus;
  command: Command | null;
};
export const initialSection = (value: DraftObject): Section => ({
  value,
  generation: 0,
  confirmedGeneration: 0,
  status: 'saved',
  command: null,
});
export function editSection(section: Section, value: DraftObject): Section {
  return {
    ...section,
    value,
    generation: section.generation + 1,
    status: section.command || section.status === 'refresh' ? section.status : 'unsaved',
  };
}
export function submitSection(
  section: Section,
  key: string,
  version: number,
  path: string,
  address = false,
  kind?: IntakeKind,
): Section {
  const content = structuredClone(section.value);
  const body: DraftObject = kind
    ? { kind, content }
    : address
      ? { expected_version: version, address: Object.keys(content).length ? content : null }
      : { expected_version: version, content };
  return {
    ...section,
    status: 'saving',
    command: Object.freeze({ key, path, body, generation: section.generation }),
  };
}
export function finishSection(section: Section, status: 'saved' | 'unknown' | 'failed'): Section {
  if (status === 'unknown') return { ...section, status };
  return {
    ...section,
    confirmedGeneration:
      status === 'saved'
        ? (section.command?.generation ?? section.confirmedGeneration)
        : section.confirmedGeneration,
    command: null,
    status: status === 'saved' && section.command?.generation !== section.generation ? 'unsaved' : status,
  };
}
export const allSaved = (sections: Section[]) => sections.every((section) => section.status === 'saved');
