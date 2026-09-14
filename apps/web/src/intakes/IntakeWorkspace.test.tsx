import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AppRoutes } from '../app/App';
import { LanguageProvider } from '../i18n/LanguageProvider';
import * as api from '../api/intakeClient';
import type { IntakeDetail, IntakeCommandResult, Result, AddressDetail } from '../api/intakeContracts';
import { runAxe } from '../test/axe';
vi.mock('../api/intakeClient');
const id = 'bda61d25-4021-4d8a-9f5d-9b77ad6c351f';
const detail = (version = 1, name = 'Fictional Person'): IntakeDetail => ({
  summary: {
    intake_id: id,
    kind: 'worker',
    version,
    lifecycle: 'draft',
    display_name: name,
    complete: false,
    missing_fields: ['phone'],
    review_status: 'unreviewed',
    updated_at: '2026-09-14T12:00:00Z',
  },
  content_version: version,
  candidate: { full_name: name },
  resolved: {},
  links: {},
  dependency_stale: false,
});
function mount(path = '/staff/intakes/workers') {
  return render(
    <LanguageProvider>
      <MemoryRouter initialEntries={[path]}>
        <AppRoutes />
      </MemoryRouter>
    </LanguageProvider>,
  );
}
function deferred<T>() {
  let resolve: (value: T) => void = () => {
    throw new Error('Resolver unavailable');
  };
  const promise = new Promise<T>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}
beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.queryIntakes).mockResolvedValue({ ok: true, value: { items: [], next_cursor: null } });
  vi.mocked(api.getIntake).mockResolvedValue({ ok: true, value: detail() });
  vi.mocked(api.getIntakeAddress).mockResolvedValue({
    ok: true,
    value: { intake_id: id, version: 1, section: 'worker_residence', candidate: null, resolved: null },
  });
  vi.mocked(api.saveIntake).mockImplementation((command) =>
    Promise.resolve({
      ok: true,
      value: { command_id: command.key, result_record_version: 1, current: detail() },
    }),
  );
  vi.spyOn(window, 'confirm').mockReturnValue(true);
});
afterEach(() => vi.restoreAllMocks());
describe('staff intake drafts', () => {
  it('saves partial intake and reopens authoritative version', async () => {
    const view = mount();
    fireEvent.click(screen.getByRole('button', { name: 'New intake' }));
    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Fictional Person' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save details' }));
    await screen.findByText('All changes saved');
    expect(api.saveIntake).toHaveBeenCalledWith(
      expect.objectContaining({ body: { kind: 'worker', content: { full_name: 'Fictional Person' } } }),
    );
    view.unmount();
    vi.mocked(api.getIntake).mockResolvedValue({ ok: true, value: detail(4, 'Authoritative name') });
    vi.mocked(api.getIntakeAddress).mockResolvedValue({
      ok: true,
      value: { intake_id: id, version: 4, section: 'worker_residence', candidate: null, resolved: null },
    });
    mount(`/staff/intakes/${id}`);
    await screen.findByDisplayValue('Authoritative name');
    expect(screen.getByText(/Version 4/)).toBeInTheDocument();
  });
  it('keeps later edits unsaved after pending save', async () => {
    const pending = deferred<Result<IntakeCommandResult>>();
    vi.mocked(api.saveIntake).mockReturnValue(pending.promise);
    mount();
    fireEvent.click(screen.getByRole('button', { name: 'New intake' }));
    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Submitted' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save details' }));
    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Later edit' } });
    await act(async () => {
      pending.resolve({
        ok: true,
        value: { command_id: 'key', result_record_version: 1, current: detail() },
      });
      await pending.promise;
    });
    expect(screen.getByLabelText('Full name')).toHaveValue('Later edit');
    expect(screen.queryByText('All changes saved')).not.toBeInTheDocument();
  });
  it('warns before abandoning unsaved changes', () => {
    mount();
    fireEvent.click(screen.getByRole('button', { name: 'New intake' }));
    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Unsaved' } });
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false);
    fireEvent.click(screen.getByRole('link', { name: 'Employers' }));
    expect(confirm).toHaveBeenCalled();
    expect(screen.getByLabelText('Full name')).toHaveValue('Unsaved');
    const event = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  });
  it('retries unknown saves with original command identity', async () => {
    vi.mocked(api.saveIntake).mockResolvedValueOnce({ ok: false, failure: 'unknown' });
    mount();
    fireEvent.click(screen.getByRole('button', { name: 'New intake' }));
    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Original' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save details' }));
    await screen.findByRole('button', { name: 'Retry original save' });
    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Later' } });
    fireEvent.click(screen.getByRole('button', { name: 'Retry original save' }));
    await waitFor(() => {
      expect(api.saveIntake).toHaveBeenCalledTimes(2);
    });
    expect(vi.mocked(api.saveIntake).mock.calls.at(0)?.[0]).toBe(
      vi.mocked(api.saveIntake).mock.calls.at(1)?.[0],
    );
    expect(screen.getByLabelText('Full name')).toHaveValue('Later');
  });
  it('keeps aggregate unsaved after one section succeeds and next unknown with later edits', async () => {
    mount(`/staff/intakes/${id}`);
    await screen.findByLabelText('Address line 1');
    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Changed' } });
    fireEvent.change(screen.getByLabelText('Address line 1'), { target: { value: 'Address A' } });
    vi.mocked(api.saveIntake).mockResolvedValueOnce({
      ok: true,
      value: { command_id: 'key', result_record_version: 2, current: detail(2, 'Changed') },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save details' }));
    await waitFor(() => {
      expect(screen.getByText(/Version 2/)).toBeInTheDocument();
    });
    expect(screen.getByLabelText('Address line 1')).toHaveValue('Address A');
    expect(screen.queryByText('All changes saved')).not.toBeInTheDocument();
    vi.mocked(api.saveIntake).mockResolvedValueOnce({ ok: false, failure: 'unknown' });
    fireEvent.click(screen.getByRole('button', { name: 'Save address: Residential address' }));
    await screen.findByRole('button', { name: 'Retry original save' });
    fireEvent.change(screen.getByLabelText('Address line 1'), { target: { value: 'Address B' } });
    expect(screen.queryByText('All changes saved')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Save details' })).toBeDisabled();
    expect(vi.mocked(api.saveIntake).mock.calls.at(1)?.[0].body).toEqual({
      expected_version: 2,
      address: { line1: 'Address A' },
    });
  });
  it('denied restricted sections do not claim an absent or saved address', async () => {
    vi.mocked(api.getIntakeAddress).mockResolvedValue({ ok: false, failure: 'forbidden' });
    mount(`/staff/intakes/${id}`);
    await screen.findByText('Section unavailable. Values are not shown.');
    expect(screen.queryByLabelText('Address line 1')).not.toBeInTheDocument();
    expect(screen.queryByText('All changes saved')).not.toBeInTheDocument();
  });
  it('renders bilingual accessible employer fields and preserves section-local values on language change', async () => {
    const view = mount('/staff/intakes/employers');
    await screen.findByText('No drafts found.');
    fireEvent.click(screen.getByRole('button', { name: 'New intake' }));
    fireEvent.change(screen.getByLabelText('Employer name'), { target: { value: 'Fictional Employer' } });
    expect(await runAxe(view.container)).toEqual([]);
    fireEvent.click(screen.getByRole('button', { name: 'Cambiar a español' }));
    expect(screen.getByLabelText('Nombre del empleador')).toHaveValue('Fictional Employer');
    expect(screen.getByRole('button', { name: 'Guardar datos' })).toBeInTheDocument();
    expect(await runAxe(view.container)).toEqual([]);
  }, 15000);
  it('loads bounded shared drafts and ignores late results after selecting a record', async () => {
    vi.mocked(api.queryIntakes).mockResolvedValue({
      ok: true,
      value: { items: [detail().summary], next_cursor: 'next' },
    });
    mount();
    fireEvent.click(await screen.findByRole('link', { name: `Resume: Fictional Person — ${id}` }));
    await screen.findByDisplayValue('Fictional Person');
    expect(api.queryIntakes).toHaveBeenCalledWith('worker');
  });
  it('shows conflicts and requires reopening before a new save', async () => {
    mount(`/staff/intakes/${id}`);
    await screen.findByLabelText('Full name');
    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Conflict' } });
    vi.mocked(api.saveIntake).mockResolvedValue({ ok: false, failure: 'conflict' });
    fireEvent.click(screen.getByRole('button', { name: 'Save details' }));
    await screen.findByRole('alert');
    expect(screen.getByRole('button', { name: 'Save details' })).toBeDisabled();
  });
  it('removes all in-memory form values on pagehide', async () => {
    mount(`/staff/intakes/${id}`);
    await screen.findByLabelText('Full name');
    act(() => {
      window.dispatchEvent(new Event('pagehide'));
    });
    expect(screen.queryByDisplayValue('Fictional Person')).not.toBeInTheDocument();
  });
  it('saves an address and refetches its authorized current section', async () => {
    mount(`/staff/intakes/${id}`);
    await screen.findByLabelText('Address line 1');
    fireEvent.change(screen.getByLabelText('Address line 1'), { target: { value: 'Fictional Street' } });
    vi.mocked(api.saveIntake).mockResolvedValue({
      ok: true,
      value: { command_id: 'key', result_record_version: 2, current: detail(2) },
    });
    vi.mocked(api.getIntakeAddress).mockResolvedValue({
      ok: true,
      value: {
        intake_id: id,
        version: 2,
        section: 'worker_residence',
        candidate: { line1: 'Fictional Street' },
        resolved: null,
      },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save address: Residential address' }));
    await screen.findByText('All changes saved');
    expect(
      within(screen.getByRole('group', { name: 'Residential address' })).getByLabelText('Address line 1'),
    ).toHaveValue('Fictional Street');
  });
  it('keeps submitted filters bound to pagination and accepts an exact reference', async () => {
    vi.mocked(api.queryIntakes).mockResolvedValue({
      ok: true,
      value: { items: [detail().summary], next_cursor: 'cursor' },
    });
    mount();
    await screen.findByRole('button', { name: 'Next page' });
    fireEvent.change(screen.getByLabelText('Name (at least 2 characters)'), {
      target: { value: 'First query' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Search drafts' }));
    await waitFor(() => {
      expect(api.queryIntakes).toHaveBeenLastCalledWith('worker', { name_query: 'First query' });
    });
    fireEvent.change(screen.getByLabelText('Name (at least 2 characters)'), {
      target: { value: 'Later input' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }));
    await waitFor(() => {
      expect(api.queryIntakes).toHaveBeenLastCalledWith('worker', {
        name_query: 'First query',
        cursor: 'cursor',
      });
    });
    fireEvent.click(screen.getByRole('checkbox', { name: 'Exact intake reference' }));
    fireEvent.change(screen.getByRole('textbox'), { target: { value: id } });
    fireEvent.click(screen.getByRole('button', { name: 'Search drafts' }));
    await waitFor(() => {
      expect(api.queryIntakes).toHaveBeenLastCalledWith('worker', { reference: id });
    });
  });
  it('retains edits made during an address save when its current section must be reloaded', async () => {
    mount(`/staff/intakes/${id}`);
    await screen.findByLabelText('Address line 1');
    const pending = deferred<Result<IntakeCommandResult>>();
    vi.mocked(api.saveIntake).mockReturnValue(pending.promise);
    fireEvent.change(screen.getByLabelText('Address line 1'), { target: { value: 'Submitted address' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save address: Residential address' }));
    fireEvent.change(screen.getByLabelText('Address line 1'), { target: { value: 'Later address' } });
    vi.mocked(api.getIntakeAddress).mockResolvedValue({ ok: false, failure: 'failed' });
    await act(async () => {
      pending.resolve({
        ok: true,
        value: { command_id: 'key', result_record_version: 2, current: detail(2) },
      });
      await pending.promise;
    });
    await screen.findByText(
      'Saved; current section could not be loaded. Reload this section before saving again.',
    );
    expect(screen.getByRole('button', { name: 'Save address: Residential address' })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: 'Load restricted section' }));
    await waitFor(() => {
      expect(screen.getByLabelText('Address line 1')).toHaveValue('Later address');
    });
    vi.mocked(api.getIntakeAddress).mockResolvedValue({
      ok: true,
      value: {
        intake_id: id,
        version: 2,
        section: 'worker_residence',
        candidate: { line1: 'Submitted address' },
        resolved: null,
      },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Load restricted section' }));
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Save address: Residential address' })).toBeEnabled();
    });
    expect(screen.getByLabelText('Address line 1')).toHaveValue('Later address');
    expect(screen.queryByText('All changes saved')).not.toBeInTheDocument();
  });
  it('copies an authorized employer address once without synchronizing later edits', async () => {
    const employer = detail();
    employer.summary.kind = 'employer';
    employer.candidate = { display_name: 'Fictional Employer' };
    vi.mocked(api.getIntake).mockResolvedValue({ ok: true, value: employer });
    vi.mocked(api.getIntakeAddress).mockImplementation((_id, section) =>
      Promise.resolve({
        ok: true,
        value: { intake_id: id, version: 1, section, candidate: null, resolved: null },
      }),
    );
    mount(`/staff/intakes/${id}`);
    await screen.findByRole('button', { name: 'Copy contact / business address once' });
    const party = within(screen.getByRole('group', { name: 'Contact / business address' }));
    const worksite = within(screen.getByRole('group', { name: 'Worksite address' }));
    fireEvent.change(party.getByLabelText('Address line 1'), { target: { value: 'Copy me' } });
    fireEvent.click(screen.getByRole('button', { name: 'Copy contact / business address once' }));
    fireEvent.change(party.getByLabelText('Address line 1'), { target: { value: 'Later party' } });
    expect(worksite.getByLabelText('Address line 1')).toHaveValue('Copy me');
    expect(screen.getByRole('link', { name: 'Back to drafts' })).toHaveAttribute(
      'href',
      '/staff/intakes/employers',
    );
  });
  it('admits only one restricted reload and preserves edits made while it is pending', async () => {
    vi.mocked(api.getIntakeAddress).mockResolvedValue({ ok: false, failure: 'forbidden' });
    mount(`/staff/intakes/${id}`);
    const reload = await screen.findByRole('button', { name: 'Load restricted section' });
    const pending = deferred<Result<AddressDetail>>();
    vi.mocked(api.getIntakeAddress).mockReturnValue(pending.promise);
    fireEvent.click(reload);
    fireEvent.click(reload);
    expect(api.getIntakeAddress).toHaveBeenCalledTimes(2);
    expect(reload).toBeDisabled();
    await act(async () => {
      pending.resolve({
        ok: true,
        value: {
          intake_id: id,
          version: 1,
          section: 'worker_residence',
          candidate: { line1: 'Current' },
          resolved: null,
        },
      });
      await pending.promise;
    });
    fireEvent.change(screen.getByLabelText('Address line 1'), { target: { value: 'Later edit' } });
    expect(screen.getByLabelText('Address line 1')).toHaveValue('Later edit');
    expect(screen.queryByText('All changes saved')).not.toBeInTheDocument();
  });
  it('does not restore a late restricted success after a newly opened record denies access', async () => {
    const old = deferred<Result<AddressDetail>>();
    vi.mocked(api.getIntakeAddress).mockResolvedValueOnce({ ok: false, failure: 'forbidden' });
    const view = mount(`/staff/intakes/${id}`);
    const reload = await screen.findByRole('button', { name: 'Load restricted section' });
    vi.mocked(api.getIntakeAddress).mockReturnValueOnce(old.promise);
    fireEvent.click(reload);
    fireEvent.click(reload);
    view.unmount();
    vi.mocked(api.getIntakeAddress).mockResolvedValue({ ok: false, failure: 'forbidden' });
    mount(`/staff/intakes/${id}`);
    await screen.findByText('Section unavailable. Values are not shown.');
    await act(async () => {
      old.resolve({
        ok: true,
        value: {
          intake_id: id,
          version: 1,
          section: 'worker_residence',
          candidate: { line1: 'Old concealed value' },
          resolved: null,
        },
      });
      await old.promise;
    });
    expect(screen.queryByLabelText('Address line 1')).not.toBeInTheDocument();
    expect(screen.queryByDisplayValue('Old concealed value')).not.toBeInTheDocument();
  });
  it('keeps a new edit dirty when the pending restricted refresh succeeds', async () => {
    mount(`/staff/intakes/${id}`);
    await screen.findByLabelText('Address line 1');
    fireEvent.change(screen.getByLabelText('Address line 1'), { target: { value: 'Submitted' } });
    vi.mocked(api.saveIntake).mockResolvedValue({
      ok: true,
      value: { command_id: 'key', result_record_version: 2, current: detail(2) },
    });
    vi.mocked(api.getIntakeAddress).mockResolvedValue({ ok: false, failure: 'failed' });
    fireEvent.click(screen.getByRole('button', { name: 'Save address: Residential address' }));
    await screen.findByRole('button', { name: 'Load restricted section' });
    const pending = deferred<Result<AddressDetail>>();
    vi.mocked(api.getIntakeAddress).mockReturnValue(pending.promise);
    fireEvent.click(screen.getByRole('button', { name: 'Load restricted section' }));
    fireEvent.change(screen.getByLabelText('Address line 1'), { target: { value: 'Edited during refresh' } });
    await act(async () => {
      pending.resolve({
        ok: true,
        value: {
          intake_id: id,
          version: 2,
          section: 'worker_residence',
          candidate: { line1: 'Submitted' },
          resolved: null,
        },
      });
      await pending.promise;
    });
    expect(screen.getByLabelText('Address line 1')).toHaveValue('Edited during refresh');
    expect(screen.getByRole('button', { name: 'Save address: Residential address' })).toBeEnabled();
    expect(screen.queryByText('All changes saved')).not.toBeInTheDocument();
  });
  it.each(['retry', 'first response'] as const)(
    'blocks unseen concurrent changes in a successful %s',
    async (mode) => {
      mount(`/staff/intakes/${id}`);
      await screen.findByLabelText('Address line 1');
      fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Submitted content' } });
      fireEvent.change(screen.getByLabelText('Address line 1'), { target: { value: 'Local address draft' } });
      const pending = deferred<Result<IntakeCommandResult>>();
      vi.mocked(api.saveIntake).mockReturnValueOnce(pending.promise);
      fireEvent.click(screen.getByRole('button', { name: 'Save details' }));
      fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Later local content' } });
      if (mode === 'retry') {
        await act(async () => {
          pending.resolve({ ok: false, failure: 'unknown' });
          await pending.promise;
        });
        vi.mocked(api.saveIntake).mockResolvedValueOnce({
          ok: true,
          value: {
            command_id: 'key',
            result_record_version: 2,
            current: detail(3, 'Unseen external content'),
          },
        });
        fireEvent.click(await screen.findByRole('button', { name: 'Retry original save' }));
      } else {
        await act(async () => {
          pending.resolve({
            ok: true,
            value: {
              command_id: 'key',
              result_record_version: 2,
              current: detail(3, 'Unseen external content'),
            },
          });
          await pending.promise;
        });
      }
      await screen.findByRole('alert');
      expect(screen.getByLabelText('Full name')).toHaveValue('Later local content');
      expect(screen.getByLabelText('Address line 1')).toHaveValue('Local address draft');
      expect(screen.queryByDisplayValue('Unseen external content')).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Save details' })).toBeDisabled();
      expect(screen.getByRole('button', { name: 'Save address: Residential address' })).toBeDisabled();
      expect(screen.queryByText('All changes saved')).not.toBeInTheDocument();
      expect(
        screen.getByText(
          'The original save succeeded. Newer changes require reopening and comparison before another save.',
        ),
      ).toBeInTheDocument();
      const calls = vi.mocked(api.saveIntake).mock.calls.length;
      fireEvent.click(screen.getByRole('button', { name: 'Save address: Residential address' }));
      expect(api.saveIntake).toHaveBeenCalledTimes(calls);
    },
  );
  it('does not refetch or replace address buffers after an advanced-current address receipt', async () => {
    mount(`/staff/intakes/${id}`);
    await screen.findByLabelText('Address line 1');
    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Unsaved local content' } });
    fireEvent.change(screen.getByLabelText('Address line 1'), {
      target: { value: 'Submitted local address' },
    });
    const pending = deferred<Result<IntakeCommandResult>>();
    vi.mocked(api.saveIntake).mockReturnValueOnce(pending.promise);
    fireEvent.click(screen.getByRole('button', { name: 'Save address: Residential address' }));
    fireEvent.change(screen.getByLabelText('Address line 1'), { target: { value: 'Later local address' } });
    await act(async () => {
      pending.resolve({
        ok: true,
        value: { command_id: 'key', result_record_version: 2, current: detail(3, 'Unseen external content') },
      });
      await pending.promise;
    });
    expect(screen.getByLabelText('Full name')).toHaveValue('Unsaved local content');
    expect(screen.getByLabelText('Address line 1')).toHaveValue('Later local address');
    expect(api.getIntakeAddress).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('button', { name: 'Save address: Residential address' })).toBeDisabled();
    expect(screen.queryByText('All changes saved')).not.toBeInTheDocument();
  });
  it('keeps the submitted creation form when its receipt already has newer external changes', async () => {
    mount();
    fireEvent.click(screen.getByRole('button', { name: 'New intake' }));
    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Submitted creation' } });
    vi.mocked(api.saveIntake).mockResolvedValueOnce({
      ok: true,
      value: { command_id: 'key', result_record_version: 1, current: detail(2, 'External name') },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save details' }));
    await screen.findByRole('alert');
    expect(screen.getByLabelText('Full name')).toHaveValue('Submitted creation');
    expect(api.getIntakeAddress).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Save details' })).toBeDisabled();
    expect(screen.queryByText('All changes saved')).not.toBeInTheDocument();
  });
});
