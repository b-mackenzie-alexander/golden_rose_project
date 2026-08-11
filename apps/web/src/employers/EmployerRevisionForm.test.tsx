import { act, fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';

import { reviseEmployer } from '../api/employerClient';
import { LanguageProvider, useLanguage } from '../i18n/LanguageProvider';
import { runAxe } from '../test/axe';
import { EmployerRevisionForm } from './EmployerRevisionForm';

vi.mock('../api/employerClient', () => ({
  reviseEmployer: vi.fn(),
}));

function createDeferredPromise<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;

  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });

  return { promise, resolve, reject };
}

function RevisionFormLocaleHarness({ children }: { children: React.ReactNode }) {
  const { messages, toggleLanguage } = useLanguage();

  return (
    <>
      <button onClick={toggleLanguage} type="button">
        {messages.switchLanguage}
      </button>
      {children}
    </>
  );
}

describe('EmployerRevisionForm', () => {
  it('opens from current detail and submits one validated expected-version command', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    const onRevisionSuccess = vi.fn();
    const onAuthorityChange = vi.fn();

    reviseEmployerMock.mockReset();
    reviseEmployerMock.mockResolvedValue({
      ok: true,
      value: {
        detail: {
          employerId: '33333333-3333-4333-8333-333333333333',
          employerType: 'household',
          displayName: 'Golden Rose Household Updated',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 8,
          updatedAt: '2026-08-11T03:30:00Z',
        },
        resultVersion: 8,
        replayed: false,
      },
    });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValue('44444444-4444-4444-8444-444444444444');

    render(
      <LanguageProvider>
        <EmployerRevisionForm
          detail={{
            employerId: '33333333-3333-4333-8333-333333333333',
            employerType: 'business',
            displayName: 'Golden Rose Business',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 7,
            updatedAt: '2026-08-11T03:00:00Z',
          }}
          onAuthorityChange={onAuthorityChange}
          onRevisionSuccess={onRevisionSuccess}
        />
      </LanguageProvider>,
    );

    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();
    expect(screen.queryByLabelText('Revision employer type')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));

    expect(await screen.findByLabelText('Revision employer type')).toBeInTheDocument();

    const typeSelect = screen.getByLabelText('Revision employer type');
    const nameInput = screen.getByLabelText('Revision employer name');
    const submitButton = screen.getByRole('button', { name: 'Save draft employer revision' });

    expect(typeSelect).toHaveValue('business');
    expect(nameInput).toHaveValue('Golden Rose Business');

    await user.selectOptions(typeSelect, 'household');
    await user.clear(nameInput);
    await user.type(nameInput, 'Golden Rose Household Updated');
    await user.click(submitButton);

    expect(reviseEmployerMock).toHaveBeenCalledTimes(1);
    expect(reviseEmployerMock).toHaveBeenCalledWith({
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '44444444-4444-4444-8444-444444444444',
      expectedVersion: 7,
      employerType: 'household',
      displayName: 'Golden Rose Household Updated',
    });
    expect(onAuthorityChange).toHaveBeenNthCalledWith(1, { owner: 'revision', locked: true });
    expect(onAuthorityChange).toHaveBeenNthCalledWith(2, { owner: null, locked: false });
    expect(onRevisionSuccess).toHaveBeenCalledWith({
      detail: {
        employerId: '33333333-3333-4333-8333-333333333333',
        employerType: 'household',
        displayName: 'Golden Rose Household Updated',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 8,
        updatedAt: '2026-08-11T03:30:00Z',
      },
      resultVersion: 8,
      replayed: false,
    });
    expect(screen.queryByLabelText('Revision employer type')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('rejects invalid and normalized no-op edits before command creation', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);

    reviseEmployerMock.mockReset();

    render(
      <LanguageProvider>
        <EmployerRevisionForm
          detail={{
            employerId: '33333333-3333-4333-8333-333333333333',
            employerType: 'business',
            displayName: 'Golden Rose Business',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 7,
            updatedAt: '2026-08-11T03:00:00Z',
          }}
        />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));

    const typeSelect = screen.getByLabelText('Revision employer type');
    const nameInput = screen.getByLabelText('Revision employer name');
    const submitButton = screen.getByRole('button', { name: 'Save draft employer revision' });

    await user.clear(nameInput);
    await user.type(nameInput, '   ');
    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent('Enter 1 to 200 visible characters for the employer name.');
    expect(nameInput).toHaveFocus();
    expect(reviseEmployerMock).not.toHaveBeenCalled();

    await user.clear(nameInput);
    await user.type(nameInput, 'Valid Revision');
    await user.selectOptions(typeSelect, '');
    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Select either Business or Household before saving the draft employer revision.',
    );
    expect(typeSelect).toHaveFocus();
    expect(reviseEmployerMock).not.toHaveBeenCalled();

    await user.selectOptions(typeSelect, 'business');
    await user.clear(nameInput);
    await user.type(nameInput, 'Golden Rose Business');
    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Change the employer type or employer name before saving the draft employer revision.',
    );
    expect(nameInput).toHaveFocus();
    expect(reviseEmployerMock).not.toHaveBeenCalled();
  });

  it('retries unknown outcome with the identical command key and payload', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);

    reviseEmployerMock.mockReset();
    reviseEmployerMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValue('55555555-5555-4555-8555-555555555555');

    render(
      <LanguageProvider>
        <EmployerRevisionForm
          detail={{
            employerId: '33333333-3333-4333-8333-333333333333',
            employerType: 'business',
            displayName: 'Golden Rose Business',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 7,
            updatedAt: '2026-08-11T03:00:00Z',
          }}
        />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Unknown Revision Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const unknownHeading = await screen.findByRole('heading', { name: 'Revision outcome is unknown' });
    const unknownRegion = unknownHeading.closest('section');
    expect(unknownRegion).not.toBeNull();
    expect(reviseEmployerMock).toHaveBeenCalledTimes(1);
    expect(reviseEmployerMock).toHaveBeenNthCalledWith(1, {
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '55555555-5555-4555-8555-555555555555',
      expectedVersion: 7,
      employerType: 'household',
      displayName: 'Unknown Revision Rose',
    });

    await user.click(within(unknownRegion as HTMLElement).getByRole('button', { name: 'Retry same revision attempt' }));

    expect(reviseEmployerMock).toHaveBeenCalledTimes(2);
    expect(reviseEmployerMock).toHaveBeenNthCalledWith(2, {
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '55555555-5555-4555-8555-555555555555',
      expectedVersion: 7,
      employerType: 'household',
      displayName: 'Unknown Revision Rose',
    });

    randomUuidSpy.mockRestore();
  });

  it('requires canonical reload before releasing conflict authority', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    const onCanonicalReload = vi.fn().mockResolvedValue(undefined);

    reviseEmployerMock.mockReset();
    reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValue('66666666-6666-4666-8666-666666666666');

    render(
      <LanguageProvider>
        <EmployerRevisionForm
          detail={{
            employerId: '33333333-3333-4333-8333-333333333333',
            employerType: 'business',
            displayName: 'Golden Rose Business',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 7,
            updatedAt: '2026-08-11T03:00:00Z',
          }}
          onCanonicalReload={onCanonicalReload}
        />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Conflict Revision Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const conflictHeading = await screen.findByRole('heading', { name: 'Revision is blocked until current employer detail reloads' });
    const conflictRegion = conflictHeading.closest('section');
    expect(conflictRegion).not.toBeNull();
    expect(reviseEmployerMock).toHaveBeenCalledTimes(1);
    expect(reviseEmployerMock).toHaveBeenNthCalledWith(1, {
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '66666666-6666-4666-8666-666666666666',
      expectedVersion: 7,
      employerType: 'household',
      displayName: 'Conflict Revision Rose',
    });
    expect(screen.queryByLabelText('Revision employer type')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Revision employer name')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Save draft employer revision' })).not.toBeInTheDocument();
    expect(within(conflictRegion as HTMLElement).queryByRole('button', { name: 'Retry same revision attempt' })).not.toBeInTheDocument();

    await user.click(within(conflictRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));

    expect(onCanonicalReload).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('heading', { name: 'Revision is blocked until current employer detail reloads' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('releases stale command identity but blocks editing until canonical reload succeeds or returns terminal not-found', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    const onCanonicalReload = vi.fn().mockResolvedValue('success');

    reviseEmployerMock.mockReset();
    reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'stale' } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValue('77777777-7777-4777-8777-777777777777');

    render(
      <LanguageProvider>
        <EmployerRevisionForm
          detail={{
            employerId: '33333333-3333-4333-8333-333333333333',
            employerType: 'business',
            displayName: 'Golden Rose Business',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 7,
            updatedAt: '2026-08-11T03:00:00Z',
          }}
          onCanonicalReload={onCanonicalReload}
        />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Stale Revision Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const staleHeading = await screen.findByRole('heading', {
      name: 'Revision requires current employer detail before editing can continue',
    });
    const staleRegion = staleHeading.closest('section');
    expect(staleRegion).not.toBeNull();
    expect(reviseEmployerMock).toHaveBeenCalledTimes(1);
    expect(reviseEmployerMock).toHaveBeenNthCalledWith(1, {
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: '77777777-7777-4777-8777-777777777777',
      expectedVersion: 7,
      employerType: 'household',
      displayName: 'Stale Revision Rose',
    });
    expect(screen.getByLabelText('Revision employer type')).toBeDisabled();
    expect(screen.getByLabelText('Revision employer name')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Save draft employer revision' })).toBeDisabled();
    expect(within(staleRegion as HTMLElement).queryByRole('button', { name: 'Retry same revision attempt' })).not.toBeInTheDocument();

    await user.click(within(staleRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));

    expect(onCanonicalReload).toHaveBeenCalledTimes(1);
    expect(
      screen.queryByRole('heading', { name: 'Revision requires current employer detail before editing can continue' }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('keeps unknown authority when a non-not-found canonical reload fails', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    const onCanonicalReload = vi.fn().mockRejectedValue(new Error('reload failed'));

    reviseEmployerMock.mockReset();
    reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValue('88888888-8888-4888-8888-888888888888');

    render(
      <LanguageProvider>
        <EmployerRevisionForm
          detail={{
            employerId: '33333333-3333-4333-8333-333333333333',
            employerType: 'business',
            displayName: 'Golden Rose Business',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 7,
            updatedAt: '2026-08-11T03:00:00Z',
          }}
          onCanonicalReload={onCanonicalReload}
        />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Unknown Reload Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const unknownHeading = await screen.findByRole('heading', { name: 'Revision outcome is unknown' });
    const unknownRegion = unknownHeading.closest('section');
    expect(unknownRegion).not.toBeNull();
    expect(screen.queryByLabelText('Revision employer type')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Revision employer name')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Save draft employer revision' })).not.toBeInTheDocument();

    await user.click(within(unknownRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));

    expect(onCanonicalReload).toHaveBeenCalledTimes(1);
    expect(await screen.findByRole('heading', { name: 'Revision outcome is unknown' })).toBeInTheDocument();
    expect(within(unknownRegion as HTMLElement).getByRole('button', { name: 'Retry same revision attempt' })).toBeInTheDocument();
    expect(reviseEmployerMock).toHaveBeenCalledTimes(1);

    randomUuidSpy.mockRestore();
  });

  it('releases frozen authority after successful canonical reload or terminal canonical not-found', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    const onCanonicalReload = vi.fn().mockResolvedValueOnce('success').mockResolvedValueOnce('not_found');

    reviseEmployerMock.mockReset();
    reviseEmployerMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('99999999-9999-4999-8999-999999999999')
      .mockReturnValueOnce('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa');

    const detail = {
      employerId: '33333333-3333-4333-8333-333333333333',
      employerType: 'business' as const,
      displayName: 'Golden Rose Business',
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 7,
      updatedAt: '2026-08-11T03:00:00Z',
    };

    const { rerender } = render(
      <LanguageProvider>
        <EmployerRevisionForm detail={detail} onCanonicalReload={onCanonicalReload} />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Unknown Success Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const firstUnknownHeading = await screen.findByRole('heading', { name: 'Revision outcome is unknown' });
    const firstUnknownRegion = firstUnknownHeading.closest('section');
    expect(firstUnknownRegion).not.toBeNull();

    await user.click(within(firstUnknownRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));

    expect(onCanonicalReload).toHaveBeenNthCalledWith(1);
    expect(screen.queryByRole('heading', { name: 'Revision outcome is unknown' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();

    rerender(
      <LanguageProvider>
        <EmployerRevisionForm detail={detail} onCanonicalReload={onCanonicalReload} />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Unknown Not Found Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const secondUnknownHeading = await screen.findByRole('heading', { name: 'Revision outcome is unknown' });
    const secondUnknownRegion = secondUnknownHeading.closest('section');
    expect(secondUnknownRegion).not.toBeNull();

    await user.click(within(secondUnknownRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));

    expect(onCanonicalReload).toHaveBeenNthCalledWith(2);
    expect(screen.queryByRole('heading', { name: 'Revision outcome is unknown' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();
    expect(reviseEmployerMock).toHaveBeenCalledTimes(2);

    randomUuidSpy.mockRestore();
  });

  it('releases definitive validation or forbidden attempt and rotates key on corrected submit while ignoring late completion', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    const onRevisionSuccess = vi.fn();
    const lateSuccess = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    reviseEmployerMock.mockReset();
    reviseEmployerMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'validation' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'forbidden' } })
      .mockReturnValueOnce(lateSuccess.promise);

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('b1111111-1111-4111-8111-111111111111')
      .mockReturnValueOnce('b2222222-2222-4222-8222-222222222222')
      .mockReturnValueOnce('b3333333-3333-4333-8333-333333333333');

    const detail = {
      employerId: '33333333-3333-4333-8333-333333333333',
      employerType: 'business' as const,
      displayName: 'Golden Rose Business',
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 7,
      updatedAt: '2026-08-11T03:00:00Z',
    };

    const { rerender } = render(
      <LanguageProvider>
        <EmployerRevisionForm detail={detail} onRevisionSuccess={onRevisionSuccess} />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Validation Revision Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    expect(await screen.findByRole('heading', { name: 'Draft employer revision could not be completed' })).toBeInTheDocument();
    expect(screen.getByLabelText('Revision employer type')).toHaveValue('household');
    expect(screen.getByLabelText('Revision employer name')).toHaveValue('Validation Revision Rose');
    expect(reviseEmployerMock).toHaveBeenNthCalledWith(1, {
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: 'b1111111-1111-4111-8111-111111111111',
      expectedVersion: 7,
      employerType: 'household',
      displayName: 'Validation Revision Rose',
    });

    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Forbidden Revision Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    expect(
      await screen.findByRole('heading', { name: 'Draft employer revision is not available for this staff session' }),
    ).toBeInTheDocument();
    expect(reviseEmployerMock).toHaveBeenNthCalledWith(2, {
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: 'b2222222-2222-4222-8222-222222222222',
      expectedVersion: 7,
      employerType: 'household',
      displayName: 'Forbidden Revision Rose',
    });

    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Late Completion Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    expect(reviseEmployerMock).toHaveBeenNthCalledWith(3, {
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: 'b3333333-3333-4333-8333-333333333333',
      expectedVersion: 7,
      employerType: 'household',
      displayName: 'Late Completion Rose',
    });

    rerender(
      <LanguageProvider>
        <EmployerRevisionForm detail={detail} onRevisionSuccess={onRevisionSuccess} resetSignal={1} />
      </LanguageProvider>,
    );

    lateSuccess.resolve({
      ok: true,
      value: {
        detail: {
          employerId: '33333333-3333-4333-8333-333333333333',
          employerType: 'household',
          displayName: 'Late Completion Rose',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 8,
          updatedAt: '2026-08-11T03:30:00Z',
        },
        resultVersion: 8,
        replayed: false,
      },
    });
    await lateSuccess.promise;

    expect(onRevisionSuccess).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();
    expect(screen.queryByDisplayValue('Late Completion Rose')).not.toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('treats command not found as terminal and requires a new canonical selection', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);

    reviseEmployerMock.mockReset();
    reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'not_found' } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValue('c1111111-1111-4111-8111-111111111111');

    const firstDetail = {
      employerId: '33333333-3333-4333-8333-333333333333',
      employerType: 'business' as const,
      displayName: 'Golden Rose Business',
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 7,
      updatedAt: '2026-08-11T03:00:00Z',
    };

    const secondDetail = {
      employerId: '44444444-4444-4444-8444-444444444444',
      employerType: 'household' as const,
      displayName: 'Canonical Replacement Rose',
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 2,
      updatedAt: '2026-08-11T04:00:00Z',
    };

    const { rerender } = render(
      <LanguageProvider>
        <EmployerRevisionForm detail={firstDetail} />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Missing Revision Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    expect(
      await screen.findByRole('heading', { name: 'Draft employer revision target is no longer available' }),
    ).toBeInTheDocument();
    expect(screen.getByText('Select a current draft employer before starting another revision attempt.')).toBeInTheDocument();
    expect(screen.queryByLabelText('Revision employer type')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Edit draft employer' })).not.toBeInTheDocument();
    expect(screen.queryByDisplayValue('Missing Revision Rose')).not.toBeInTheDocument();

    rerender(
      <LanguageProvider>
        <EmployerRevisionForm detail={secondDetail} />
      </LanguageProvider>,
    );

    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    expect(screen.getByLabelText('Revision employer type')).toHaveValue('household');
    expect(screen.getByLabelText('Revision employer name')).toHaveValue('Canonical Replacement Rose');

    randomUuidSpy.mockRestore();
  });

  it('treats canonical reload not found as terminal rather than an indefinite frozen failure', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    const onCanonicalReload = vi.fn().mockResolvedValue('not_found');

    reviseEmployerMock.mockReset();
    reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'stale' } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValue('d1111111-1111-4111-8111-111111111111');

    const firstDetail = {
      employerId: '33333333-3333-4333-8333-333333333333',
      employerType: 'business' as const,
      displayName: 'Golden Rose Business',
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 7,
      updatedAt: '2026-08-11T03:00:00Z',
    };

    const secondDetail = {
      employerId: '55555555-5555-4555-8555-555555555555',
      employerType: 'business' as const,
      displayName: 'Reload Recovery Replacement',
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 3,
      updatedAt: '2026-08-11T05:00:00Z',
    };

    const { rerender } = render(
      <LanguageProvider>
        <EmployerRevisionForm detail={firstDetail} onCanonicalReload={onCanonicalReload} />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Reload Missing Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const staleHeading = await screen.findByRole('heading', {
      name: 'Revision requires current employer detail before editing can continue',
    });
    const staleRegion = staleHeading.closest('section');
    expect(staleRegion).not.toBeNull();

    await user.click(within(staleRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));

    expect(onCanonicalReload).toHaveBeenCalledTimes(1);
    expect(
      await screen.findByRole('heading', { name: 'Draft employer revision target is no longer available' }),
    ).toBeInTheDocument();
    expect(screen.getByText('Select a current draft employer before starting another revision attempt.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Edit draft employer' })).not.toBeInTheDocument();
    expect(
      screen.queryByRole('heading', { name: 'Revision requires current employer detail before editing can continue' }),
    ).not.toBeInTheDocument();

    rerender(
      <LanguageProvider>
        <EmployerRevisionForm detail={secondDetail} onCanonicalReload={onCanonicalReload} />
      </LanguageProvider>,
    );

    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('hides submitted values from disabled controls during unknown and conflict recovery', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);

    reviseEmployerMock.mockReset();
    reviseEmployerMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('e1111111-1111-4111-8111-111111111111')
      .mockReturnValueOnce('e2222222-2222-4222-8222-222222222222');

    const detail = {
      employerId: '33333333-3333-4333-8333-333333333333',
      employerType: 'business' as const,
      displayName: 'Golden Rose Business' as const,
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 7,
      updatedAt: '2026-08-11T03:00:00Z',
    };

    const { rerender } = render(
      <LanguageProvider>
        <EmployerRevisionForm detail={detail} />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Unknown Hidden Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    expect(await screen.findByRole('heading', { name: 'Revision outcome is unknown' })).toBeInTheDocument();
    expect(screen.queryByLabelText('Revision employer type')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Revision employer name')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Save draft employer revision' })).not.toBeInTheDocument();
    expect(screen.queryByDisplayValue('Unknown Hidden Rose')).not.toBeInTheDocument();

    rerender(
      <LanguageProvider>
        <EmployerRevisionForm detail={detail} resetSignal={1} />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Conflict Hidden Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    expect(
      await screen.findByRole('heading', { name: 'Revision is blocked until current employer detail reloads' }),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText('Revision employer type')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Revision employer name')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Save draft employer revision' })).not.toBeInTheDocument();
    expect(screen.queryByDisplayValue('Conflict Hidden Rose')).not.toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('ignores late completion after pagehide reset or unmount', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    const onRevisionSuccess = vi.fn();
    const latePagehideSuccess = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();
    const lateUnmountSuccess = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    reviseEmployerMock.mockReset();
    reviseEmployerMock.mockReturnValueOnce(latePagehideSuccess.promise).mockReturnValueOnce(lateUnmountSuccess.promise);

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('f1111111-1111-4111-8111-111111111111')
      .mockReturnValueOnce('f2222222-2222-4222-8222-222222222222');

    const detail = {
      employerId: '33333333-3333-4333-8333-333333333333',
      employerType: 'business' as const,
      displayName: 'Golden Rose Business' as const,
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 7,
      updatedAt: '2026-08-11T03:00:00Z',
    };

    const { rerender, unmount } = render(
      <LanguageProvider>
        <EmployerRevisionForm detail={detail} onRevisionSuccess={onRevisionSuccess} />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Pagehide Late Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    act(() => {
      window.dispatchEvent(new Event('pagehide'));
    });

    rerender(
      <LanguageProvider>
        <EmployerRevisionForm detail={detail} onRevisionSuccess={onRevisionSuccess} resetSignal={1} />
      </LanguageProvider>,
    );

    await act(async () => {
      latePagehideSuccess.resolve({
        ok: true,
        value: {
          detail: {
            employerId: '33333333-3333-4333-8333-333333333333',
            employerType: 'household',
            displayName: 'Pagehide Late Rose',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T03:30:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });
      await latePagehideSuccess.promise;
    });

    expect(onRevisionSuccess).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();
    expect(screen.queryByDisplayValue('Pagehide Late Rose')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Unmount Late Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    unmount();

    await act(async () => {
      lateUnmountSuccess.resolve({
        ok: true,
        value: {
          detail: {
            employerId: '33333333-3333-4333-8333-333333333333',
            employerType: 'household',
            displayName: 'Unmount Late Rose',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T03:45:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });
      await lateUnmountSuccess.promise;
    });

    expect(onRevisionSuccess).not.toHaveBeenCalled();

    randomUuidSpy.mockRestore();
  });

  it('blocks competing controls and warns before unload while authority is pending or unknown', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    const onAuthorityChange = vi.fn();
    const deferredRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    reviseEmployerMock.mockReset();
    reviseEmployerMock.mockReturnValueOnce(deferredRevision.promise);

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValue('abababab-abab-4bab-8bab-abababababab');

    const detail = {
      employerId: '33333333-3333-4333-8333-333333333333',
      employerType: 'business' as const,
      displayName: 'Golden Rose Business' as const,
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 7,
      updatedAt: '2026-08-11T03:00:00Z',
    };

    const { rerender } = render(
      <LanguageProvider>
        <EmployerRevisionForm detail={detail} onAuthorityChange={onAuthorityChange} />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Pending Unknown Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    expect(onAuthorityChange).toHaveBeenNthCalledWith(1, { owner: 'revision', locked: true });
    expect(screen.getByLabelText('Revision employer type')).toBeDisabled();
    expect(screen.getByLabelText('Revision employer name')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Save draft employer revision' })).toBeDisabled();

    const pendingBeforeUnload = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(pendingBeforeUnload);
    expect(pendingBeforeUnload.defaultPrevented).toBe(true);

    await act(async () => {
      deferredRevision.resolve({ ok: false, failure: { kind: 'unknown_outcome' } });
      await deferredRevision.promise;
    });

    expect(await screen.findByRole('heading', { name: 'Revision outcome is unknown' })).toBeInTheDocument();
    expect(onAuthorityChange).toHaveBeenCalledTimes(1);

    const unknownBeforeUnload = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(unknownBeforeUnload);
    expect(unknownBeforeUnload.defaultPrevented).toBe(true);

    rerender(
      <LanguageProvider>
        <EmployerRevisionForm detail={detail} onAuthorityChange={onAuthorityChange} resetSignal={1} />
      </LanguageProvider>,
    );

    expect(onAuthorityChange).toHaveBeenNthCalledWith(2, { owner: null, locked: false });
    const releasedBeforeUnload = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(releasedBeforeUnload);
    expect(releasedBeforeUnload.defaultPrevented).toBe(false);

    randomUuidSpy.mockRestore();
  });

  it('serializes repeated retry reload and cross-action same-tick activations in recovery', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    const deferredRetry = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();
    const deferredConflictReload = createDeferredPromise<void | 'success' | 'not_found'>();
    const onCanonicalReload = vi.fn().mockReturnValueOnce(deferredConflictReload.promise);

    reviseEmployerMock.mockReset();
    reviseEmployerMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } })
      .mockReturnValueOnce(deferredRetry.promise)
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('cdcdcdcd-cdcd-4dcd-8dcd-cdcdcdcdcdcd')
      .mockReturnValueOnce('dededede-dede-4ede-8ede-dededededede');

    const detail = {
      employerId: '33333333-3333-4333-8333-333333333333',
      employerType: 'business' as const,
      displayName: 'Golden Rose Business' as const,
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 7,
      updatedAt: '2026-08-11T03:00:00Z',
    };

    const { rerender } = render(
      <LanguageProvider>
        <EmployerRevisionForm detail={detail} onCanonicalReload={onCanonicalReload} />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Serialized Unknown Revision');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const unknownHeading = await screen.findByRole('heading', { name: 'Revision outcome is unknown' });
    const unknownRegion = unknownHeading.closest('section');
    expect(unknownRegion).not.toBeNull();

    const retryButton = within(unknownRegion as HTMLElement).getByRole('button', {
      name: 'Retry same revision attempt',
    });
    const unknownReloadButton = within(unknownRegion as HTMLElement).getByRole('button', {
      name: 'Reload current employer detail',
    });

    fireEvent.click(retryButton);
    fireEvent.click(retryButton);
    fireEvent.click(unknownReloadButton);

    expect(reviseEmployerMock).toHaveBeenCalledTimes(2);
    expect(reviseEmployerMock).toHaveBeenNthCalledWith(2, {
      employerId: '33333333-3333-4333-8333-333333333333',
      commandId: 'cdcdcdcd-cdcd-4dcd-8dcd-cdcdcdcdcdcd',
      expectedVersion: 7,
      employerType: 'household',
      displayName: 'Serialized Unknown Revision',
    });
    expect(onCanonicalReload).not.toHaveBeenCalled();
    expect(retryButton).toBeDisabled();
    expect(unknownReloadButton).toBeDisabled();

    await act(async () => {
      deferredRetry.resolve({
        ok: true,
        value: {
          detail: {
            employerId: '33333333-3333-4333-8333-333333333333',
            employerType: 'household',
            displayName: 'Serialized Unknown Revision',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T03:30:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });
      await deferredRetry.promise;
    });

    rerender(
      <LanguageProvider>
        <EmployerRevisionForm detail={detail} onCanonicalReload={onCanonicalReload} resetSignal={1} />
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Serialized Conflict Revision');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const conflictHeading = await screen.findByRole('heading', { name: 'Revision is blocked until current employer detail reloads' });
    const conflictRegion = conflictHeading.closest('section');
    expect(conflictRegion).not.toBeNull();

    const conflictReloadButton = within(conflictRegion as HTMLElement).getByRole('button', {
      name: 'Reload current employer detail',
    });

    fireEvent.click(conflictReloadButton);
    fireEvent.click(conflictReloadButton);

    expect(onCanonicalReload).toHaveBeenCalledTimes(1);
    expect(conflictReloadButton).toBeDisabled();

    await act(async () => {
      deferredConflictReload.resolve(undefined);
      await deferredConflictReload.promise;
    });

    randomUuidSpy.mockRestore();
  });

  it('announces and focuses every revision transition with reduced-motion-safe behavior', async () => {
    const user = userEvent.setup();
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    const unknownRefreshFailure = new Error('reload failed');
    const originalMatchMedia = window.matchMedia;

    Object.defineProperty(window, 'matchMedia', {
      configurable: true,
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: query === '(prefers-reduced-motion: reduce)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    reviseEmployerMock.mockReset();
    reviseEmployerMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'validation' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'forbidden' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'stale' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'not_found' } })
      .mockResolvedValueOnce({
        ok: true,
        value: {
          detail: {
            employerId: '33333333-3333-4333-8333-333333333333',
            employerType: 'household',
            displayName: 'Focused Success Rose',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T03:30:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('10101010-1010-4010-8010-101010101010')
      .mockReturnValueOnce('20202020-2020-4020-8020-202020202020')
      .mockReturnValueOnce('30303030-3030-4030-8030-303030303030')
      .mockReturnValueOnce('40404040-4040-4040-8040-404040404040')
      .mockReturnValueOnce('50505050-5050-4050-8050-505050505050')
      .mockReturnValueOnce('60606060-6060-4060-8060-606060606060')
      .mockReturnValueOnce('70707070-7070-4070-8070-707070707070');

    const detail = {
      employerId: '33333333-3333-4333-8333-333333333333',
      employerType: 'business' as const,
      displayName: 'Golden Rose Business' as const,
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 7,
      updatedAt: '2026-08-11T03:00:00Z',
    };

    try {
      const { rerender } = render(
        <LanguageProvider>
          <EmployerRevisionForm detail={detail} onCanonicalReload={vi.fn().mockRejectedValue(unknownRefreshFailure)} />
        </LanguageProvider>,
      );

      await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
      await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
      await user.clear(screen.getByLabelText('Revision employer name'));
      await user.type(screen.getByLabelText('Revision employer name'), 'Focused Validation Rose');
      await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));
      expect(await screen.findByRole('heading', { name: 'Draft employer revision could not be completed' })).toHaveFocus();
      expect(screen.getByRole('alert')).toBeInTheDocument();

      await user.clear(screen.getByLabelText('Revision employer name'));
      await user.type(screen.getByLabelText('Revision employer name'), 'Focused Forbidden Rose');
      await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));
      expect(
        await screen.findByRole('heading', { name: 'Draft employer revision is not available for this staff session' }),
      ).toHaveFocus();

      await user.clear(screen.getByLabelText('Revision employer name'));
      await user.type(screen.getByLabelText('Revision employer name'), 'Focused Unknown Rose');
      await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));
      const unknownHeading = await screen.findByRole('heading', { name: 'Revision outcome is unknown' });
      expect(unknownHeading).toHaveFocus();

      const unknownRegion = unknownHeading.closest('section');
      expect(unknownRegion).not.toBeNull();
      await user.click(within(unknownRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));
      expect(await screen.findByRole('heading', { name: 'Current employer detail could not be refreshed' })).toHaveFocus();
      expect(screen.getByRole('heading', { name: 'Revision outcome is unknown' })).toBeInTheDocument();

      rerender(
        <LanguageProvider>
          <EmployerRevisionForm detail={detail} onCanonicalReload={vi.fn().mockResolvedValue(undefined)} resetSignal={1} />
        </LanguageProvider>,
      );

      await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
      await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
      await user.clear(screen.getByLabelText('Revision employer name'));
      await user.type(screen.getByLabelText('Revision employer name'), 'Focused Conflict Rose');
      await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));
      expect(
        await screen.findByRole('heading', { name: 'Revision is blocked until current employer detail reloads' }),
      ).toHaveFocus();

      rerender(
        <LanguageProvider>
          <EmployerRevisionForm detail={detail} onCanonicalReload={vi.fn().mockResolvedValue(undefined)} resetSignal={2} />
        </LanguageProvider>,
      );

      await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
      await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
      await user.clear(screen.getByLabelText('Revision employer name'));
      await user.type(screen.getByLabelText('Revision employer name'), 'Focused Stale Rose');
      await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));
      expect(
        await screen.findByRole('heading', { name: 'Revision requires current employer detail before editing can continue' }),
      ).toHaveFocus();

      rerender(
        <LanguageProvider>
          <EmployerRevisionForm detail={detail} resetSignal={3} />
        </LanguageProvider>,
      );

      await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
      await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
      await user.clear(screen.getByLabelText('Revision employer name'));
      await user.type(screen.getByLabelText('Revision employer name'), 'Focused Not Found Rose');
      await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));
      expect(await screen.findByRole('heading', { name: 'Draft employer revision target is no longer available' })).toHaveFocus();

      rerender(
        <LanguageProvider>
          <EmployerRevisionForm detail={detail} resetSignal={4} />
        </LanguageProvider>,
      );

      await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
      await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
      await user.clear(screen.getByLabelText('Revision employer name'));
      await user.type(screen.getByLabelText('Revision employer name'), 'Focused Success Rose');
      await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));
      expect(await screen.findByRole('heading', { name: 'Draft employer revision saved' })).toHaveFocus();
    } finally {
      randomUuidSpy.mockRestore();
      Object.defineProperty(window, 'matchMedia', {
        configurable: true,
        writable: true,
        value: originalMatchMedia,
      });
    }
  });

  describe('passes axe in both locales across every revision and recovery state', () => {
    const detail = {
      employerId: '33333333-3333-4333-8333-333333333333',
      employerType: 'business' as const,
      displayName: 'Golden Rose Business' as const,
      lifecycleStatus: 'draft' as const,
      sourceChannel: 'staff_entry' as const,
      version: 7,
      updatedAt: '2026-08-11T03:00:00Z',
    };

    async function assertEnglishSpanishAxeState(
      user: ReturnType<typeof userEvent.setup>,
      trigger: () => Promise<void>,
      englishAssertion: () => Promise<void>,
      spanishAssertion: () => Promise<void>,
      options?: { onCanonicalReload?: () => void | 'success' | 'not_found' | Promise<void | 'success' | 'not_found'> },
    ) {
      const view = render(
        <LanguageProvider>
          <RevisionFormLocaleHarness>
            <EmployerRevisionForm detail={detail} onCanonicalReload={options?.onCanonicalReload} />
          </RevisionFormLocaleHarness>
        </LanguageProvider>,
      );

      await trigger();
      await englishAssertion();
      expect(await runAxe(view.container)).toEqual([]);

      await user.click(screen.getByRole('button', { name: 'Cambiar a español' }));
      await spanishAssertion();
      expect(await runAxe(view.container)).toEqual([]);

      view.unmount();
    }

    async function openAndSubmit(user: ReturnType<typeof userEvent.setup>, name: string) {
      await user.click(screen.getByRole('button', { name: /Edit draft employer|Editar empleador en borrador/ }));
      await user.selectOptions(
        await screen.findByLabelText(/Revision employer type|Tipo de empleador para la revisión/),
        'household',
      );
      const revisionNameInput = await screen.findByLabelText(/Revision employer name|Nombre del empleador para la revisión/);
      await user.clear(revisionNameInput);
      await user.type(revisionNameInput, name);
      await user.click(screen.getByRole('button', { name: /Save draft employer revision|Guardar revisión del empleador en borrador/ }));
    }

    it('covers the editing state', async () => {
      const user = userEvent.setup();
      await assertEnglishSpanishAxeState(
        user,
        async () => {
          await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
        },
        async () => {
          expect(await screen.findByLabelText('Revision employer type')).toBeInTheDocument();
          expect(await screen.findByLabelText('Revision employer name')).toBeInTheDocument();
        },
        async () => {
          expect(await screen.findByLabelText('Tipo de empleador para la revisión')).toBeInTheDocument();
          expect(await screen.findByLabelText('Nombre del empleador para la revisión')).toBeInTheDocument();
        },
      );
    });

    it('covers the client validation failure state', async () => {
      const user = userEvent.setup();
      const reviseEmployerMock = vi.mocked(reviseEmployer);
      reviseEmployerMock.mockReset();

      await assertEnglishSpanishAxeState(
        user,
        async () => {
          await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
          const revisionNameInput = await screen.findByLabelText('Revision employer name');
          await user.clear(revisionNameInput);
          await user.type(revisionNameInput, '   ');
          await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));
        },
        async () => {
          expect(await screen.findByRole('alert')).toHaveTextContent('Enter 1 to 200 visible characters for the employer name.');
        },
        async () => {
          expect(await screen.findByRole('alert')).toHaveTextContent(
            'Ingrese entre 1 y 200 caracteres visibles para el nombre del empleador.',
          );
        },
      );
    });

    it('covers the pending state', async () => {
      const user = userEvent.setup();
      const reviseEmployerMock = vi.mocked(reviseEmployer);
      reviseEmployerMock.mockReset();
      const pendingRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();
      reviseEmployerMock.mockReturnValueOnce(pendingRevision.promise);

      await assertEnglishSpanishAxeState(
        user,
        async () => {
          await openAndSubmit(user, 'Pending Axe Rose');
        },
        async () => {
          expect(screen.getByLabelText('Revision employer type')).toBeDisabled();
          expect(screen.getByLabelText('Revision employer name')).toBeDisabled();
          expect(screen.getByRole('button', { name: 'Save draft employer revision' })).toBeDisabled();
        },
        async () => {
          expect(screen.getByLabelText('Tipo de empleador para la revisión')).toBeDisabled();
          expect(screen.getByLabelText('Nombre del empleador para la revisión')).toBeDisabled();
          expect(screen.getByRole('button', { name: 'Guardar revisión del empleador en borrador' })).toBeDisabled();
        },
      );
      pendingRevision.resolve({ ok: false, failure: { kind: 'unknown_outcome' } });
    });

    it('covers validation and forbidden server-failure states', async () => {
      const user = userEvent.setup();
      const reviseEmployerMock = vi.mocked(reviseEmployer);

      reviseEmployerMock.mockReset();
      reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'validation' } });
      await assertEnglishSpanishAxeState(
        user,
        async () => {
          await openAndSubmit(user, 'Validation Axe Rose');
        },
        async () => {
          await screen.findByRole('heading', { name: 'Draft employer revision could not be completed' });
        },
        async () => {
          await screen.findByRole('heading', { name: 'No se pudo completar la revisión del empleador en borrador' });
        },
      );

      reviseEmployerMock.mockReset();
      reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'forbidden' } });
      await assertEnglishSpanishAxeState(
        user,
        async () => {
          await openAndSubmit(user, 'Forbidden Axe Rose');
        },
        async () => {
          await screen.findByRole('heading', { name: 'Draft employer revision is not available for this staff session' });
        },
        async () => {
          await screen.findByRole('heading', { name: 'La revisión del empleador en borrador no está disponible para esta sesión del personal' });
        },
      );
    });

    it('covers unknown conflict stale and not-found recovery states', async () => {
      const user = userEvent.setup();
      const reviseEmployerMock = vi.mocked(reviseEmployer);

      reviseEmployerMock.mockReset();
      reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } });
      await assertEnglishSpanishAxeState(
        user,
        async () => {
          await openAndSubmit(user, 'Unknown Axe Rose');
        },
        async () => {
          await screen.findByRole('heading', { name: 'Revision outcome is unknown' });
        },
        async () => {
          await screen.findByRole('heading', { name: 'El resultado de la revisión es desconocido' });
        },
      );

      reviseEmployerMock.mockReset();
      reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } });
      await assertEnglishSpanishAxeState(
        user,
        async () => {
          await openAndSubmit(user, 'Conflict Axe Rose');
        },
        async () => {
          await screen.findByRole('heading', { name: 'Revision is blocked until current employer detail reloads' });
        },
        async () => {
          await screen.findByRole('heading', { name: 'La revisión está bloqueada hasta que se recargue el detalle actual del empleador' });
        },
      );

      reviseEmployerMock.mockReset();
      reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'stale' } });
      await assertEnglishSpanishAxeState(
        user,
        async () => {
          await openAndSubmit(user, 'Stale Axe Rose');
        },
        async () => {
          await screen.findByRole('heading', { name: 'Revision requires current employer detail before editing can continue' });
        },
        async () => {
          await screen.findByRole('heading', {
            name: 'La revisión requiere el detalle actual del empleador antes de que la edición pueda continuar',
          });
        },
      );

      reviseEmployerMock.mockReset();
      reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'not_found' } });
      await assertEnglishSpanishAxeState(
        user,
        async () => {
          await openAndSubmit(user, 'Not Found Axe Rose');
        },
        async () => {
          await screen.findByRole('heading', { name: 'Draft employer revision target is no longer available' });
        },
        async () => {
          await screen.findByRole('heading', { name: 'El objetivo de la revisión del empleador en borrador ya no está disponible' });
        },
      );
    });

    it('covers refresh-failure and success states', async () => {
      const user = userEvent.setup();
      const reviseEmployerMock = vi.mocked(reviseEmployer);

      reviseEmployerMock.mockReset();
      reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } });
      await assertEnglishSpanishAxeState(
        user,
        async () => {
          await openAndSubmit(user, 'Refresh Failure Axe Rose');
          const unknownRegion = (await screen.findByRole('heading', { name: 'Revision outcome is unknown' })).closest('section');
          expect(unknownRegion).not.toBeNull();
          await user.click(within(unknownRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));
        },
        async () => {
          await screen.findByRole('heading', { name: 'Current employer detail could not be refreshed' });
        },
        async () => {
          await screen.findByRole('heading', { name: 'No se pudo actualizar el detalle actual del empleador' });
        },
        { onCanonicalReload: vi.fn().mockRejectedValue(new Error('reload failed')) },
      );

      reviseEmployerMock.mockReset();
      reviseEmployerMock.mockResolvedValueOnce({
        ok: true,
        value: {
          detail: {
            employerId: '33333333-3333-4333-8333-333333333333',
            employerType: 'household',
            displayName: 'Success Axe Rose',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T03:30:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });
      await assertEnglishSpanishAxeState(
        user,
        async () => {
          await openAndSubmit(user, 'Success Axe Rose');
        },
        async () => {
          await screen.findByRole('heading', { name: 'Draft employer revision saved' });
        },
        async () => {
          await screen.findByRole('heading', { name: 'La revisión del empleador en borrador se guardó' });
        },
      );
    });
  });
});
