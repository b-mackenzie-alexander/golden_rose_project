import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { correctCanonical } from '../api/canonicalCorrectionClient';
import { CanonicalCorrectionForm } from './CanonicalCorrectionForm';
vi.mock('../api/canonicalCorrectionClient', () => ({ correctCanonical: vi.fn() }));
const id = '11111111-1111-4111-8111-111111111111';
function mount() {
  return render(<LanguageProvider><CanonicalCorrectionForm path={`/workers/${id}/corrections`} targetId={id} output="worker" initial={{ full_name: 'Fictional Original' }} version={1} blocked={false} onLock={vi.fn()} onDirty={vi.fn()} onSaved={vi.fn().mockResolvedValue(true)} onDenied={vi.fn()} /></LanguageProvider>);
}
beforeEach(() => { vi.clearAllMocks(); });
it('corrects canonical facts without editing finalized intake', async () => {
  vi.mocked(correctCanonical).mockImplementation((_path, key) => Promise.resolve({ ok: true, value: { command_id: key, event_id: id, result_record_version: 2, target: { id, entity_type: 'worker', current_version: 2 } } }));
  mount(); fireEvent.click(screen.getByRole('button', { name: 'Correct this section' }));
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Fictional Corrected' } });
  fireEvent.change(screen.getByLabelText('Reason for correction'), { target: { value: 'Corrected reported name' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save correction' }));
  await screen.findByText('Correction saved. Current facts need re-review.');
  expect(correctCanonical).toHaveBeenCalledWith(`/workers/${id}/corrections`, expect.any(String), { expected_version: 1, reason_text: 'Corrected reported name', full_name: 'Fictional Corrected' }, id);
});
it('retains later dirty edits and retries the exact original body', async () => {
  vi.mocked(correctCanonical).mockResolvedValueOnce({ ok: false, failure: 'unknown' }).mockImplementationOnce((_path, key) => Promise.resolve({ ok: true, value: { command_id: key, event_id: id, result_record_version: 2, target: { id, entity_type: 'worker', current_version: 2 } } }));
  mount(); fireEvent.click(screen.getByRole('button', { name: 'Correct this section' }));
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Fictional First' } });
  fireEvent.change(screen.getByLabelText('Reason for correction'), { target: { value: 'Correction' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save correction' }));
  await screen.findByText(/Outcome unknown/);
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Fictional Later' } });
  await act(async () => { await Promise.resolve(); fireEvent.click(screen.getByRole('button', { name: 'Retry original correction' })); });
  expect(screen.getByLabelText('Full name')).toHaveValue('Fictional Later');
  expect(screen.getByText('Unsaved correction')).toBeInTheDocument();
  expect(vi.mocked(correctCanonical).mock.calls[1]).toEqual(vi.mocked(correctCanonical).mock.calls[0]);
});
it('requires comparison when a replay discovers another writer', async () => {
  vi.mocked(correctCanonical).mockImplementation((_path, key) => Promise.resolve({ ok: true, value: { command_id: key, event_id: id, result_record_version: 2, target: { id, entity_type: 'worker', current_version: 3 } } }));
  mount(); fireEvent.click(screen.getByRole('button', { name: 'Correct this section' }));
  fireEvent.change(screen.getByLabelText('Reason for correction'), { target: { value: 'Correction' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save correction' }));
  await screen.findByText('The record changed. Compare current facts before correcting again.');
  expect(screen.getByRole('button', { name: 'Save correction' })).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Fictional later edit' } });
  expect(screen.getByRole('button', { name: 'Save correction' })).toBeDisabled();
});
