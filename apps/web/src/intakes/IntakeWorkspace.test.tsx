import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AppRoutes } from '../app/App';
import { LanguageProvider } from '../i18n/LanguageProvider';
import * as api from '../api/intakeClient';
import * as discovery from '../api/canonicalDiscovery';
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
  vi.mocked(api.queryWorkInterests).mockResolvedValue({
    ok: true,
    value: { items: [], next_cursor: null },
  });
  vi.mocked(api.queryFollowUpOwners).mockResolvedValue({
    ok: true,
    value: { items: [], next_cursor: null },
  });
  vi.mocked(api.queryIntakeHistory).mockResolvedValue({
    ok: true,
    value: { items: [], next_cursor: null },
  });
  vi.mocked(api.queryIntakes).mockResolvedValue({ ok: true, value: { items: [], next_cursor: null } });
  vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: detail() });
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
    vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: detail(4, 'Authoritative name') });
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
    fireEvent.change(screen.getByLabelText('Employer name'), {
      target: { value: 'Fictional Employer' },
    });
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
      within(screen.getByRole('group', { name: 'Residential address' })).getByLabelText(
        'Address line 1',
      ),
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
    fireEvent.change(screen.getByLabelText('Address line 1'), {
      target: { value: 'Submitted address' },
    });
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
    vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: employer });
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
    fireEvent.change(screen.getByLabelText('Address line 1'), {
      target: { value: 'Edited during refresh' },
    });
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
      fireEvent.change(screen.getByLabelText('Address line 1'), {
        target: { value: 'Local address draft' },
      });
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
    fireEvent.change(screen.getByLabelText('Address line 1'), {
      target: { value: 'Later local address' },
    });
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
it('shows missing information before opening intake', async () => {
  vi.mocked(api.queryIntakes).mockResolvedValue({
    ok: true,
    value: { items: [detail().summary], next_cursor: null },
  });
  mount();
  expect(await screen.findByText('Missing: Phone')).toBeInTheDocument();
});
it('separates saved completeness and review status', async () => {
  mount(`/staff/intakes/${id}`);
  await screen.findByLabelText('Full name');
  expect(screen.getByRole('group', { name: 'Review and follow-up' })).toBeInTheDocument();
  expect(screen.getByText(/Not reviewed/)).toBeInTheDocument();
});

it('records an explicit current-content review without editing facts', async () => {
  const complete = detail();
  complete.summary.complete = true;
  complete.summary.missing_fields = [];
  vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: complete });
  const reviewed = {
    ...complete,
    summary: { ...complete.summary, version: 2, review_status: 'current' as const },
    latest_review: {
      review_id: id,
      reviewed_record_version: 1,
      reviewed_content_version: 1,
      outcome: 'intake_reviewed',
      actor_id: id,
      actor_display_name: 'Fictional reviewer',
      occurred_at: '2026-09-14T12:00:00Z',
    },
  };
  vi.mocked(api.saveIntake).mockResolvedValue({
    ok: true,
    value: { command_id: id, result_record_version: 2, current: reviewed },
  });
  mount(`/staff/intakes/${id}`);
  await screen.findByLabelText('Address line 1');
  fireEvent.change(screen.getByLabelText('Restricted note'), {
    target: { value: 'Fictional review note' },
  });
  fireEvent.click(screen.getByLabelText('Confirm this recorded action'));
  fireEvent.click(screen.getByRole('button', { name: 'Record review' }));
  await screen.findByText(/Current review/);
  expect(api.saveIntake).toHaveBeenCalledWith(
    expect.objectContaining({
      path: `/intakes/${id}/reviews`,
      body: { expected_version: 1, outcome: 'intake_reviewed', note: 'Fictional review note' },
    }),
  );
  expect(screen.getByText(/Fictional reviewer/)).toBeInTheDocument();
});
it('keeps unknown review identity and later notes while blocking every section save', async () => {
  const complete = detail();
  complete.summary.complete = true;
  vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: complete });
  vi.mocked(api.saveIntake).mockResolvedValue({ ok: false, failure: 'unknown' });
  mount(`/staff/intakes/${id}`);
  await screen.findByLabelText('Address line 1');
  fireEvent.change(screen.getByLabelText('Restricted note'), { target: { value: 'Original note' } });
  fireEvent.click(screen.getByLabelText('Confirm this recorded action'));
  fireEvent.click(screen.getByRole('button', { name: 'Record review' }));
  await screen.findByRole('button', { name: 'Retry original save' });
  fireEvent.change(screen.getByLabelText('Restricted note'), { target: { value: 'Later note' } });
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Later name' } });
  expect(screen.getByRole('button', { name: 'Save details' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'Retry original save' }));
  await waitFor(() => {
    expect(api.saveIntake).toHaveBeenCalledTimes(2);
  });
  expect(vi.mocked(api.saveIntake).mock.calls[0]?.[0]).toBe(
    vi.mocked(api.saveIntake).mock.calls[1]?.[0],
  );
  expect(screen.getByLabelText('Restricted note')).toHaveValue('Later note');
});
it('records needs-follow-up with explicit owner and deadline, retaining rejected input', async () => {
  vi.mocked(api.queryFollowUpOwners).mockResolvedValue({
    ok: true,
    value: { items: [{ staff_id: id, display_name: 'Fictional owner' }], next_cursor: 'more' },
  });
  mount(`/staff/intakes/${id}`);
  await screen.findByLabelText('Address line 1');
  fireEvent.change(screen.getByLabelText('Review outcome'), { target: { value: 'needs_follow_up' } });
  fireEvent.change(screen.getByLabelText('Reason category'), {
    target: { value: 'missing_information' },
  });
  fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Fictional missing phone' } });
  fireEvent.change(screen.getByLabelText('Follow-up owner'), { target: { value: id } });
  fireEvent.change(screen.getByLabelText('Due instant (include UTC offset)'), {
    target: { value: 'bad instant' },
  });
  fireEvent.change(screen.getByLabelText('IANA time zone'), { target: { value: 'America/New_York' } });
  vi.mocked(api.saveIntake).mockResolvedValue({ ok: false, failure: 'failed' });
  fireEvent.click(screen.getByLabelText('Confirm this recorded action'));
  fireEvent.click(screen.getByRole('button', { name: 'Record review' }));
  await waitFor(() => {
    expect(api.saveIntake).toHaveBeenCalledTimes(1);
  });
  expect(screen.getByLabelText('Due instant (include UTC offset)')).toHaveValue('bad instant');
  fireEvent.change(screen.getByLabelText('Due instant (include UTC offset)'), {
    target: { value: '2026-09-13T15:00:00-04:00' },
  });
  fireEvent.click(screen.getByLabelText('Confirm this recorded action'));
  fireEvent.click(screen.getByRole('button', { name: 'Record review' }));
  await waitFor(() => {
    expect(api.saveIntake).toHaveBeenCalledTimes(2);
  });
  expect(vi.mocked(api.saveIntake).mock.calls[1]?.[0].body).toEqual({
    expected_version: 1,
    outcome: 'needs_follow_up',
    reason_code: 'missing_information',
    reason_text: 'Fictional missing phone',
    owner_staff_id: id,
    next_follow_up_at: '2026-09-13T15:00:00-04:00',
    time_zone: 'America/New_York',
  });
  fireEvent.click(
    within(screen.getByRole('group', { name: 'Review and follow-up' })).getByRole('button', {
      name: 'Next page',
    }),
  );
  await waitFor(() => {
    expect(api.queryFollowUpOwners).toHaveBeenCalledWith(id, 'more');
  });
});
it.each(['reschedule', 'reassign', 'attempt'])(
  'records %s without claiming reviewed or hiding shared responsibility',
  async (action) => {
    const follow = detail();
    follow.summary.follow_up = {
      owner_staff_id: id,
      next_follow_up_at: '2026-09-13T12:00:00Z',
      overdue: true,
    };
    follow.summary.review_status = 'current';
    vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: follow });
    vi.mocked(api.queryFollowUpOwners).mockResolvedValue({
      ok: true,
      value: { items: [{ staff_id: id, display_name: 'Fictional owner' }], next_cursor: null },
    });
    vi.mocked(api.saveIntake).mockResolvedValue({ ok: false, failure: 'failed' });
    mount(`/staff/intakes/${id}`);
    await screen.findByLabelText('Address line 1');
    expect(screen.getByText(/Retained follow-up deadline:/)).toHaveTextContent('Overdue');
    expect(screen.getByText(/responsibility is shared/)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Follow-up action'), { target: { value: 'follow-ups' } });
    const actions = screen.getAllByLabelText('Follow-up action');
    if (!actions[1]) throw new Error('Missing action control');
    fireEvent.change(actions[1], { target: { value: action } });
    fireEvent.change(screen.getByLabelText('Reason'), { target: { value: 'Fictional bookkeeping' } });
    await screen.findByRole('option', { name: 'Fictional owner' });
    fireEvent.change(screen.getByLabelText('Follow-up owner'), { target: { value: id } });
    fireEvent.change(screen.getByLabelText('Due instant (include UTC offset)'), {
      target: { value: '2026-09-14T12:00:00Z' },
    });
    fireEvent.change(screen.getByLabelText('IANA time zone'), { target: { value: 'Etc/UTC' } });
    if (action === 'attempt') {
      fireEvent.change(screen.getByLabelText('Contact method'), { target: { value: 'phone' } });
      fireEvent.change(screen.getByLabelText('Contact outcome'), { target: { value: 'no_answer' } });
    }
    fireEvent.click(screen.getByLabelText('Confirm this recorded action'));
    fireEvent.click(
      screen.getByRole('button', {
        name:
          action === 'attempt'
            ? 'Record contact attempt'
            : action === 'reassign'
              ? 'Reassign follow-up'
              : 'Reschedule follow-up',
      }),
    );
    await waitFor(() => {
      expect(api.saveIntake).toHaveBeenCalledTimes(1);
    });
    expect(vi.mocked(api.saveIntake).mock.calls[0]?.[0].path).toBe(`/intakes/${id}/follow-ups`);
    expect(vi.mocked(api.saveIntake).mock.calls[0]?.[0].body.action).toBe(action);
    expect(screen.getByText(/Current review/)).toBeInTheDocument();
  },
);
it('blocks current review while details are dirty and clears denied review notes', async () => {
  const complete = detail();
  complete.summary.complete = true;
  vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: complete });
  mount(`/staff/intakes/${id}`);
  await screen.findByLabelText('Address line 1');
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Later' } });
  fireEvent.click(screen.getByLabelText('Confirm this recorded action'));
  expect(screen.getByRole('button', { name: 'Record review' })).toBeDisabled();
  vi.mocked(api.saveIntake).mockResolvedValue({
    ok: true,
    value: { command_id: id, result_record_version: 1, current: complete },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Save details' }));
  await waitFor(() => {
    expect(screen.getByRole('button', { name: 'Record review' })).toBeEnabled();
  });
  fireEvent.change(screen.getByLabelText('Restricted note'), { target: { value: 'Concealed note' } });
  fireEvent.click(screen.getByLabelText('Confirm this recorded action'));
  vi.mocked(api.saveIntake).mockResolvedValue({ ok: false, failure: 'forbidden' });
  fireEvent.click(screen.getByRole('button', { name: 'Record review' }));
  await waitFor(() => {
    expect(screen.queryByLabelText('Restricted note')).not.toBeInTheDocument();
  });
  expect(screen.queryByDisplayValue('Concealed note')).not.toBeInTheDocument();
});
it('requires fresh review confirmation after a section save advances the displayed version', async () => {
  const complete = detail();
  complete.summary.complete = true;
  vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: complete });
  const revised = {
    ...complete,
    summary: { ...complete.summary, version: 2 },
    content_version: 2,
    candidate: { full_name: 'Revised fictional name' },
  };
  mount(`/staff/intakes/${id}`);
  await screen.findByLabelText('Address line 1');
  fireEvent.click(screen.getByLabelText('Confirm this recorded action'));
  fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Revised fictional name' } });
  vi.mocked(api.saveIntake).mockResolvedValue({
    ok: true,
    value: { command_id: id, result_record_version: 2, current: revised },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Save details' }));
  await screen.findByText(/Version 2/);
  expect(screen.getByLabelText('Confirm this recorded action')).not.toBeChecked();
  expect(screen.getByRole('button', { name: 'Record review' })).toBeDisabled();
  fireEvent.click(screen.getByLabelText('Confirm this recorded action'));
  expect(screen.getByRole('button', { name: 'Record review' })).toBeEnabled();
});
it('retains the selected trusted owner across pages and invalidates confirmation on scope denial', async () => {
  vi.mocked(api.queryFollowUpOwners).mockResolvedValue({
    ok: true,
    value: { items: [{ staff_id: id, display_name: 'First fictional owner' }], next_cursor: 'next' },
  });
  mount(`/staff/intakes/${id}`);
  await screen.findByLabelText('Address line 1');
  fireEvent.change(screen.getByLabelText('Review outcome'), { target: { value: 'needs_follow_up' } });
  await screen.findByRole('option', { name: 'First fictional owner' });
  fireEvent.change(screen.getByLabelText('Follow-up owner'), { target: { value: id } });
  vi.mocked(api.queryFollowUpOwners).mockResolvedValue({
    ok: true,
    value: {
      items: [
        { staff_id: 'f76bf415-6b21-4fbd-9639-28b9b3374411', display_name: 'Second fictional owner' },
      ],
      next_cursor: 'last',
    },
  });
  fireEvent.click(
    within(screen.getByRole('group', { name: 'Review and follow-up' })).getByRole('button', {
      name: 'Next page',
    }),
  );
  await screen.findByRole('option', { name: 'Second fictional owner' });
  expect(screen.getByLabelText('Follow-up owner')).toHaveValue(id);
  expect(screen.getByRole('option', { name: 'First fictional owner' })).toBeInTheDocument();
  fireEvent.click(screen.getByLabelText('Confirm this recorded action'));
  vi.mocked(api.queryFollowUpOwners).mockResolvedValue({ ok: false, failure: 'forbidden' });
  fireEvent.click(
    within(screen.getByRole('group', { name: 'Review and follow-up' })).getByRole('button', {
      name: 'Next page',
    }),
  );
  await screen.findByText('Unavailable. No protected values are shown.');
  expect(screen.queryByRole('option', { name: 'First fictional owner' })).not.toBeInTheDocument();
  expect(screen.getByLabelText('Confirm this recorded action')).not.toBeChecked();
  expect(screen.getByRole('button', { name: 'Record review' })).toBeDisabled();
});

describe('canonical workspace integration', () => {
  const reviewId = '11111111-1111-4111-8111-111111111111';
  function reviewed(): IntakeDetail {
    const value = detail();
    return { ...value, summary: { ...value.summary, complete: true, missing_fields: [], review_status: 'current' },
      latest_review: { review_id: reviewId, reviewed_record_version: 1, reviewed_content_version: 1,
        outcome: 'intake_reviewed', actor_id: reviewId, actor_display_name: 'Fictional Staff', occurred_at: '' } };
  }
  function finalized(): IntakeDetail {
    const value = reviewed(), ref = { id: reviewId, version: 1, disposition: 'created' as const };
    return { ...value, summary: { ...value.summary, version: 2, lifecycle: 'finalized' },
      finalization: { kind: 'worker', worker: ref, contact: ref, residence: ref, preferences: ref } };
  }
  it('preserves the original unknown finalization retry and prevents later edits', async () => {
    vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: reviewed() });
    vi.mocked(api.saveCanonicalIntake).mockResolvedValueOnce({ ok: false, failure: 'unknown' })
      .mockImplementationOnce((command) => Promise.resolve({ ok: true, value: {
        command_id: command.key, result_record_version: 2, current: finalized(), finalization: finalized().finalization,
      } }));
    mount(`/staff/intakes/${id}`);
    await screen.findByText('All changes saved');
    fireEvent.click(screen.getByLabelText(/I confirm/));
    fireEvent.click(screen.getByRole('button', { name: 'Finalize intake' }));
    const retry = await screen.findByRole('button', { name: /Retry/ });
    expect(screen.getByLabelText('Full name')).toBeDisabled();
    expect(screen.getByLabelText('Address line 1')).toBeDisabled();
    fireEvent.click(retry);
    await screen.findByRole('heading', { name: 'Finalized intake — read-only' });
    expect(api.saveCanonicalIntake).toHaveBeenCalledTimes(2);
    expect(vi.mocked(api.saveCanonicalIntake).mock.calls[1]?.[0]).toEqual(vi.mocked(api.saveCanonicalIntake).mock.calls[0]?.[0]);
    expect(screen.queryByLabelText('Full name')).not.toBeInTheDocument();
    expect(api.saveIntake).not.toHaveBeenCalled();
  });
  it('reopens finalized detail without draft/address mutation controls or restricted reads', async () => {
    vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: finalized() });
    mount(`/staff/intakes/${id}`);
    await screen.findByRole('heading', { name: 'Finalized intake — read-only' });
    expect(api.getIntakeAddress).not.toHaveBeenCalled();
    expect(screen.queryByRole('button', { name: 'Finalize intake' })).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Original finalization references' })).toBeInTheDocument();
  });
  it('allows reconfirmation after a definite finalization failure', async () => {
    vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: reviewed() });
    vi.mocked(api.saveCanonicalIntake).mockResolvedValue({ ok: false, failure: 'failed' });
    mount(`/staff/intakes/${id}`); await screen.findByText('All changes saved');
    fireEvent.click(screen.getByLabelText(/I confirm/));
    fireEvent.click(screen.getByRole('button', { name: 'Finalize intake' }));
    await waitFor(() => { expect(screen.getByRole('button', { name: 'Discard pending selection' })).toBeInTheDocument(); });
    fireEvent.click(screen.getByLabelText(/I confirm/));
    fireEvent.click(screen.getByRole('button', { name: 'Finalize intake' }));
    await waitFor(() => { expect(api.saveCanonicalIntake).toHaveBeenCalledTimes(2); });
  });
  it('blocks finalization while an independent section is dirty', async () => {
    vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: reviewed() });
    mount(`/staff/intakes/${id}`); await screen.findByText('All changes saved');
    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Unsaved change' } });
    fireEvent.click(screen.getByLabelText(/I confirm/));
    expect(screen.getByRole('button', { name: 'Finalize intake' })).toBeDisabled();
    expect(api.saveCanonicalIntake).not.toHaveBeenCalled();
  });
  it('saves explicit unlink using current version then refreshes address projections', async () => {
    const value = detail(), ref = { id: reviewId, version: 1 };
    vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: { ...value,
      links: { worker: ref, worker_contact: ref, worker_preferences: ref, worker_residence: ref },
      resolved: { full_name: 'Canonical name' } } });
    vi.mocked(api.saveCanonicalIntake).mockImplementation((command) => Promise.resolve({ ok: true, value: {
      command_id: command.key, result_record_version: 2, current: detail(2),
    } }));
    mount(`/staff/intakes/${id}`); await screen.findByText('All changes saved');
    expect(screen.getByDisplayValue('Canonical name')).toBeDisabled();
    vi.mocked(api.getIntakeAddress).mockResolvedValue({ ok: true, value: {
      intake_id: id, section: 'worker_residence', version: 2, candidate: null, resolved: null,
    } });
    fireEvent.click(screen.getByRole('button', { name: 'Remove saved selection' }));
    await waitFor(() => { expect(api.saveCanonicalIntake).toHaveBeenCalledWith(expect.objectContaining({
      path: `/intakes/${id}/links`, body: { expected_version: 1, party: null },
    })); });
    await screen.findByText(/Version 2/);
    await screen.findByText('All changes saved');
    expect(api.getIntakeAddress).toHaveBeenCalledTimes(2);
  });
});

it('resets employer selection controls after saving and discarding without clearing candidate edits', async () => {
  const employerId = '11111111-1111-4111-8111-111111111111';
  const employer = (version = 1): IntakeDetail => ({ ...detail(version),
    summary: { ...detail(version).summary, kind: 'employer' }, candidate: { display_name: 'Draft business', employer_type: 'business' } });
  vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: employer() });
  let version = 1;
  vi.mocked(api.getIntakeAddress).mockImplementation((_id, section) => Promise.resolve({ ok: true, value: {
    intake_id: id, version, section, candidate: null, resolved: null,
  } }));
  vi.mocked(api.saveCanonicalIntake).mockImplementation((command) => {
    version = 2;
    return Promise.resolve({ ok: true, value: { command_id: command.key, result_record_version: 2, current: employer(2) } });
  });
  vi.spyOn(discovery, 'discover').mockResolvedValue({ ok: true, value: {
    items: [{ id: employerId, version: 5, label: 'Fictional business', employerType: 'business' }], next_cursor: null } });
  mount(`/staff/intakes/${id}`); await screen.findByText('All changes saved');
  async function selectParent() {
    fireEvent.change(screen.getByLabelText('Name to search'), { target: { value: 'Fictional' } });
    fireEvent.click(screen.getByRole('button', { name: 'Search existing records' }));
    await screen.findByRole('option', { name: /Fictional business/ });
    fireEvent.change(screen.getByLabelText('Choose explicitly'), { target: { value: employerId } });
  }
  await selectParent();
  for (const title of ['Contact', 'Worksite', 'Business address']) {
    fireEvent.change(within(screen.getByRole('group', { name: title })).getByLabelText('Choose explicitly'), { target: { value: 'new' } });
  }
  fireEvent.click(screen.getByRole('button', { name: 'Save selection' }));
  await screen.findByText('All changes saved');
  expect(screen.queryByRole('group', { name: 'Contact' })).not.toBeInTheDocument();
  expect(screen.getByLabelText('Name to search')).toHaveValue('');
  await selectParent();
  fireEvent.change(screen.getByLabelText('Employer name'), { target: { value: 'Retained candidate edit' } });
  fireEvent.click(screen.getByRole('button', { name: 'Discard pending selection' }));
  expect(screen.queryByRole('group', { name: 'Contact' })).not.toBeInTheDocument();
  expect(screen.getByLabelText('Employer name')).toHaveValue('Retained candidate edit');
  expect(screen.queryByText('All changes saved')).not.toBeInTheDocument();
}, 15000);

it('retains later candidate edits when an original link retry returns a subsequently finalized intake', async () => {
  const ref = { id: '11111111-1111-4111-8111-111111111111', version: 1 };
  vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: { ...detail(),
    links: { worker: ref, worker_contact: ref, worker_residence: ref, worker_preferences: ref },
    resolved: { full_name: 'Canonical name' } } });
  const output = { ...ref, disposition: 'created' as const };
  vi.mocked(api.saveCanonicalIntake).mockResolvedValueOnce({ ok: false, failure: 'unknown' })
    .mockImplementationOnce((command) => Promise.resolve({ ok: true, value: {
      command_id: command.key, result_record_version: 2, current: { ...detail(3),
        summary: { ...detail(3).summary, lifecycle: 'finalized' },
        finalization: { kind: 'worker', worker: output, contact: output, residence: output, preferences: output } },
    } }));
  mount(`/staff/intakes/${id}`); await screen.findByText('All changes saved');
  fireEvent.click(screen.getByRole('button', { name: 'Remove saved selection' }));
  await screen.findByRole('button', { name: /Retry/ });
  fireEvent.change(screen.getByDisplayValue('Fictional Person'), { target: { value: 'Keep this later edit' } });
  fireEvent.click(screen.getByRole('button', { name: /Retry/ }));
  await waitFor(() => { expect(api.saveCanonicalIntake).toHaveBeenCalledTimes(2); });
  await waitFor(() => { expect(screen.queryByRole('button', { name: /Retry/ })).not.toBeInTheDocument(); });
  expect(screen.getByDisplayValue('Keep this later edit')).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Finalized intake — read-only' })).not.toBeInTheDocument();
});

it('clears displayed resolved address facts when an address save is denied', async () => {
  vi.mocked(api.getIntakeAddress).mockResolvedValue({ ok: true, value: {
    intake_id: id, version: 1, section: 'worker_residence', candidate: null,
    resolved: { line1: 'Fictional restricted address' },
  } });
  vi.mocked(api.saveIntake).mockResolvedValue({ ok: false, failure: 'forbidden' });
  mount(`/staff/intakes/${id}`); await screen.findByText('All changes saved');
  expect(screen.getByDisplayValue('Fictional restricted address')).toBeDisabled();
  const fields = screen.getAllByLabelText('Address line 1');
  const editable = fields.find((field) => !(field as HTMLInputElement).matches(':disabled'));
  expect(editable).toBeDefined();
  fireEvent.change(editable as HTMLElement, { target: { value: 'Fictional candidate address' } });
  fireEvent.click(screen.getByRole('button', { name: /Save address/ }));
  await waitFor(() => { expect(screen.queryByDisplayValue('Fictional restricted address')).not.toBeInTheDocument(); });
});

it('retains later candidate edits when an original revision retry returns a subsequently finalized intake', async () => {
  const ref = { id: '11111111-1111-4111-8111-111111111111', version: 1 };
  vi.mocked(api.getCanonicalIntake).mockResolvedValue({ ok: true, value: { ...detail(),
    links: { worker: ref, worker_contact: ref, worker_residence: ref, worker_preferences: ref },
    resolved: { full_name: 'Canonical name' } } });
  const output = { ...ref, disposition: 'created' as const };
  vi.mocked(api.saveIntake).mockResolvedValueOnce({ ok: false, failure: 'unknown' })
    .mockImplementationOnce((command) => Promise.resolve({ ok: true, value: {
      command_id: command.key, result_record_version: 2, current: { ...detail(3),
        summary: { ...detail(3).summary, lifecycle: 'finalized' },
        finalization: { kind: 'worker', worker: output, contact: output, residence: output, preferences: output } },
    } }));
  mount(`/staff/intakes/${id}`); await screen.findByText('All changes saved');
  fireEvent.change(screen.getByDisplayValue('Fictional Person'), { target: { value: 'Submitted revision' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save details' }));
  await screen.findByRole('button', { name: /Retry/ });
  fireEvent.change(screen.getByDisplayValue('Submitted revision'), { target: { value: 'Keep this later edit' } });
  fireEvent.click(screen.getByRole('button', { name: /Retry/ }));
  await waitFor(() => { expect(api.saveIntake).toHaveBeenCalledTimes(2); });
  await waitFor(() => { expect(screen.queryByRole('button', { name: /Retry/ })).not.toBeInTheDocument(); });
  const calls = vi.mocked(api.saveIntake).mock.calls;
  expect(calls[0]?.[0]).toBeDefined();
  expect(calls[1]?.[0]).toEqual(calls[0]?.[0]);
  expect(screen.getByDisplayValue('Keep this later edit')).toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Finalized intake — read-only' })).not.toBeInTheDocument();
});


it.each(['en', 'es'])('shows unavailable linked completeness truthfully in %s recovery lists', async (language) => {
  const summary = { ...detail().summary, display_name: undefined, complete: null, missing_fields: [] };
  vi.mocked(api.queryIntakes).mockResolvedValue({ ok: true, value: { items: [summary], next_cursor: null } });
  const view = mount();
  if (language === 'es') fireEvent.click(screen.getByRole('button', { name: 'Cambiar a español' }));
  await screen.findByText(language === 'en' ? /Completeness unavailable/ : /No se puede consultar si está completo/);
  expect(screen.queryByText(/^(Incomplete|Incompleto) ·/)).not.toBeInTheDocument();
  expect(screen.queryByText(/^(Missing|Faltan):/)).not.toBeInTheDocument();
  expect(await runAxe(view.container)).toEqual([]);
});
