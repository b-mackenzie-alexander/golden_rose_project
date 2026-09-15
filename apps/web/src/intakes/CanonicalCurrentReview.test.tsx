import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { currentReview, reviewCanonical } from '../api/canonicalCorrectionClient';
import type { FinalizationOutputs } from '../api/intakeCanonicalContracts';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { CanonicalCurrentReview } from './CanonicalCurrentReview';
vi.mock('../api/canonicalCorrectionClient', () => ({ currentReview: vi.fn(), reviewCanonical: vi.fn() }));
const id = '11111111-1111-4111-8111-111111111111';
const ref = { id, version: 1, disposition: 'created' as const };
const outputs: FinalizationOutputs = { kind: 'worker', worker: ref, contact: ref, residence: ref, preferences: ref };
const state = { review_version: 0, latest_review_id: null, status: 'unreviewed' as const, dependencies: outputs };
function mount() {
  const onLock = vi.fn(), onDenied = vi.fn();
  render(<LanguageProvider><CanonicalCurrentReview intakeId={id} outputs={outputs} blocked={false} onLock={onLock} onDenied={onDenied} /></LanguageProvider>);
  return { onLock, onDenied };
}
beforeEach(() => { vi.clearAllMocks(); vi.mocked(currentReview).mockResolvedValue({ ok: true, value: state }); });
it('requires explicit read and locks other commands through an unknown original retry', async () => {
  vi.mocked(reviewCanonical).mockResolvedValueOnce({ ok: false, failure: 'unknown' }).mockResolvedValueOnce({ ok: true, value: { ...state, review_version: 1, latest_review_id: id, status: 'current' } });
  const { onLock } = mount(); expect(currentReview).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Check current review' }));
  await screen.findByText('Current facts have not been reviewed.');
  fireEvent.change(screen.getByLabelText('Review note (optional)'), { target: { value: 'Fictional original note' } });
  fireEvent.click(screen.getByRole('button', { name: 'Review current facts' }));
  await screen.findByText('Review outcome unknown. Retry the original request.');
  expect(onLock).toHaveBeenLastCalledWith(true);
  expect(screen.getByRole('button', { name: 'Check current review' })).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Review note (optional)'), { target: { value: 'Fictional later note' } });
  fireEvent.click(screen.getByRole('button', { name: 'Retry original review' }));
  await screen.findByText('Current facts review is current.');
  expect(vi.mocked(reviewCanonical).mock.calls[1]).toEqual(vi.mocked(reviewCanonical).mock.calls[0]);
  expect(onLock).toHaveBeenLastCalledWith(false);
});
it('clears protected facts on revocation', async () => {
  vi.mocked(currentReview).mockResolvedValue({ ok: false, failure: 'forbidden' });
  const { onDenied, onLock } = mount(); fireEvent.click(screen.getByRole('button', { name: 'Check current review' }));
  await waitFor(() => { expect(onDenied).toHaveBeenCalledOnce(); });
  expect(onLock).toHaveBeenLastCalledWith(false);
  expect(screen.queryByRole('button', { name: 'Review current facts' })).not.toBeInTheDocument();
});
