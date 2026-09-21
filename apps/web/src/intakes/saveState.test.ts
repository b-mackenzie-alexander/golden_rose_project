import { describe, expect, it } from 'vitest';
import { initialSection, editSection, submitSection, finishSection, allSaved } from './saveState';

describe('section-local saves', () => {
  it('keeps later edits unsaved after pending save', () => {
    const edited = editSection(initialSection({ full_name: 'First' }), { full_name: 'Submitted' });
    const pending = submitSection(edited, 'key', 1, '/intakes/id/revisions');
    const later = editSection(pending, { full_name: 'Later' });
    const saved = finishSection(later, 'saved');
    expect(saved.value).toEqual({ full_name: 'Later' });
    expect(saved.status).toBe('unsaved');
    expect(saved.command).toBeNull();
  });
  it('retries unknown saves with original command identity', () => {
    const pending = submitSection(
      editSection(initialSection({}), { full_name: 'First' }),
      'original',
      3,
      '/intakes/id/revisions',
    );
    const unknown = finishSection(pending, 'unknown');
    const later = editSection(unknown, { full_name: 'Later' });
    expect(later.command).toBe(pending.command);
    expect(later.command?.body).toEqual({ expected_version: 3, content: { full_name: 'First' } });
    expect(later.status).toBe('unknown');
  });
  it('turns recovery-state edits back into saveable unsaved changes', () => {
    const refresh = { ...initialSection({ line1: 'Submitted address' }), status: 'refresh' as const };
    const later = editSection(refresh, { line1: 'Corrected address' });
    expect(later.value).toEqual({ line1: 'Corrected address' });
    expect(later.status).toBe('unsaved');
  });
  it('keeps aggregate unsaved after one section succeeds and next unknown with later edits', () => {
    const saved = finishSection(
      submitSection(
        editSection(initialSection({}), { full_name: 'First' }),
        'one',
        1,
        '/intakes/id/revisions',
      ),
      'saved',
    );
    const unknown = editSection(
      finishSection(
        submitSection(
          editSection(initialSection({}), { line1: 'First' }),
          'two',
          2,
          '/intakes/id/addresses/worker_residence/revisions',
          true,
        ),
        'unknown',
      ),
      { line1: 'Later' },
    );
    expect(allSaved([saved, unknown])).toBe(false);
    expect(allSaved([saved, initialSection({})])).toBe(true);
    expect(allSaved([saved, { ...initialSection({}), status: 'unavailable' }])).toBe(false);
  });
});
