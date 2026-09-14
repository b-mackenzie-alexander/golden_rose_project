import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { vi } from 'vitest';

import { createEmployer, getEmployer, reviseEmployer, searchEmployers } from '../api/employerClient';
import { App, AppRoutes } from '../app/App';
import { EmployerCreateForm } from './EmployerCreateForm';
import { EmployerWorkspace } from './EmployerWorkspace';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { VALUE_SAFE_TESTING_LIBRARY_MESSAGE } from '../test/valueSafeDiagnostics';

vi.mock('../api/employerClient', () => ({
  createEmployer: vi.fn(),
  getEmployer: vi.fn(),
  reviseEmployer: vi.fn(),
  searchEmployers: vi.fn(),
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

describe('EmployerWorkspace', () => {
  it('resets state on page hide without requiring a persisted-restore callback', () => {
    render(
      <LanguageProvider>
        <EmployerWorkspace onPersistedRestore={() => {}} />
      </LanguageProvider>,
    );

    act(() => {
      window.dispatchEvent(new Event('pagehide'));
      window.dispatchEvent(new Event('pageshow'));
    });

    expect(screen.getByRole('region', { name: 'Employers workspace' })).toBeInTheDocument();
    expect(screen.getByRole('form', { name: 'Create a draft employer' })).toBeInTheDocument();
    expect(screen.getByRole('form', { name: 'Employer search' })).toBeInTheDocument();
  });

  it('does not restore created detail or form state when create success resolves after pagehide', async () => {
    const user = userEvent.setup();
    const deferredCreate = createDeferredPromise<Awaited<ReturnType<typeof createEmployer>>>();
    const createEmployerMock = vi.mocked(createEmployer);
    createEmployerMock.mockReset();
    createEmployerMock.mockReturnValueOnce(deferredCreate.promise);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Late Success Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));

    act(() => {
      window.dispatchEvent(new Event('pagehide'));
    });

    expect(screen.getByLabelText('Draft employer display name')).toHaveValue('');

    await act(async () => {
      deferredCreate.resolve({
        ok: true,
        value: {
          employerId: '61616161-6161-4161-8161-616161616161',
          employerType: 'business',
          displayName: 'Late Success Rose',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
        },
      });
      await deferredCreate.promise;
    });

    expect(screen.queryByRole('heading', { name: 'Draft employer created' })).not.toBeInTheDocument();
    expect(screen.getByLabelText('Draft employer display name')).toHaveValue('');
    expect(screen.queryByDisplayValue('Late Success Rose')).not.toBeInTheDocument();
  });

  it('does not restore unknown create authority after pagehide when a late completion resolves', async () => {
    const user = userEvent.setup();
    const deferredCreate = createDeferredPromise<Awaited<ReturnType<typeof createEmployer>>>();
    const createEmployerMock = vi.mocked(createEmployer);
    createEmployerMock.mockReset();
    createEmployerMock.mockReturnValueOnce(deferredCreate.promise);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Late Unknown Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));

    act(() => {
      window.dispatchEvent(new Event('pagehide'));
    });

    expect(screen.queryByRole('heading', { name: 'Create outcome is unknown' })).not.toBeInTheDocument();

    await act(async () => {
      deferredCreate.resolve({ ok: false, failure: { kind: 'unknown_outcome' } });
      await deferredCreate.promise;
    });

    expect(screen.queryByRole('heading', { name: 'Create outcome is unknown' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry same create attempt' })).not.toBeInTheDocument();
    expect(screen.getByLabelText('Draft employer display name')).toHaveValue('');
  });

  it('retires create authority synchronously on pagehide before parent reset effects', async () => {
    const user = userEvent.setup();
    const deferredCreate = createDeferredPromise<Awaited<ReturnType<typeof createEmployer>>>();
    const createEmployerMock = vi.mocked(createEmployer);
    const onCreateSuccess = vi.fn();
    createEmployerMock.mockReset();
    createEmployerMock.mockReturnValueOnce(deferredCreate.promise);

    render(
      <LanguageProvider>
        <EmployerCreateForm onCreateSuccess={onCreateSuccess} />
      </LanguageProvider>,
    );

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Synchronous Pagehide Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));

    window.dispatchEvent(new Event('pagehide'));

    await act(async () => {
      deferredCreate.resolve({
        ok: true,
        value: {
          employerId: '91919191-9191-4191-8191-919191919191',
          employerType: 'business',
          displayName: 'Synchronous Pagehide Rose',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
        },
      });
      await deferredCreate.promise;
    });

    expect(onCreateSuccess).not.toHaveBeenCalled();
    expect(screen.queryByRole('heading', { name: 'Draft employer created' })).not.toBeInTheDocument();
  });

  it('renders overview search create and detail regions in operational order', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const workspace = screen.getByRole('region', { name: 'Employers workspace' });
    const headings = within(workspace).getAllByRole('heading').map((heading) => heading.textContent);

    expect(headings.slice(0, 8)).toEqual([
      'Employer workspace',
      'Workspace overview',
      'Workflow guide',
      'Search first',
      'Create only if needed',
      'Review and revise',
      'Find an employer',
      'Create a draft employer',
    ]);
    expect(within(workspace).getByRole('region', { name: 'Workspace overview' })).toBeInTheDocument();
    expect(within(workspace).getByRole('region', { name: 'Workflow guide' })).toBeInTheDocument();
    expect(within(workspace).getByRole('region', { name: 'Find an employer' })).toBeInTheDocument();
    expect(within(workspace).getByRole('region', { name: 'Create a draft employer' })).toBeInTheDocument();
    expect(within(workspace).getByRole('region', { name: 'Work area' })).toBeInTheDocument();
  });

  it('shows the current employer workflow without prominent environment copy', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const workflowGuide = screen.getByRole('region', { name: 'Workflow guide' });

    expect(within(workflowGuide).getByRole('heading', { name: 'Search first' })).toBeInTheDocument();
    expect(within(workflowGuide).getByText('Use a name fragment and optional type to check for an existing draft.')).toBeInTheDocument();
    expect(within(workflowGuide).getByRole('heading', { name: 'Create only if needed' })).toBeInTheDocument();
    expect(
      within(workflowGuide).getByText('Add a draft employer only after the current search does not find the right record.'),
    ).toBeInTheDocument();
    expect(within(workflowGuide).getByRole('heading', { name: 'Review and revise' })).toBeInTheDocument();
    expect(
      within(workflowGuide).getByText('Select a draft to review current details, then save only intentional revisions.'),
    ).toBeInTheDocument();
    expect(within(workflowGuide).getByText('Current step')).toBeInTheDocument();
    expect(screen.getByText('Create a draft only after search confirms this employer is not already listed.')).toBeInTheDocument();
    expect(screen.queryByText(/fictional synthetic/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/local staff workspace/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/test-harness/i)).not.toBeInTheDocument();
  });

  it('updates create guidance from the current search checkpoint', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: { items: [], nextCursor: null },
      })
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '31313131-3131-4131-8131-313131313131',
              employerType: 'business',
              displayName: 'Checkpoint Rose',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByText('Search first before creating a new draft employer.')).toBeInTheDocument();

    await user.type(screen.getByLabelText('Employer name'), 'No Match Rose');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'No matching employers' });

    expect(
      screen.getByText('No matching draft was found for the current search. Create a draft if this is the employer you need.'),
    ).toBeInTheDocument();
    const workflowGuide = screen.getByRole('region', { name: 'Workflow guide' });
    const searchStep = within(workflowGuide).getByRole('heading', { name: 'Search first' }).closest('li');
    const createStep = within(workflowGuide).getByRole('heading', { name: 'Create only if needed' }).closest('li');
    const reviewStep = within(workflowGuide).getByRole('heading', { name: 'Review and revise' }).closest('li');

    expect(searchStep).toHaveTextContent('Completed this session');
    expect(createStep).toHaveTextContent('Current step');
    expect(reviewStep).not.toHaveTextContent('Current step');

    await user.type(screen.getByLabelText('Employer name'), ' Candidate');

    expect(screen.getByText('Search first before creating a new draft employer.')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });

    expect(
      screen.getByText('Search returned draft employers. Select a matching draft, or create only if none is correct.'),
    ).toBeInTheDocument();
    expect(searchStep).toHaveTextContent('Completed this session');
    expect(createStep).not.toHaveTextContent('Current step');
    expect(reviewStep).toHaveTextContent('Current step');
  });

  it('uses natural visible labels and unique accessible form names', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const searchForm = screen.getByRole('form', { name: 'Employer search' });
    const createForm = screen.getByRole('form', { name: 'Create a draft employer' });

    expect(within(searchForm).getByLabelText('Employer name')).toBeInTheDocument();
    expect(within(searchForm).getByLabelText('Employer type')).toBeInTheDocument();
    expect(within(createForm).getByLabelText('Draft employer type')).toBeInTheDocument();
    expect(within(createForm).getByLabelText('Draft employer display name')).toBeInTheDocument();
    expect(screen.queryByLabelText('Create employer type')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Create employer name')).not.toBeInTheDocument();
  });

  it('updates current work and session activity after create select and revision', async () => {
    const user = userEvent.setup();
    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('41414141-4141-4141-8141-414141414141');
    vi.mocked(createEmployer).mockReset();
    vi.mocked(searchEmployers).mockReset();
    vi.mocked(getEmployer).mockReset();
    vi.mocked(reviseEmployer).mockReset();
    vi.mocked(createEmployer).mockResolvedValue({
      ok: true,
      value: {
        employerId: '41414141-4141-4141-8141-414141414141',
        employerType: 'business',
        displayName: 'Session Created Rose',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
      },
    });
    vi.mocked(searchEmployers).mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '51515151-5151-4151-8151-515151515151',
            employerType: 'household',
            displayName: 'Session Selected Rose',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    vi.mocked(getEmployer)
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '51515151-5151-4151-8151-515151515151',
          employerType: 'household',
          displayName: 'Session Selected Rose',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 3,
          updatedAt: '2026-09-13T20:00:00Z',
        },
      })
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '51515151-5151-4151-8151-515151515151',
          employerType: 'business',
          displayName: 'Session Revised Rose',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 4,
          updatedAt: '2026-09-13T20:05:00Z',
        },
      });
    vi.mocked(reviseEmployer).mockResolvedValue({
      ok: true,
      value: {
        detail: {
          employerId: '51515151-5151-4151-8151-515151515151',
          employerType: 'business',
          displayName: 'Session Revised Rose',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 4,
          updatedAt: '2026-09-13T20:05:00Z',
        },
        resultVersion: 4,
        replayed: false,
      },
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const currentWork = screen.getByRole('region', { name: 'Current work' });
    expect(within(currentWork).getByText('No current employer selected in this browser session.')).toBeInTheDocument();
    expect(within(currentWork).getByText('Start by searching for an employer before creating or revising a draft.')).toBeInTheDocument();
    expect(screen.getByRole('region', { name: 'Current-session activity' })).toHaveTextContent('No session activity yet.');

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Session Created Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));
    await screen.findByRole('heading', { name: 'Draft employer created' });

    expect(currentWork).toHaveTextContent('Session Created Rose');
    expect(within(currentWork).getByText('Created draft employer in this session.')).toBeInTheDocument();
    expect(
      within(currentWork).getByText('Search again or select the created draft when you are ready to review current details.'),
    ).toBeInTheDocument();
    expect(within(screen.getByRole('region', { name: 'Workflow guide' })).getByText('Review and revise')).toBeInTheDocument();
    expect(within(screen.getByRole('region', { name: 'Workflow guide' })).getByText('Current step')).toBeInTheDocument();
    const sessionActivity = screen.getByRole('region', { name: 'Current-session activity' });
    expect(sessionActivity).toHaveTextContent('Created — Session Created Rose');

    await user.type(screen.getByLabelText('Employer name'), 'Session');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Session Selected Rose' }));
    await screen.findByRole('region', { name: 'Employer detail' });

    expect(currentWork).toHaveTextContent('Session Selected Rose');
    expect(within(currentWork).getByText('Reviewing selected draft employer.')).toBeInTheDocument();
    expect(
      within(currentWork).getByText('Use Edit draft employer only when the current detail needs a deliberate revision.'),
    ).toBeInTheDocument();
    expect(sessionActivity).toHaveTextContent('Selected — Session Selected Rose');

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'business');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Session Revised Rose');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));
    await screen.findByRole('heading', { name: 'Draft employer revision saved' });

    expect(currentWork).toHaveTextContent('Session Revised Rose');
    expect(within(currentWork).getByText('Revision saved in this session.')).toBeInTheDocument();
    expect(
      within(currentWork).getByText('The draft is refreshed after save; continue reviewing current detail before another change.'),
    ).toBeInTheDocument();
    expect(sessionActivity).toHaveTextContent('Revised — Session Revised Rose');
    expect(currentWork).not.toHaveTextContent(/assigned|queue|timeline|metric|complete/i);
    randomUuidSpy.mockRestore();
  });

  it('clears current work and activity on pagehide', async () => {
    const user = userEvent.setup();
    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('61616161-6161-4161-8161-616161616161');
    vi.mocked(createEmployer).mockReset();
    vi.mocked(createEmployer).mockResolvedValue({
      ok: true,
      value: {
        employerId: '61616161-6161-4161-8161-616161616161',
        employerType: 'business',
        displayName: 'Pagehide Current Rose',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
      },
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Pagehide Current Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));
    await screen.findByRole('heading', { name: 'Draft employer created' });
    expect(screen.getByRole('region', { name: 'Current-session activity' })).toHaveTextContent('Created — Pagehide Current Rose');

    act(() => {
      window.dispatchEvent(new Event('pagehide'));
    });

    expect(screen.getByRole('region', { name: 'Current work' })).toHaveTextContent('No current employer selected in this browser session.');
    expect(screen.getByRole('region', { name: 'Current-session activity' })).toHaveTextContent('No session activity yet.');
    expect(screen.queryByText('Pagehide Current Rose')).not.toBeInTheDocument();
    randomUuidSpy.mockRestore();
  });

  it('shows search instructions without fetching on mount', () => {
    const fetchMock = vi.fn<typeof fetch>();
    vi.stubGlobal('fetch', fetchMock);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole('heading', { name: 'Find an employer' })).toBeInTheDocument();
    expect(
      screen.getByText('Use a bounded employer name fragment to find an existing draft employer before creating another one.'),
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Employer name')).toBeInTheDocument();
    expect(screen.getByLabelText('Employer type')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Search employers' })).toBeInTheDocument();
    expect(screen.queryByText('No employers found.')).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('blocks invalid and type-only searches', async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn<typeof fetch>();
    vi.stubGlobal('fetch', fetchMock);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const nameInput = screen.getByLabelText('Employer name');
    const typeSelect = screen.getByLabelText('Employer type');
    const submitButton = screen.getByRole('button', { name: 'Search employers' });

    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent('Enter 2 to 100 visible characters from the employer name.');
    expect(nameInput).toHaveFocus();
    expect(nameInput).toHaveAttribute('aria-invalid', 'true');
    expect(nameInput).toHaveAttribute('aria-describedby', 'employer-search-error');
    expect(fetchMock).not.toHaveBeenCalled();

    await user.clear(nameInput);
    await user.type(nameInput, 'A');
    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent('Enter 2 to 100 visible characters from the employer name.');
    expect(nameInput).toHaveFocus();
    expect(fetchMock).not.toHaveBeenCalled();

    await user.clear(nameInput);
    await user.type(nameInput, 'A'.repeat(101));
    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent('Enter 2 to 100 visible characters from the employer name.');
    expect(nameInput).toHaveFocus();
    expect(fetchMock).not.toHaveBeenCalled();

    fireEvent.change(nameInput, { target: { value: 'Rose\u0007' } });
    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent('Enter 2 to 100 visible characters from the employer name.');
    expect(nameInput).toHaveFocus();
    expect(fetchMock).not.toHaveBeenCalled();

    await user.clear(nameInput);
    await user.selectOptions(typeSelect, 'business');
    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent('Enter 2 to 100 visible characters from the employer name.');
    expect(nameInput).toHaveFocus();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('submits one explicit bounded search', async () => {
    const deferredSearch = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock.mockReturnValue(deferredSearch.promise);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const nameInput = screen.getByLabelText('Employer name');
    const typeSelect = screen.getByLabelText('Employer type');
    const submitButton = screen.getByRole('button', { name: 'Search employers' });

    fireEvent.change(nameInput, { target: { value: 'Rose' } });
    fireEvent.change(typeSelect, { target: { value: 'business' } });
    fireEvent.click(submitButton);

    expect(searchEmployersMock).toHaveBeenCalledTimes(1);
    expect(searchEmployersMock.mock.calls[0]?.[0]).toMatchObject({
      displayNameQuery: 'Rose',
      employerType: 'business',
    });
    expect(searchEmployersMock.mock.calls[0]?.[0].signal).toBeInstanceOf(AbortSignal);
    expect(screen.getByRole('status')).toHaveTextContent('Searching employers.');
    expect(screen.getByText('Submitted search: Rose · Business')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();

    fireEvent.click(submitButton);
    expect(searchEmployersMock).toHaveBeenCalledTimes(1);

    fireEvent.change(nameInput, { target: { value: 'Rose Staffing' } });

    expect(submitButton).toBeEnabled();
    expect(screen.getByDisplayValue('Rose Staffing')).toBeInTheDocument();
    expect(screen.getByText('Submitted search: Rose · Business')).toBeInTheDocument();
    expect(searchEmployersMock).toHaveBeenCalledTimes(1);

    act(() => {
      deferredSearch.resolve({
        ok: false,
        failure: { kind: 'unexpected' },
      });
    });

    await waitFor(() => {
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });
  });

  it('renders an accepted empty page safely', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: { items: [], nextCursor: null },
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Ghost Rose');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));

    const emptyHeading = await screen.findByRole('heading', { name: 'No matching employers' });

    expect(emptyHeading).toHaveFocus();
    expect(screen.getByText('Try a different employer name fragment or clear the employer type filter.')).toBeInTheDocument();
    expect(screen.queryByText('Ghost Rose')).not.toBeInTheDocument();
    expect(screen.queryByRole('status', { name: /searching employers/i })).not.toBeInTheDocument();
  });

  it('renders minimized accepted results', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '11111111-1111-4111-8111-111111111111',
            employerType: 'business',
            displayName: '<img src=x onerror=alert(1)> Synthetic Rose Staffing',
            lifecycleStatus: 'draft',
          },
          {
            employerId: '22222222-2222-4222-8222-222222222222',
            employerType: 'household',
            displayName: 'Household Lantern',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Rose');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));

    const resultsHeading = await screen.findByRole('heading', { name: 'Search results' });
    const resultsRegion = screen.getByRole('region', { name: 'Search results' });

    expect(resultsHeading).toHaveFocus();
    expect(screen.getByRole('button', { name: '<img src=x onerror=alert(1)> Synthetic Rose Staffing' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Household Lantern' })).toBeInTheDocument();
    expect(within(resultsRegion).getByText('Business')).toBeInTheDocument();
    expect(within(resultsRegion).getAllByText('Draft')).toHaveLength(2);
    expect(screen.queryByText('11111111-1111-4111-8111-111111111111')).not.toBeInTheDocument();
    expect(screen.queryByText('2026-08-05T07:15:00Z')).not.toBeInTheDocument();
    expect(document.querySelector('img')).toBeNull();
  });

  it('disambiguates duplicate result names for assistive technology', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '24242424-2424-4242-8242-242424242424',
            employerType: 'business',
            displayName: 'Duplicate Rose',
            lifecycleStatus: 'draft',
          },
          {
            employerId: '25252525-2525-4252-8252-252525252525',
            employerType: 'household',
            displayName: 'Duplicate Rose',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Duplicate');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));

    expect(await screen.findByRole('button', { name: 'Duplicate Rose, Business, Draft' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Duplicate Rose, Household, Draft' })).toBeInTheDocument();
    expect(screen.queryAllByRole('button', { name: 'Duplicate Rose' })).toHaveLength(0);
  });

  it('maps search failures to bounded localized states', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'validation' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'forbidden' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unavailable' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unavailable' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unexpected' } });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const nameInput = screen.getByLabelText('Employer name');
    const submitButton = screen.getByRole('button', { name: 'Search employers' });

    await user.type(nameInput, 'Rose');
    await user.click(submitButton);

    let failureHeading = await screen.findByRole('heading', { name: 'Search could not run' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('Review the employer name fragment or employer type and try again.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry search' })).not.toBeInTheDocument();

    await user.click(submitButton);

    failureHeading = await screen.findByRole('heading', { name: 'Search is not available for this staff session' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('This staff session is not allowed to run employer searches.')).toBeInTheDocument();

    await user.click(submitButton);

    failureHeading = await screen.findByRole('heading', { name: 'Search requires a fresh staff action' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('Run the employer search again before continuing from this workspace state.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry search' })).not.toBeInTheDocument();

    await user.click(submitButton);

    failureHeading = await screen.findByRole('heading', { name: 'Search is temporarily unavailable' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('Retry the same employer search when the service becomes available.')).toBeInTheDocument();

    const retryButton = screen.getByRole('button', { name: 'Retry search' });
    await user.click(retryButton);

    expect(searchEmployersMock).toHaveBeenNthCalledWith(
      5,
      expect.objectContaining({
        displayNameQuery: 'Rose',
        employerType: undefined,
      }),
    );

    await user.click(submitButton);

    failureHeading = await screen.findByRole('heading', { name: 'Search response could not be used' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('Retry the search or change the filters before trying again.')).toBeInTheDocument();
    expect(screen.queryByText('503 database offline')).not.toBeInTheDocument();
  });

  it('invalidates pending base search on supersession edit and unmount', async () => {
    const firstSearch = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const secondSearch = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock.mockReturnValueOnce(firstSearch.promise).mockReturnValueOnce(secondSearch.promise);

    const { unmount } = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const nameInput = screen.getByLabelText('Employer name');
    const submitButton = screen.getByRole('button', { name: 'Search employers' });

    fireEvent.change(nameInput, { target: { value: 'Rose' } });
    fireEvent.click(submitButton);

    const firstSignal = searchEmployersMock.mock.calls[0]?.[0].signal;
    expect(firstSignal).toBeInstanceOf(AbortSignal);
    expect(screen.getByRole('status')).toHaveTextContent('Searching employers.');

    fireEvent.change(nameInput, { target: { value: 'Rose Staffing' } });

    expect(firstSignal?.aborted).toBe(true);
    expect(screen.getByDisplayValue('Rose Staffing')).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();

    await act(async () => {
      firstSearch.resolve({
        ok: true,
        value: {
          items: [
            {
              employerId: '33333333-3333-4333-8333-333333333333',
              employerType: 'business',
              displayName: 'Late Stale Result',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });
      await firstSearch.promise;
    });

    expect(screen.queryByRole('button', { name: 'Late Stale Result' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Search results' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Search response could not be used' })).not.toBeInTheDocument();
    expect(screen.getByDisplayValue('Rose Staffing')).toBeInTheDocument();

    fireEvent.click(submitButton);

    const secondSignal = searchEmployersMock.mock.calls[1]?.[0].signal;
    expect(secondSignal).toBeInstanceOf(AbortSignal);
    expect(screen.getByRole('status')).toHaveTextContent('Searching employers.');

    unmount();
    expect(secondSignal?.aborted).toBe(true);

    await act(async () => {
      secondSearch.resolve({
        ok: false,
        failure: { kind: 'unexpected' },
      });
      await secondSearch.promise;
    });
  });

  it('keeps search values out of browser side channels', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '44444444-4444-4444-8444-444444444444',
            employerType: 'business',
            displayName: 'Synthetic Rose Privacy',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });

    const localStorageSetItem = vi.spyOn(Storage.prototype, 'setItem');
    const localStorageGetItem = vi.spyOn(Storage.prototype, 'getItem');
    const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => undefined);
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined);

    window.history.replaceState({}, '', '/employers');

    render(
      <LanguageProvider>
        <App />
      </LanguageProvider>,
    );

    const nameInput = await screen.findByLabelText('Employer name');
    const typeSelect = screen.getByLabelText('Employer type');
    const submitButton = screen.getByRole('button', { name: 'Search employers' });

    expect(nameInput).toHaveAttribute('autocomplete', 'off');
    expect(nameInput).toHaveAttribute('autocorrect', 'off');
    expect(nameInput).toHaveAttribute('autocapitalize', 'none');
    expect(nameInput).toHaveAttribute('spellcheck', 'false');

    await user.type(nameInput, 'Synthetic Rose Query');
    await user.selectOptions(typeSelect, 'business');
    await user.click(submitButton);

    await screen.findByRole('heading', { name: 'Search results' });

    expect(window.location.pathname).toBe('/employers');
    expect(window.location.search).toBe('');
    expect(window.location.hash).toBe('');
    expect(localStorageSetItem).not.toHaveBeenCalled();
    expect(localStorageGetItem).not.toHaveBeenCalled();
    expect(consoleLog).not.toHaveBeenCalled();
    expect(consoleWarn).not.toHaveBeenCalled();
    expect(consoleError).not.toHaveBeenCalled();

    const dataAttributeValues = Array.from(document.querySelectorAll<HTMLElement>('*')).flatMap((element) =>
      element.getAttributeNames()
        .filter((attributeName) => attributeName.startsWith('data-'))
        .map((attributeName) => element.getAttribute(attributeName) ?? ''),
    );

    expect(dataAttributeValues.join(' ')).not.toContain('Synthetic Rose Query');
    expect(dataAttributeValues.join(' ')).not.toContain('business');

    render(<div>SYNTHETIC_EMPLOYER_SECRET SYNTHETIC_API_CURSOR</div>);

    let redactedDiagnostic = '';

    try {
      screen.getByRole('heading', { name: 'Missing diagnostic target' });
    } catch (error) {
      redactedDiagnostic = error instanceof Error ? error.message : String(error);
    }

    expect(redactedDiagnostic).toContain(VALUE_SAFE_TESTING_LIBRARY_MESSAGE);
    expect(redactedDiagnostic).not.toContain('SYNTHETIC_EMPLOYER_SECRET');
    expect(redactedDiagnostic).not.toContain('SYNTHETIC_API_CURSOR');
  });

  it('loads the next page with the submitted filters', async () => {
    const user = userEvent.setup();
    const nextPageSearch = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '55555555-5555-4555-8555-555555555555',
              employerType: 'business',
              displayName: 'Synthetic Rose Page One',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: 'opaque-cursor-002',
        },
      })
      .mockReturnValueOnce(nextPageSearch.promise);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Rose');
    await user.selectOptions(screen.getByLabelText('Employer type'), 'business');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));

    await screen.findByRole('heading', { name: 'Search results' });

    const loadMoreButton = screen.getByRole('button', { name: 'Load more employers' });

    expect(screen.queryByText('Page 1 of 2')).not.toBeInTheDocument();
    expect(screen.queryByText('1 result')).not.toBeInTheDocument();

    await user.click(loadMoreButton);

    expect(searchEmployersMock).toHaveBeenNthCalledWith(
      2,
      expect.objectContaining({
        displayNameQuery: 'Rose',
        employerType: 'business',
        cursor: 'opaque-cursor-002',
      }),
    );
    expect(screen.queryByText('opaque-cursor-002')).not.toBeInTheDocument();

    await act(async () => {
      nextPageSearch.resolve({
        ok: false,
        failure: { kind: 'unexpected' },
      });
      await nextPageSearch.promise;
    });
  });

  it('appends unique accepted results and retires a null cursor', async () => {
    const user = userEvent.setup();
    const nextPageSearch = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '66666666-6666-4666-8666-666666666666',
              employerType: 'business',
              displayName: 'Synthetic Rose Page One',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: 'opaque-cursor-003',
        },
      })
      .mockReturnValueOnce(nextPageSearch.promise);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Rose');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));

    const resultsHeading = await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Load more employers' }));

    await act(async () => {
      nextPageSearch.resolve({
        ok: true,
        value: {
          items: [
            {
              employerId: '66666666-6666-4666-8666-666666666666',
              employerType: 'business',
              displayName: 'Synthetic Rose Page One',
              lifecycleStatus: 'draft',
            },
            {
              employerId: '77777777-7777-4777-8777-777777777777',
              employerType: 'household',
              displayName: 'Lantern Household Two',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });
      await nextPageSearch.promise;
    });

    expect(screen.getAllByRole('button', { name: 'Synthetic Rose Page One' })).toHaveLength(1);

    const appendedResultButton = screen.getByRole('button', { name: 'Lantern Household Two' });
    expect(appendedResultButton).toHaveFocus();
    expect(screen.queryByRole('button', { name: 'Load more employers' })).not.toBeInTheDocument();
    expect(resultsHeading).not.toHaveFocus();
  });

  it('invalidates pending pagination on filter edit new search and unmount', async () => {
    const user = userEvent.setup();
    const pendingPage = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const nextBaseSearch = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const trailingPage = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '88888888-8888-4888-8888-888888888888',
              employerType: 'business',
              displayName: 'Synthetic Rose Page One',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: 'opaque-cursor-004',
        },
      })
      .mockReturnValueOnce(pendingPage.promise)
      .mockReturnValueOnce(nextBaseSearch.promise)
      .mockReturnValueOnce(trailingPage.promise);

    const { unmount } = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const nameInput = screen.getByLabelText('Employer name');
    const submitButton = screen.getByRole('button', { name: 'Search employers' });

    await user.type(nameInput, 'Rose');
    await user.click(submitButton);
    await screen.findByRole('heading', { name: 'Search results' });

    await user.click(screen.getByRole('button', { name: 'Load more employers' }));

    const paginationSignal = searchEmployersMock.mock.calls[1]?.[0].signal;
    expect(paginationSignal).toBeInstanceOf(AbortSignal);

    await user.type(nameInput, ' Staffing');

    expect(paginationSignal?.aborted).toBe(true);
    expect(screen.queryByRole('button', { name: 'Load more employers' })).not.toBeInTheDocument();

    await act(async () => {
      pendingPage.resolve({
        ok: true,
        value: {
          items: [
            {
              employerId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
              employerType: 'business',
              displayName: 'Late Pagination Result',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });
      await pendingPage.promise;
    });

    expect(screen.queryByRole('button', { name: 'Late Pagination Result' })).not.toBeInTheDocument();
    expect(screen.getByDisplayValue('Rose Staffing')).toBeInTheDocument();

    await user.click(submitButton);
    expect(searchEmployersMock.mock.calls[2]?.[0]).toMatchObject({
      displayNameQuery: 'Rose Staffing',
      employerType: undefined,
      cursor: null,
    });

    await act(async () => {
      nextBaseSearch.resolve({
        ok: true,
        value: {
          items: [
            {
              employerId: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
              employerType: 'business',
              displayName: 'Fresh Base Result',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: 'opaque-cursor-006',
        },
      });
      await nextBaseSearch.promise;
    });

    await screen.findByRole('button', { name: 'Load more employers' });
    await user.click(screen.getByRole('button', { name: 'Load more employers' }));

    expect(searchEmployersMock).toHaveBeenCalledTimes(4);

    const trailingPaginationSignal = searchEmployersMock.mock.calls[3]?.[0].signal;
    expect(trailingPaginationSignal).toBeInstanceOf(AbortSignal);

    unmount();

    expect(trailingPaginationSignal?.aborted).toBe(true);

    await act(async () => {
      trailingPage.resolve({
        ok: false,
        failure: { kind: 'unexpected' },
      });
      await trailingPage.promise;
    });
  });

  it('preserves results and cursor retry after page failure', async () => {
    const user = userEvent.setup();
    const failedPage = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const retriedPage = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
              employerType: 'business',
              displayName: 'Synthetic Rose Page One',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: 'opaque-cursor-007',
        },
      })
      .mockReturnValueOnce(failedPage.promise)
      .mockReturnValueOnce(retriedPage.promise);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Rose');
    await user.selectOptions(screen.getByLabelText('Employer type'), 'business');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });

    await user.click(screen.getByRole('button', { name: 'Load more employers' }));

    await act(async () => {
      failedPage.resolve({
        ok: false,
        failure: { kind: 'unavailable' },
      });
      await failedPage.promise;
    });

    expect(screen.getByRole('button', { name: 'Synthetic Rose Page One' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Load more employers' })).not.toBeInTheDocument();

    const retryPageButton = screen.getByRole('button', { name: 'Retry loading more employers' });
    expect(retryPageButton).toBeInTheDocument();

    await user.click(retryPageButton);

    expect(searchEmployersMock).toHaveBeenNthCalledWith(
      3,
      expect.objectContaining({
        displayNameQuery: 'Rose',
        employerType: 'business',
        cursor: 'opaque-cursor-007',
      }),
    );

    await act(async () => {
      retriedPage.resolve({
        ok: true,
        value: {
          items: [
            {
              employerId: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
              employerType: 'household',
              displayName: 'Recovered Page Result',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });
      await retriedPage.promise;
    });

    expect(screen.getByRole('button', { name: 'Recovered Page Result' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry loading more employers' })).not.toBeInTheDocument();
  });

  it('keeps accepted results while mapping pagination failures by classification', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    const firstPage = {
      ok: true as const,
      value: {
        items: [
          {
            employerId: '21212121-2121-4212-8212-212121212121',
            employerType: 'business' as const,
            displayName: 'Pagination Anchor',
            lifecycleStatus: 'draft' as const,
          },
        ],
        nextCursor: 'opaque-cursor-008',
      },
    };

    searchEmployersMock
      .mockResolvedValueOnce(firstPage)
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'validation' } })
      .mockResolvedValueOnce(firstPage)
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'forbidden' } })
      .mockResolvedValueOnce(firstPage)
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } })
      .mockResolvedValueOnce(firstPage)
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unavailable' } })
      .mockResolvedValueOnce(firstPage)
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unexpected' } });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Rose');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });

    const loadMore = screen.getByRole('button', { name: 'Load more employers' });

    await user.click(loadMore);
    let pageFailureHeading = await screen.findByRole('heading', { name: 'More employers could not load' });
    expect(pageFailureHeading).toBeInTheDocument();
    expect(screen.getByText('Run the employer search again before loading more employers.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Pagination Anchor' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry loading more employers' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Load more employers' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Load more employers' }));
    pageFailureHeading = await screen.findByRole('heading', { name: 'More employers are not available for this staff session' });
    expect(pageFailureHeading).toBeInTheDocument();
    expect(screen.getByText('This staff session is not allowed to load more employers for the current search.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Pagination Anchor' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry loading more employers' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Load more employers' }));
    pageFailureHeading = await screen.findByRole('heading', { name: 'More employers require a fresh search' });
    expect(pageFailureHeading).toBeInTheDocument();
    expect(screen.getByText('Run the employer search again before loading more employers.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Pagination Anchor' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry loading more employers' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Load more employers' }));
    pageFailureHeading = await screen.findByRole('heading', { name: 'More employers are temporarily unavailable' });
    expect(pageFailureHeading).toBeInTheDocument();
    expect(screen.getByText('Retry loading more employers when the service becomes available.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Retry loading more employers' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Pagination Anchor' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Load more employers' }));
    pageFailureHeading = await screen.findByRole('heading', { name: 'More employers response could not be used' });
    expect(pageFailureHeading).toBeInTheDocument();
    expect(screen.getByText('Run the employer search again before loading more employers.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Pagination Anchor' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry loading more employers' })).not.toBeInTheDocument();
    expect(screen.queryByText('503 database offline')).not.toBeInTheDocument();
  });

  it('loads one exact detail for the selected result', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();

    const deferredDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();

    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
            employerType: 'business',
            displayName: 'Detail Selection Anchor',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock.mockReturnValue(deferredDetail.promise);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Rose');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('button', { name: 'Detail Selection Anchor' });

    await user.click(screen.getByRole('button', { name: 'Detail Selection Anchor' }));

    expect(getEmployerMock).toHaveBeenCalledTimes(1);
    const detailCall = getEmployerMock.mock.calls[0];
    expect(detailCall?.[0]).toBe('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee');
    expect(detailCall?.[1]?.signal).toBeInstanceOf(AbortSignal);
    const workArea = screen.getByRole('region', { name: 'Work area' });
    const findEmployer = screen.getByRole('region', { name: 'Find an employer' });
    const loadingDetail = within(workArea).getByRole('region', { name: 'Employer detail' });
    expect(within(loadingDetail).getByRole('heading', { name: 'Employer detail' })).toBeInTheDocument();
    expect(within(loadingDetail).getByRole('status')).toHaveTextContent('Loading employer detail.');
    expect(within(findEmployer).queryByRole('region', { name: 'Employer detail' })).not.toBeInTheDocument();

    await act(async () => {
      deferredDetail.resolve(null);
      await deferredDetail.promise;
    });
  });

  it('renders only matching minimized detail', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();

    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: 'ffffffff-ffff-4fff-8fff-ffffffffffff',
            employerType: 'business',
            displayName: 'Detail Display Anchor',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock.mockResolvedValue({
      ok: true,
      value: {
        employerId: 'ffffffff-ffff-4fff-8fff-ffffffffffff',
        employerType: 'business',
        displayName: '<img src=x onerror=alert(1)> Detail Rendering Rose',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 1,
        updatedAt: '2026-08-11T04:00:00Z',
      },
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Rose');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await user.click(screen.getByRole('button', { name: 'Detail Display Anchor' }));

    const detailHeading = await screen.findByRole('heading', { name: 'Employer detail' });
    expect(detailHeading).toHaveFocus();

    const detailRegion = screen.getByRole('region', { name: 'Employer detail' });
    const workArea = screen.getByRole('region', { name: 'Work area' });
    const findEmployer = screen.getByRole('region', { name: 'Find an employer' });

    expect(within(workArea).getByRole('region', { name: 'Employer detail' })).toBe(detailRegion);
    expect(within(findEmployer).queryByRole('region', { name: 'Employer detail' })).not.toBeInTheDocument();
    expect(within(detailRegion).getByText('Name')).toBeInTheDocument();
    expect(within(detailRegion).getByText('<img src=x onerror=alert(1)> Detail Rendering Rose')).toBeInTheDocument();
    expect(within(detailRegion).getByText('Type')).toBeInTheDocument();
    expect(within(detailRegion).getByText('Business')).toBeInTheDocument();
    expect(within(detailRegion).getByText('Lifecycle')).toBeInTheDocument();
    expect(within(detailRegion).getByText('Draft')).toBeInTheDocument();
    expect(within(detailRegion).getByText('Source')).toBeInTheDocument();
    expect(within(detailRegion).getByText('Staff entry')).toBeInTheDocument();
    expect(within(detailRegion).queryByText('ffffffff-ffff-4fff-8fff-ffffffffffff')).not.toBeInTheDocument();
    expect(within(detailRegion).queryByText('2026-08-05T07:15:00Z')).not.toBeInTheDocument();
    expect(document.querySelector('img')).toBeNull();
  });

  it('edits only the selected exact draft Employer', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();

    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '71717171-7171-4171-8171-717171717171',
            employerType: 'business',
            displayName: 'Selected Draft Anchor',
            lifecycleStatus: 'draft',
          },
          {
            employerId: '81818181-8181-4181-8181-818181818181',
            employerType: 'household',
            displayName: 'Unselected Draft Anchor',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock.mockResolvedValue({
      ok: true,
      value: {
        employerId: '71717171-7171-4171-8171-717171717171',
        employerType: 'business',
        displayName: 'Selected Draft Anchor',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 7,
        updatedAt: '2026-08-11T04:10:00Z',
      },
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.queryByRole('button', { name: 'Edit draft employer' })).not.toBeInTheDocument();

    await user.type(screen.getByLabelText('Employer name'), 'Draft');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await user.click(screen.getByRole('button', { name: 'Selected Draft Anchor' }));

    await screen.findByRole('region', { name: 'Employer detail' });
    const revisionEditButton = screen.getByRole('button', { name: 'Edit draft employer' });
    expect(revisionEditButton).toBeInTheDocument();

    await user.click(revisionEditButton);

    expect(screen.getByRole('form', { name: 'Revise draft employer' })).toBeInTheDocument();
    expect(screen.getByLabelText('Revision employer type')).toHaveValue('business');
    expect(screen.getByLabelText('Revision employer name')).toHaveValue('Selected Draft Anchor');
    expect(screen.queryByDisplayValue('Unselected Draft Anchor')).not.toBeInTheDocument();
  });

  it('serializes create and revision with one workspace command lock', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    createEmployerMock.mockReset();
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const deferredCreate = createDeferredPromise<Awaited<ReturnType<typeof createEmployer>>>();
    const deferredRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '91919191-9191-4191-8191-919191919191',
            employerType: 'business',
            displayName: 'Workspace Lock Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock.mockResolvedValue({
      ok: true,
      value: {
        employerId: '91919191-9191-4191-8191-919191919191',
        employerType: 'business',
        displayName: 'Workspace Lock Draft',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 7,
        updatedAt: '2026-08-11T05:00:00Z',
      },
    });
    createEmployerMock.mockReturnValueOnce(deferredCreate.promise);
    reviseEmployerMock.mockReturnValueOnce(deferredRevision.promise);

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa')
      .mockReturnValueOnce('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Draft');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await user.click(screen.getByRole('button', { name: 'Workspace Lock Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Workspace Revision Attempt');

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'household');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Workspace Create Attempt');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));

    expect(createEmployerMock).toHaveBeenCalledTimes(1);
    expect(createEmployerMock).toHaveBeenCalledWith({
      commandId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
      employerType: 'household',
      displayName: 'Workspace Create Attempt',
    });
    expect(screen.getByRole('button', { name: 'Save draft employer revision' })).toBeDisabled();

    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));
    expect(reviseEmployerMock).not.toHaveBeenCalled();

    await act(async () => {
      deferredCreate.resolve({
        ok: true,
        value: {
          employerId: '92929292-9292-4292-8292-929292929292',
          employerType: 'household',
          displayName: 'Workspace Create Attempt',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
        },
      });
      await deferredCreate.promise;
    });

    await user.type(screen.getByLabelText('Employer name'), 'Draft');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await user.click(screen.getByRole('button', { name: 'Workspace Lock Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });

    const revisionEntryButton = screen.queryByRole('button', { name: 'Edit draft employer' });
    if (revisionEntryButton !== null) {
      await user.click(revisionEntryButton);
    } else {
      expect(screen.getByRole('form', { name: 'Revise draft employer' })).toBeInTheDocument();
    }
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Workspace Revision Attempt');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    expect(reviseEmployerMock).toHaveBeenCalledTimes(1);
    expect(reviseEmployerMock).toHaveBeenCalledWith({
      employerId: '91919191-9191-4191-8191-919191919191',
      commandId: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
      expectedVersion: 7,
      employerType: 'business',
      displayName: 'Workspace Revision Attempt',
    });
    expect(screen.getByLabelText('Draft employer type')).toBeDisabled();
    expect(screen.getByLabelText('Draft employer display name')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create draft employer' })).toBeDisabled();

    await act(async () => {
      deferredRevision.resolve({
        ok: true,
        value: {
          detail: {
            employerId: '91919191-9191-4191-8191-919191919191',
            employerType: 'business',
            displayName: 'Workspace Revision Attempt',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T05:10:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });
      await deferredRevision.promise;
    });

    randomUuidSpy.mockRestore();
  });

  it('blocks revision during pending unknown conflict and recovery create authority', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    createEmployerMock.mockReset();
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const pendingCreate = createDeferredPromise<Awaited<ReturnType<typeof createEmployer>>>();
    const abandonmentSearch = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();

    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '93939393-9393-4393-8393-939393939393',
              employerType: 'business',
              displayName: 'Create Authority Draft',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      })
      .mockReturnValueOnce(abandonmentSearch.promise);
    getEmployerMock.mockResolvedValue({
      ok: true,
      value: {
        employerId: '93939393-9393-4393-8393-939393939393',
        employerType: 'business',
        displayName: 'Create Authority Draft',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 7,
        updatedAt: '2026-08-11T05:20:00Z',
      },
    });
    createEmployerMock
      .mockReturnValueOnce(pendingCreate.promise)
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('cccccccc-cccc-4ccc-8ccc-cccccccccccc')
      .mockReturnValueOnce('dddddddd-dddd-4ddd-8ddd-dddddddddddd');
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Draft');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await user.click(screen.getByRole('button', { name: 'Create Authority Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));

    const revisionNameInput = screen.getByLabelText('Revision employer name');
    const revisionSubmitButton = screen.getByRole('button', { name: 'Save draft employer revision' });

    await user.clear(revisionNameInput);
    await user.type(revisionNameInput, 'Blocked Revision Attempt');
    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Create Lock Attempt');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));

    expect(createEmployerMock).toHaveBeenCalledTimes(1);
    expect(revisionNameInput).toBeDisabled();
    expect(revisionSubmitButton).toBeDisabled();

    await user.click(revisionSubmitButton);
    expect(reviseEmployerMock).not.toHaveBeenCalled();

    await act(async () => {
      pendingCreate.resolve({ ok: false, failure: { kind: 'unknown_outcome' } });
      await pendingCreate.promise;
    });

    const unknownHeading = await screen.findByRole('heading', { name: 'Create outcome is unknown' });
    const unknownRegion = unknownHeading.closest('section');
    expect(unknownRegion).not.toBeNull();
    expect(revisionNameInput).toBeDisabled();
    expect(revisionSubmitButton).toBeDisabled();

    await user.click(within(unknownRegion as HTMLElement).getByRole('button', { name: 'Abandon unknown create and search' }));
    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(revisionNameInput).toBeDisabled();
    expect(revisionSubmitButton).toBeDisabled();

    await act(async () => {
      abandonmentSearch.resolve({ ok: true, value: { items: [], nextCursor: null } });
      await abandonmentSearch.promise;
    });

    expect(screen.queryByRole('heading', { name: 'Create outcome is unknown' })).not.toBeInTheDocument();
    expect(revisionNameInput).not.toBeDisabled();
    expect(revisionSubmitButton).not.toBeDisabled();

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Create Conflict Attempt');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));

    const conflictHeading = await screen.findByRole('heading', { name: 'Create is blocked until you search first' });
    expect(conflictHeading).toBeInTheDocument();
    expect(revisionNameInput).toBeDisabled();
    expect(revisionSubmitButton).toBeDisabled();
    expect(reviseEmployerMock).not.toHaveBeenCalled();

    randomUuidSpy.mockRestore();
    confirmSpy.mockRestore();
  });

  it('blocks create during pending unknown conflict and recovery revision authority', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    createEmployerMock.mockReset();
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const pendingRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '94949494-9494-4494-8494-949494949494',
            employerType: 'business',
            displayName: 'Revision Authority Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock.mockResolvedValue({
      ok: true,
      value: {
        employerId: '94949494-9494-4494-8494-949494949494',
        employerType: 'business',
        displayName: 'Revision Authority Draft',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 7,
        updatedAt: '2026-08-11T05:30:00Z',
      },
    });
    reviseEmployerMock
      .mockReturnValueOnce(pendingRevision.promise)
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'stale' } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee')
      .mockReturnValueOnce('ffffffff-ffff-4fff-8fff-ffffffffffff')
      .mockReturnValueOnce('abababab-abab-4bab-8bab-abababababab');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Draft');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await user.click(screen.getByRole('button', { name: 'Revision Authority Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Pending Revision Lock');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    expect(reviseEmployerMock).toHaveBeenCalledTimes(1);
    expect(screen.getByLabelText('Draft employer type')).toBeDisabled();
    expect(screen.getByLabelText('Draft employer display name')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create draft employer' })).toBeDisabled();

    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));
    expect(createEmployerMock).not.toHaveBeenCalled();

    await act(async () => {
      pendingRevision.resolve({ ok: false, failure: { kind: 'unknown_outcome' } });
      await pendingRevision.promise;
    });

    const unknownHeading = await screen.findByRole('heading', { name: 'Revision outcome is unknown' });
    const unknownRegion = unknownHeading.closest('section');
    expect(unknownRegion).not.toBeNull();
    expect(screen.getByLabelText('Draft employer type')).toBeDisabled();
    expect(screen.getByLabelText('Draft employer display name')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create draft employer' })).toBeDisabled();

    await user.click(within(unknownRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));
    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Conflict Revision Lock');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const conflictHeading = await screen.findByRole('heading', {
      name: 'Revision is blocked until current employer detail reloads',
    });
    const conflictRegion = conflictHeading.closest('section');
    expect(conflictRegion).not.toBeNull();
    expect(screen.getByLabelText('Draft employer type')).toBeDisabled();
    expect(screen.getByLabelText('Draft employer display name')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create draft employer' })).toBeDisabled();

    await user.click(within(conflictRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));
    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Stale Revision Lock');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const staleHeading = await screen.findByRole('heading', {
      name: 'Revision requires current employer detail before editing can continue',
    });
    expect(staleHeading).toBeInTheDocument();
    expect(screen.getByLabelText('Draft employer type')).toBeDisabled();
    expect(screen.getByLabelText('Draft employer display name')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create draft employer' })).toBeDisabled();
    expect(createEmployerMock).not.toHaveBeenCalled();

    randomUuidSpy.mockRestore();
  });

  it('blocks same-tick create revision and repeated handler re-entry before React rerenders', async () => {
    const createEmployerMock = vi.mocked(createEmployer);
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    createEmployerMock.mockReset();
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const pendingCreate = createDeferredPromise<Awaited<ReturnType<typeof createEmployer>>>();

    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '95959595-9595-4595-8595-959595959595',
            employerType: 'business',
            displayName: 'Same Tick Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock.mockResolvedValue({
      ok: true,
      value: {
        employerId: '95959595-9595-4595-8595-959595959595',
        employerType: 'business',
        displayName: 'Same Tick Draft',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 7,
        updatedAt: '2026-08-11T05:40:00Z',
      },
    });
    createEmployerMock.mockReturnValueOnce(pendingCreate.promise);

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('12121212-1212-4121-8121-121212121212')
      .mockReturnValueOnce('34343434-3434-4343-8343-343434343434');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await userEvent.type(screen.getByLabelText('Employer name'), 'Draft');
    await userEvent.click(screen.getByRole('button', { name: 'Search employers' }));
    await userEvent.click(screen.getByRole('button', { name: 'Same Tick Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await userEvent.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await userEvent.clear(screen.getByLabelText('Revision employer name'));
    await userEvent.type(screen.getByLabelText('Revision employer name'), 'Blocked Same Tick Revision');
    await userEvent.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await userEvent.type(screen.getByLabelText('Draft employer display name'), 'Same Tick Create Attempt');

    const createSubmitButton = screen.getByRole('button', { name: 'Create draft employer' });
    const revisionSubmitButton = screen.getByRole('button', { name: 'Save draft employer revision' });

    fireEvent.click(createSubmitButton);
    fireEvent.click(createSubmitButton);
    fireEvent.click(revisionSubmitButton);

    expect(createEmployerMock).toHaveBeenCalledTimes(1);
    expect(createEmployerMock).toHaveBeenCalledWith({
      commandId: '12121212-1212-4121-8121-121212121212',
      employerType: 'business',
      displayName: 'Same Tick Create Attempt',
    });
    expect(reviseEmployerMock).not.toHaveBeenCalled();

    randomUuidSpy.mockRestore();
  });

  it('disables create search selection pagination and competing edit authority while revision is frozen', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    createEmployerMock.mockReset();
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '96969696-9696-4696-8696-969696969696',
            employerType: 'business',
            displayName: 'Frozen Revision Draft',
            lifecycleStatus: 'draft',
          },
          {
            employerId: '97979797-9797-4797-8797-979797979797',
            employerType: 'household',
            displayName: 'Competing Draft Target',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: 'opaque-next-page',
      },
    });
    getEmployerMock.mockResolvedValue({
      ok: true,
      value: {
        employerId: '96969696-9696-4696-8696-969696969696',
        employerType: 'business',
        displayName: 'Frozen Revision Draft',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 7,
        updatedAt: '2026-08-11T05:50:00Z',
      },
    });
    reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } });

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('56565656-5656-4565-8565-565656565656');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Draft');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await user.click(screen.getByRole('button', { name: 'Frozen Revision Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Frozen Unknown Revision');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const unknownHeading = await screen.findByRole('heading', { name: 'Revision outcome is unknown' });
    expect(unknownHeading).toBeInTheDocument();

    expect(screen.getByLabelText('Draft employer type')).toBeDisabled();
    expect(screen.getByLabelText('Draft employer display name')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create draft employer' })).toBeDisabled();
    expect(screen.getByLabelText('Employer name')).toBeDisabled();
    expect(screen.getByLabelText('Employer type')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Search employers' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Competing Draft Target' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Load more employers' })).toBeDisabled();

    await user.click(screen.getByRole('button', { name: 'Competing Draft Target' }));
    await user.click(screen.getByRole('button', { name: 'Load more employers' }));
    expect(getEmployerMock).toHaveBeenCalledTimes(1);
    expect(searchEmployersMock).toHaveBeenCalledTimes(1);

    randomUuidSpy.mockRestore();
  });

  it('revision success invalidates prior search results cursor and detail before exact refresh', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const pendingRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();
    const refreshDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();

    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '98989898-9898-4989-8989-989898989898',
            employerType: 'business',
            displayName: 'Refresh Boundary Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: 'cursor-before-revision-success',
      },
    });
    getEmployerMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '98989898-9898-4989-8989-989898989898',
          employerType: 'business',
          displayName: 'Refresh Boundary Draft',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 7,
          updatedAt: '2026-08-11T06:00:00Z',
        },
      })
      .mockReturnValueOnce(refreshDetail.promise);
    reviseEmployerMock.mockReturnValueOnce(pendingRevision.promise);

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('78787878-7878-4787-8787-787878787878');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Refresh');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    expect(screen.getByText('Submitted search: Refresh')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Load more employers' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Refresh Boundary Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Refresh Boundary Draft Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    await act(async () => {
      pendingRevision.resolve({
        ok: true,
        value: {
          detail: {
            employerId: '98989898-9898-4989-8989-989898989898',
            employerType: 'business',
            displayName: 'Refresh Boundary Draft Revised',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T06:05:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });
      await pendingRevision.promise;
    });

    expect(screen.queryByRole('heading', { name: 'Search results' })).not.toBeInTheDocument();
    expect(screen.queryByText('Submitted search: Refresh')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Load more employers' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Refresh Boundary Draft' })).not.toBeInTheDocument();
    const refreshStatusRegion = screen.getByRole('region', { name: 'Employer detail' });
    expect(within(refreshStatusRegion).getByRole('status')).toHaveTextContent('Loading employer detail.');
    expect(getEmployerMock).toHaveBeenCalledTimes(2);

    randomUuidSpy.mockRestore();
  });

  it('confirmed revision success performs exact detail refresh from a clean invalidated workspace state', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const refreshDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const pendingRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '90909090-9090-4090-8090-909090909090',
            employerType: 'business',
            displayName: 'Refresh Current Truth Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: 'cursor-before-clean-refresh',
      },
    });
    getEmployerMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '90909090-9090-4090-8090-909090909090',
          employerType: 'business',
          displayName: 'Refresh Current Truth Draft',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 7,
          updatedAt: '2026-08-11T06:10:00Z',
        },
      })
      .mockReturnValueOnce(refreshDetail.promise);
    reviseEmployerMock.mockReturnValueOnce(pendingRevision.promise);

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('79797979-7979-4797-8797-797979797979');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Refresh');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Refresh Current Truth Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Refresh Current Truth Draft Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    await act(async () => {
      pendingRevision.resolve({
        ok: true,
        value: {
          detail: {
            employerId: '90909090-9090-4090-8090-909090909090',
            employerType: 'business',
            displayName: 'Refresh Current Truth Draft Revised',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T06:15:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });
      await pendingRevision.promise;
    });

    expect(screen.queryByRole('heading', { name: 'Search results' })).not.toBeInTheDocument();
    expect(screen.queryByText('Submitted search: Refresh')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Load more employers' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Refresh Current Truth Draft' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Edit draft employer' })).not.toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');
    expect(getEmployerMock).toHaveBeenCalledTimes(2);
    const secondGetEmployerCall = getEmployerMock.mock.calls[1];
    expect(secondGetEmployerCall?.[0]).toBe('90909090-9090-4090-8090-909090909090');
    expect(secondGetEmployerCall?.[1]?.signal).toBeInstanceOf(AbortSignal);

    await act(async () => {
      refreshDetail.resolve({
        ok: true,
        value: {
          employerId: '90909090-9090-4090-8090-909090909090',
          employerType: 'business',
          displayName: 'Refresh Current Truth Draft Revised',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 8,
          updatedAt: '2026-08-11T06:15:00Z',
        },
      });
      await refreshDetail.promise;
    });

    const refreshedDetailRegion = await screen.findByRole('region', { name: 'Employer detail' });
    expect(within(refreshedDetailRegion).getByText('Refresh Current Truth Draft Revised')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Search results' })).not.toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('confirmed revision refresh failure does not overstate refreshed current work', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const refreshDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const pendingRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '92929292-9292-4292-8292-929292929292',
            employerType: 'business',
            displayName: 'Refresh Failure Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '92929292-9292-4292-8292-929292929292',
          employerType: 'business',
          displayName: 'Refresh Failure Draft',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 4,
          updatedAt: '2026-08-11T06:10:00Z',
        },
      })
      .mockReturnValueOnce(refreshDetail.promise);
    reviseEmployerMock.mockReturnValueOnce(pendingRevision.promise);

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('82828282-8282-4828-8828-828282828282');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Refresh');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Refresh Failure Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });

    const currentWork = screen.getByRole('region', { name: 'Current work' });
    expect(within(currentWork).getByText('Reviewing selected draft employer.')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Refresh Failure Draft Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    await act(async () => {
      pendingRevision.resolve({
        ok: true,
        value: {
          detail: {
            employerId: '92929292-9292-4292-8292-929292929292',
            employerType: 'business',
            displayName: 'Refresh Failure Draft Revised',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 5,
            updatedAt: '2026-08-11T06:15:00Z',
          },
          resultVersion: 5,
          replayed: false,
        },
      });
      await pendingRevision.promise;
    });

    await act(async () => {
      refreshDetail.resolve({ ok: false, failure: { kind: 'unavailable' } });
      await refreshDetail.promise;
    });

    expect(await screen.findByRole('heading', { name: 'Current employer detail could not be refreshed' })).toBeInTheDocument();
    expect(currentWork).toHaveTextContent('Refresh Failure Draft');
    expect(within(currentWork).getByText('Reviewing selected draft employer.')).toBeInTheDocument();
    expect(
      within(currentWork).getByText('Use Edit draft employer only when the current detail needs a deliberate revision.'),
    ).toBeInTheDocument();
    expect(within(currentWork).queryByText('Revision saved in this session.')).not.toBeInTheDocument();
    expect(within(currentWork).queryByText(/refreshed after save/i)).not.toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('revision success retires every active read before clearing results cursor failures submitted search and old selection', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const pendingPage = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const refreshDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const pendingRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '91919191-9191-4191-8191-919191919191',
              employerType: 'business',
              displayName: 'Retire Active Reads Draft',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: 'cursor-with-pending-page',
        },
      })
      .mockReturnValueOnce(pendingPage.promise);
    getEmployerMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '91919191-9191-4191-8191-919191919191',
          employerType: 'business',
          displayName: 'Retire Active Reads Draft',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 7,
          updatedAt: '2026-08-11T06:20:00Z',
        },
      })
      .mockReturnValueOnce(refreshDetail.promise);
    reviseEmployerMock.mockReturnValueOnce(pendingRevision.promise);

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('80808080-8080-4080-8080-808080808080');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Retire');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Retire Active Reads Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Retired Reads Revised');

    await user.click(screen.getByRole('button', { name: 'Load more employers' }));
    const paginationSignal = searchEmployersMock.mock.calls[1]?.[0].signal;
    expect(paginationSignal).toBeInstanceOf(AbortSignal);

    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    await act(async () => {
      pendingRevision.resolve({
        ok: true,
        value: {
          detail: {
            employerId: '91919191-9191-4191-8191-919191919191',
            employerType: 'business',
            displayName: 'Retired Reads Revised',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T06:25:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });
      await pendingRevision.promise;
    });

    expect(paginationSignal?.aborted).toBe(true);
    expect(screen.queryByRole('heading', { name: 'Search results' })).not.toBeInTheDocument();
    expect(screen.queryByText('Submitted search: Retire')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Load more employers' })).not.toBeInTheDocument();

    await act(async () => {
      pendingPage.resolve({
        ok: true,
        value: {
          items: [
            {
              employerId: '92929292-9292-4292-8292-929292929292',
              employerType: 'household',
              displayName: 'Late Appended Result',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });
      await pendingPage.promise;
    });

    expect(screen.queryByText('Late Appended Result')).not.toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');
    expect(getEmployerMock).toHaveBeenCalledTimes(2);

    await act(async () => {
      refreshDetail.resolve({
        ok: true,
        value: {
          employerId: '91919191-9191-4191-8191-919191919191',
          employerType: 'business',
          displayName: 'Retired Reads Revised',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 8,
          updatedAt: '2026-08-11T06:25:00Z',
        },
      });
      await refreshDetail.promise;
    });

    expect(screen.queryByText('Late Appended Result')).not.toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('late search pagination and detail completions cannot repaint after revision acknowledgement', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const pendingPage = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const pendingStaleDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const refreshDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const pendingRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '93939393-9393-4393-8393-939393939393',
              employerType: 'business',
              displayName: 'Late Paint Guard Draft',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: 'cursor-with-late-read-risk',
        },
      })
      .mockReturnValueOnce(pendingPage.promise);
    getEmployerMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '93939393-9393-4393-8393-939393939393',
          employerType: 'business',
          displayName: 'Late Paint Guard Draft',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 7,
          updatedAt: '2026-08-11T06:30:00Z',
        },
      })
      .mockReturnValueOnce(pendingStaleDetail.promise)
      .mockReturnValueOnce(refreshDetail.promise);
    reviseEmployerMock.mockReturnValueOnce(pendingRevision.promise);

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('81818181-8181-4181-8181-818181818181');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Late');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Late Paint Guard Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Late Paint Guard Revised');

    await user.click(screen.getByRole('button', { name: 'Load more employers' }));
    const paginationSignal = searchEmployersMock.mock.calls[1]?.[0].signal;
    expect(paginationSignal).toBeInstanceOf(AbortSignal);

    await user.click(screen.getByRole('button', { name: 'Late Paint Guard Draft' }));
    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');
    const staleDetailSignal = getEmployerMock.mock.calls[1]?.[1]?.signal;
    expect(staleDetailSignal).toBeInstanceOf(AbortSignal);

    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    await act(async () => {
      pendingRevision.resolve({
        ok: true,
        value: {
          detail: {
            employerId: '93939393-9393-4393-8393-939393939393',
            employerType: 'business',
            displayName: 'Late Paint Guard Revised',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T06:35:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });
      await pendingRevision.promise;
    });

    expect(paginationSignal?.aborted).toBe(true);
    expect(staleDetailSignal?.aborted).toBe(true);

    await act(async () => {
      pendingPage.resolve({
        ok: true,
        value: {
          items: [
            {
              employerId: '94949494-9494-4494-8494-949494949494',
              employerType: 'household',
              displayName: 'Late Pagination Paint',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });
      pendingStaleDetail.resolve({
        ok: true,
        value: {
          employerId: '93939393-9393-4393-8393-939393939393',
          employerType: 'business',
          displayName: 'Late Detail Paint',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 7,
          updatedAt: '2026-08-11T06:31:00Z',
        },
      });
      await pendingPage.promise;
      await pendingStaleDetail.promise;
    });

    expect(screen.queryByText('Late Pagination Paint')).not.toBeInTheDocument();
    expect(screen.queryByText('Late Detail Paint')).not.toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');

    await act(async () => {
      refreshDetail.resolve({
        ok: true,
        value: {
          employerId: '93939393-9393-4393-8393-939393939393',
          employerType: 'business',
          displayName: 'Late Paint Guard Revised',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 8,
          updatedAt: '2026-08-11T06:35:00Z',
        },
      });
      await refreshDetail.promise;
    });

    expect(screen.queryByText('Late Pagination Paint')).not.toBeInTheDocument();
    expect(screen.queryByText('Late Detail Paint')).not.toBeInTheDocument();
    expect(screen.getByText('Late Paint Guard Revised')).toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('confirmed save refresh failure never becomes unknown and never retries the command', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const refreshDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const pendingRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    searchEmployersMock.mockResolvedValueOnce({
      ok: true,
      value: {
        items: [
          {
            employerId: '95959595-9595-4595-8595-959595959595',
            employerType: 'business',
            displayName: 'Refresh Failure Guard Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '95959595-9595-4595-8595-959595959595',
          employerType: 'business',
          displayName: 'Refresh Failure Guard Draft',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 7,
          updatedAt: '2026-08-11T06:40:00Z',
        },
      })
      .mockReturnValueOnce(refreshDetail.promise);
    reviseEmployerMock.mockReturnValueOnce(pendingRevision.promise);

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('82828282-8282-4282-8282-828282828282');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Refresh');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Refresh Failure Guard Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Refresh Failure Guard Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    await act(async () => {
      pendingRevision.resolve({
        ok: true,
        value: {
          detail: {
            employerId: '95959595-9595-4595-8595-959595959595',
            employerType: 'business',
            displayName: 'Refresh Failure Guard Revised',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T06:45:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });
      await pendingRevision.promise;
    });

    expect(reviseEmployerMock).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');

    await act(async () => {
      refreshDetail.resolve({ ok: false, failure: { kind: 'unavailable' } });
      await refreshDetail.promise;
    });

    const failureHeading = await screen.findByRole('heading', { name: 'Current employer detail could not be refreshed' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('Retry reloading the current employer detail before starting another revision attempt.')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Revision outcome is unknown' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry same revision attempt' })).not.toBeInTheDocument();
    expect(reviseEmployerMock).toHaveBeenCalledTimes(1);

    randomUuidSpy.mockRestore();
  });

  it('command and canonical refresh not found clear authority and require a new selected exact detail', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const refreshDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const pendingRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '96969696-9696-4696-8696-969696969696',
              employerType: 'business',
              displayName: 'Refresh Not Found Draft',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      })
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '97979797-9797-4797-8797-979797979797',
              employerType: 'household',
              displayName: 'Replacement Selected Draft',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });
    getEmployerMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '96969696-9696-4696-8696-969696969696',
          employerType: 'business',
          displayName: 'Refresh Not Found Draft',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 7,
          updatedAt: '2026-08-11T06:50:00Z',
        },
      })
      .mockReturnValueOnce(refreshDetail.promise)
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '97979797-9797-4797-8797-979797979797',
          employerType: 'household',
          displayName: 'Replacement Selected Draft',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 3,
          updatedAt: '2026-08-11T06:55:00Z',
        },
      })
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '98989898-9898-4898-8898-989898989898',
          employerType: 'household',
          displayName: 'Conflict Reload Revised',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 9,
          updatedAt: '2026-08-11T07:10:00Z',
        },
      })
      .mockResolvedValue({
        ok: true,
        value: {
          employerId: '98989898-9898-4898-8898-989898989898',
          employerType: 'household',
          displayName: 'Conflict Reload Revised',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 9,
          updatedAt: '2026-08-11T07:10:00Z',
        },
      });
    reviseEmployerMock.mockReturnValueOnce(pendingRevision.promise);

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('83838383-8383-4383-8383-838383838383');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Refresh');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Refresh Not Found Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Refresh Not Found Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    await act(async () => {
      pendingRevision.resolve({
        ok: true,
        value: {
          detail: {
            employerId: '96969696-9696-4696-8696-969696969696',
            employerType: 'business',
            displayName: 'Refresh Not Found Revised',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T06:52:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });
      await pendingRevision.promise;
    });

    await act(async () => {
      refreshDetail.resolve({ ok: false, failure: { kind: 'not_found' } });
      await refreshDetail.promise;
    });

    const notFoundHeading = await screen.findByRole('heading', { name: 'Employer detail is no longer available' });
    expect(notFoundHeading).toHaveFocus();
    expect(screen.getByText('The selected employer detail could not be found for this staff workspace.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Edit draft employer' })).not.toBeInTheDocument();
    expect(screen.queryByRole('form', { name: 'Revise draft employer' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Revision outcome is unknown' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry same revision attempt' })).not.toBeInTheDocument();
    expect(screen.getByLabelText('Draft employer type')).toBeEnabled();
    expect(screen.getByLabelText('Draft employer display name')).toBeEnabled();

    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('button', { name: 'Replacement Selected Draft' });
    expect(screen.queryByRole('button', { name: 'Edit draft employer' })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Replacement Selected Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('revision conflict reloads exact detail before a new edit command can exist', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const conflictRefreshDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();

    searchEmployersMock.mockResolvedValueOnce({
      ok: true,
      value: {
        items: [
          {
            employerId: '98989898-9898-4898-8898-989898989898',
            employerType: 'business',
            displayName: 'Conflict Reload Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '98989898-9898-4898-8898-989898989898',
          employerType: 'business',
          displayName: 'Conflict Reload Draft',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 7,
          updatedAt: '2026-08-11T07:00:00Z',
        },
      })
      .mockReturnValueOnce(conflictRefreshDetail.promise);
    reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } }).mockResolvedValueOnce({
      ok: true,
      value: {
        detail: {
          employerId: '98989898-9898-4898-8898-989898989898',
          employerType: 'household',
          displayName: 'Conflict Reload Revised',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 9,
          updatedAt: '2026-08-11T07:10:00Z',
        },
        resultVersion: 9,
        replayed: false,
      },
    });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('84848484-8484-4484-8484-848484848484')
      .mockReturnValueOnce('85858585-8585-4585-8585-858585858585');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Conflict');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Conflict Reload Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Conflict Reload Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const conflictHeading = await screen.findByRole('heading', { name: 'Revision is blocked until current employer detail reloads' });
    const conflictRegion = conflictHeading.closest('section');
    expect(conflictRegion).not.toBeNull();

    await user.click(within(conflictRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));

    const secondConflictReloadCall = getEmployerMock.mock.calls[1];
    expect(secondConflictReloadCall?.[0]).toBe('98989898-9898-4898-8898-989898989898');
    expect(secondConflictReloadCall?.[1]?.signal).toBeInstanceOf(AbortSignal);
    expect(screen.queryByRole('button', { name: 'Edit draft employer' })).not.toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');

    await act(async () => {
      conflictRefreshDetail.resolve({
        ok: true,
        value: {
          employerId: '98989898-9898-4898-8898-989898989898',
          employerType: 'business',
          displayName: 'Conflict Reload Current',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 8,
          updatedAt: '2026-08-11T07:05:00Z',
        },
      });
      await conflictRefreshDetail.promise;
    });

    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Conflict Reload Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    expect(reviseEmployerMock).toHaveBeenNthCalledWith(2, {
      employerId: '98989898-9898-4898-8898-989898989898',
      commandId: '85858585-8585-4585-8585-858585858585',
      expectedVersion: 8,
      employerType: 'household',
      displayName: 'Conflict Reload Revised',
    });

    randomUuidSpy.mockRestore();
  });

  it('stale revision releases the command key but blocks editing until exact detail refresh', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const staleRefreshDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();

    searchEmployersMock.mockResolvedValueOnce({
      ok: true,
      value: {
        items: [
          {
            employerId: 'a8a8a8a8-a8a8-48a8-88a8-a8a8a8a8a8a8',
            employerType: 'business',
            displayName: 'Stale Reload Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: 'a8a8a8a8-a8a8-48a8-88a8-a8a8a8a8a8a8',
          employerType: 'business',
          displayName: 'Stale Reload Draft',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 7,
          updatedAt: '2026-08-11T07:20:00Z',
        },
      })
      .mockReturnValueOnce(staleRefreshDetail.promise)
      .mockResolvedValue({
        ok: true,
        value: {
          employerId: 'a8a8a8a8-a8a8-48a8-88a8-a8a8a8a8a8a8',
          employerType: 'household',
          displayName: 'Stale Reload Revised',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 9,
          updatedAt: '2026-08-11T07:30:00Z',
        },
      });
    reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'stale' } }).mockResolvedValueOnce({
      ok: true,
      value: {
        detail: {
          employerId: 'a8a8a8a8-a8a8-48a8-88a8-a8a8a8a8a8a8',
          employerType: 'household',
          displayName: 'Stale Reload Revised Again',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 10,
          updatedAt: '2026-08-11T07:35:00Z',
        },
        resultVersion: 10,
        replayed: false,
      },
    });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('86868686-8686-4686-8686-868686868686')
      .mockReturnValueOnce('87878787-8787-4787-8787-878787878787');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Stale');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Stale Reload Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Stale Reload Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const staleHeading = await screen.findByRole('heading', {
      name: 'Revision requires current employer detail before editing can continue',
    });
    const staleRegion = staleHeading.closest('section');
    expect(staleRegion).not.toBeNull();

    await user.click(within(staleRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));

    const secondStaleReloadCall = getEmployerMock.mock.calls[1];
    expect(secondStaleReloadCall?.[0]).toBe('a8a8a8a8-a8a8-48a8-88a8-a8a8a8a8a8a8');
    expect(secondStaleReloadCall?.[1]?.signal).toBeInstanceOf(AbortSignal);
    expect(screen.queryByRole('button', { name: 'Edit draft employer' })).not.toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');

    await act(async () => {
      staleRefreshDetail.resolve({
        ok: true,
        value: {
          employerId: 'a8a8a8a8-a8a8-48a8-88a8-a8a8a8a8a8a8',
          employerType: 'household',
          displayName: 'Stale Reload Revised',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 9,
          updatedAt: '2026-08-11T07:30:00Z',
        },
      });
      await staleRefreshDetail.promise;
    });

    expect(screen.getByRole('button', { name: 'Edit draft employer' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Stale Reload Revised Again');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    expect(reviseEmployerMock).toHaveBeenNthCalledWith(2, {
      employerId: 'a8a8a8a8-a8a8-48a8-88a8-a8a8a8a8a8a8',
      commandId: '87878787-8787-4787-8787-878787878787',
      expectedVersion: 9,
      employerType: 'household',
      displayName: 'Stale Reload Revised Again',
    });

    randomUuidSpy.mockRestore();
  });

  it('revision unknown reload failure preserves the original authority', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    createEmployerMock.mockReset();
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    searchEmployersMock.mockResolvedValueOnce({
      ok: true,
      value: {
        items: [
          {
            employerId: 'b9b9b9b9-b9b9-49b9-89b9-b9b9b9b9b9b9',
            employerType: 'business',
            displayName: 'Unknown Reload Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: 'b9b9b9b9-b9b9-49b9-89b9-b9b9b9b9b9b9',
          employerType: 'business',
          displayName: 'Unknown Reload Draft',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 7,
          updatedAt: '2026-08-11T07:40:00Z',
        },
      })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unavailable' } });
    reviseEmployerMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } })
      .mockResolvedValueOnce({
        ok: true,
        value: {
          detail: {
            employerId: 'b9b9b9b9-b9b9-49b9-89b9-b9b9b9b9b9b9',
            employerType: 'household',
            displayName: 'Unknown Reload Revised',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T07:45:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('89898989-8989-4898-8989-898989898989')
      .mockReturnValueOnce('90909090-9090-4090-8090-909090909090');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Unknown');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Unknown Reload Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });

    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Unknown Reload Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const unknownHeading = await screen.findByRole('heading', { name: 'Revision outcome is unknown' });
    const unknownRegion = unknownHeading.closest('section');
    expect(unknownRegion).not.toBeNull();
    expect(screen.getByLabelText('Draft employer type')).toBeDisabled();
    expect(screen.getByLabelText('Draft employer display name')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Create draft employer' })).toBeDisabled();

    await user.click(within(unknownRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));

    const secondUnknownReloadCall = getEmployerMock.mock.calls[1];
    expect(secondUnknownReloadCall?.[0]).toBe('b9b9b9b9-b9b9-49b9-89b9-b9b9b9b9b9b9');
    expect(secondUnknownReloadCall?.[1]?.signal).toBeInstanceOf(AbortSignal);
    const unknownHeadingAfterReload = await screen.findByRole('heading', { name: 'Revision outcome is unknown' });
    const unknownRegionAfterReload = unknownHeadingAfterReload.closest('section');
    expect(unknownRegionAfterReload).not.toBeNull();
    expect(within(unknownRegionAfterReload as HTMLElement).getByRole('button', { name: 'Retry same revision attempt' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Edit draft employer' })).not.toBeInTheDocument();

    await user.click(within(unknownRegionAfterReload as HTMLElement).getByRole('button', { name: 'Retry same revision attempt' }));

    expect(reviseEmployerMock).toHaveBeenNthCalledWith(2, {
      employerId: 'b9b9b9b9-b9b9-49b9-89b9-b9b9b9b9b9b9',
      commandId: '89898989-8989-4898-8989-898989898989',
      expectedVersion: 7,
      employerType: 'household',
      displayName: 'Unknown Reload Revised',
    });

    randomUuidSpy.mockRestore();
  });

  it('pagehide invalidates revision search and detail late completions', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const deferredPagination = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const deferredCanonicalReload = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const paginationSignals: Array<AbortSignal | undefined> = [];
    const detailSignals: Array<AbortSignal | undefined> = [];

    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: 'c1c1c1c1-c1c1-41c1-81c1-c1c1c1c1c1c1',
              employerType: 'business',
              displayName: 'Pagehide Revision Draft',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: 'next-page',
        },
      })
      .mockImplementationOnce((_input) => {
        paginationSignals.push(_input.signal);
        return deferredPagination.promise;
      });
    getEmployerMock
      .mockImplementationOnce((_employerId, options) => {
        detailSignals.push(options?.signal);
        return Promise.resolve({
          ok: true,
          value: {
            employerId: 'c1c1c1c1-c1c1-41c1-81c1-c1c1c1c1c1c1',
            employerType: 'business',
            displayName: 'Pagehide Revision Draft',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 7,
            updatedAt: '2026-08-11T08:00:00Z',
          },
        });
      })
      .mockImplementationOnce((_employerId, options) => {
        detailSignals.push(options?.signal);
        return deferredCanonicalReload.promise;
      });
    reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('91919191-9191-4919-8919-919191919191');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Pagehide');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });

    await user.click(screen.getByRole('button', { name: 'Load more employers' }));
    expect(searchEmployersMock).toHaveBeenNthCalledWith(2, {
      cursor: 'next-page',
      displayNameQuery: 'Pagehide',
      employerType: undefined,
      signal: paginationSignals[0],
    });

    await user.click(screen.getByRole('button', { name: 'Pagehide Revision Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Pagehide Revision Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    const conflictHeading = await screen.findByRole('heading', {
      name: 'Revision is blocked until current employer detail reloads',
    });
    const conflictRegion = conflictHeading.closest('section');
    expect(conflictRegion).not.toBeNull();

    await user.click(within(conflictRegion as HTMLElement).getByRole('button', { name: 'Reload current employer detail' }));
    expect(getEmployerMock).toHaveBeenNthCalledWith(2, 'c1c1c1c1-c1c1-41c1-81c1-c1c1c1c1c1c1', {
      signal: detailSignals[1],
    });

    act(() => {
      window.dispatchEvent(new Event('pagehide'));
    });

    expect(paginationSignals[0]?.aborted).toBe(true);
    expect(detailSignals[1]?.aborted).toBe(true);
    expect(screen.queryByRole('heading', { name: 'Search results' })).not.toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'Employer detail' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Revision is blocked until current employer detail reloads' })).not.toBeInTheDocument();

    await act(async () => {
      deferredPagination.resolve({
        ok: true,
        value: {
          items: [
            {
              employerId: 'd2d2d2d2-d2d2-42d2-82d2-d2d2d2d2d2d2',
              employerType: 'household',
              displayName: 'Late Pagehide Pagination Result',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });
      deferredCanonicalReload.resolve({
        ok: true,
        value: {
          employerId: 'c1c1c1c1-c1c1-41c1-81c1-c1c1c1c1c1c1',
          employerType: 'household',
          displayName: 'Late Pagehide Reloaded Detail',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 8,
          updatedAt: '2026-08-11T08:05:00Z',
        },
      });
      await deferredPagination.promise;
      await deferredCanonicalReload.promise;
    });

    expect(screen.queryByText('Late Pagehide Pagination Result')).not.toBeInTheDocument();
    expect(screen.queryByText('Late Pagehide Reloaded Detail')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Edit draft employer' })).not.toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('pagehide generation invalidation wins over an already queued mutation completion microtask', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const pendingRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    searchEmployersMock.mockResolvedValueOnce({
      ok: true,
      value: {
        items: [
          {
            employerId: 'e3e3e3e3-e3e3-43e3-83e3-e3e3e3e3e3e3',
            employerType: 'business',
            displayName: 'Queued Pagehide Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock.mockResolvedValueOnce({
      ok: true,
      value: {
        employerId: 'e3e3e3e3-e3e3-43e3-83e3-e3e3e3e3e3e3',
        employerType: 'business',
        displayName: 'Queued Pagehide Draft',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 7,
        updatedAt: '2026-08-11T08:20:00Z',
      },
    });
    reviseEmployerMock.mockReturnValueOnce(pendingRevision.promise);

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('a1a1a1a1-a1a1-41a1-81a1-a1a1a1a1a1a1');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Queued');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });
    await user.click(screen.getByRole('button', { name: 'Queued Pagehide Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Queued Pagehide Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    expect(reviseEmployerMock).toHaveBeenCalledTimes(1);

    pendingRevision.resolve({
      ok: true,
      value: {
        detail: {
          employerId: 'e3e3e3e3-e3e3-43e3-83e3-e3e3e3e3e3e3',
          employerType: 'household',
          displayName: 'Queued Pagehide Revised',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 8,
          updatedAt: '2026-08-11T08:25:00Z',
        },
        resultVersion: 8,
        replayed: false,
      },
    });

    act(() => {
      window.dispatchEvent(new Event('pagehide'));
    });

    await act(async () => {
      await pendingRevision.promise;
    });

    expect(getEmployerMock).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('heading', { name: 'Draft employer revision saved' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Revision outcome is unknown' })).not.toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'Employer detail' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Edit draft employer' })).not.toBeInTheDocument();
    expect(screen.queryByDisplayValue('Queued Pagehide Revised')).not.toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('revision success heading retains final focus after refreshed detail renders', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    const refreshDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const pendingRevision = createDeferredPromise<Awaited<ReturnType<typeof reviseEmployer>>>();

    searchEmployersMock.mockResolvedValueOnce({
      ok: true,
      value: {
        items: [
          {
            employerId: 'f4f4f4f4-f4f4-44f4-84f4-f4f4f4f4f4f4',
            employerType: 'business',
            displayName: 'Focus Owner Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: 'f4f4f4f4-f4f4-44f4-84f4-f4f4f4f4f4f4',
          employerType: 'business',
          displayName: 'Focus Owner Draft',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 7,
          updatedAt: '2026-08-11T08:30:00Z',
        },
      })
      .mockReturnValueOnce(refreshDetail.promise);
    reviseEmployerMock.mockReturnValueOnce(pendingRevision.promise);

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('b2b2b2b2-b2b2-42b2-82b2-b2b2b2b2b2b2');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Focus');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await user.click(screen.getByRole('button', { name: 'Focus Owner Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'Focus Owner Draft Revised');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    await act(async () => {
      pendingRevision.resolve({
        ok: true,
        value: {
          detail: {
            employerId: 'f4f4f4f4-f4f4-44f4-84f4-f4f4f4f4f4f4',
            employerType: 'business',
            displayName: 'Focus Owner Draft Revised',
            lifecycleStatus: 'draft',
            sourceChannel: 'staff_entry',
            version: 8,
            updatedAt: '2026-08-11T08:35:00Z',
          },
          resultVersion: 8,
          replayed: false,
        },
      });
      await pendingRevision.promise;
    });

    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');

    await act(async () => {
      refreshDetail.resolve({
        ok: true,
        value: {
          employerId: 'f4f4f4f4-f4f4-44f4-84f4-f4f4f4f4f4f4',
          employerType: 'business',
          displayName: 'Focus Owner Draft Revised',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 8,
          updatedAt: '2026-08-11T08:35:00Z',
        },
      });
      await refreshDetail.promise;
    });

    const successHeading = await screen.findByRole('heading', { name: 'Draft employer revision saved' });
    expect(successHeading).toHaveFocus();
    expect(screen.getByText('The current draft employer detail now reflects the saved revision.')).toBeInTheDocument();

    const detailRegion = screen.getByRole('region', { name: 'Employer detail' });
    expect(within(detailRegion).getByText('Focus Owner Draft Revised')).toBeInTheDocument();
    expect(within(detailRegion).getByRole('heading', { name: 'Employer detail' })).not.toHaveFocus();

    randomUuidSpy.mockRestore();
  });

  it('persisted pageshow still uses canonical document reload', () => {
    const canonicalReloadSpy = vi.fn();

    render(
      <LanguageProvider>
        <EmployerWorkspace onPersistedRestore={canonicalReloadSpy} />
      </LanguageProvider>,
    );

    const nonPersistedPageShowEvent = new Event('pageshow');
    Object.defineProperty(nonPersistedPageShowEvent, 'persisted', { configurable: true, value: false });

    const persistedPageShowEvent = new Event('pageshow');
    Object.defineProperty(persistedPageShowEvent, 'persisted', { configurable: true, value: true });

    act(() => {
      window.dispatchEvent(new Event('pagehide'));
      window.dispatchEvent(nonPersistedPageShowEvent);
      window.dispatchEvent(persistedPageShowEvent);
    });

    expect(canonicalReloadSpy).toHaveBeenCalledTimes(1);
    expect(screen.getByRole('region', { name: 'Employers workspace' })).toBeInTheDocument();
    expect(screen.getByRole('form', { name: 'Create a draft employer' })).toBeInTheDocument();
    expect(screen.getByRole('form', { name: 'Employer search' })).toBeInTheDocument();
  });

  it('invalidates pending detail on selection filter search and unmount', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();

    const firstDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const secondDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const thirdDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const fourthDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const detailSignals: Array<AbortSignal | undefined> = [];

    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '10101010-1010-4010-8010-101010101010',
              employerType: 'business',
              displayName: 'First Detail Target',
              lifecycleStatus: 'draft',
            },
            {
              employerId: '20202020-2020-4020-8020-202020202020',
              employerType: 'household',
              displayName: 'Second Detail Target',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      })
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '30303030-3030-4030-8030-303030303030',
              employerType: 'business',
              displayName: 'Third Detail Target',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      })
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '40404040-4040-4040-8040-404040404040',
              employerType: 'business',
              displayName: 'Fourth Detail Target',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });

    getEmployerMock
      .mockImplementationOnce(async (_employerId, options) => {
        detailSignals.push(options?.signal);
        return firstDetail.promise;
      })
      .mockImplementationOnce(async (_employerId, options) => {
        detailSignals.push(options?.signal);
        return secondDetail.promise;
      })
      .mockImplementationOnce(async (_employerId, options) => {
        detailSignals.push(options?.signal);
        return thirdDetail.promise;
      })
      .mockImplementationOnce(async (_employerId, options) => {
        detailSignals.push(options?.signal);
        return fourthDetail.promise;
      });

    const { unmount } = render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const nameInput = screen.getByLabelText('Employer name');
    const submitButton = screen.getByRole('button', { name: 'Search employers' });

    await user.type(nameInput, 'Rose');
    await user.click(submitButton);

    await user.click(screen.getByRole('button', { name: 'First Detail Target' }));
    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');

    await user.click(screen.getByRole('button', { name: 'Second Detail Target' }));
    expect(getEmployerMock).toHaveBeenNthCalledWith(1, '10101010-1010-4010-8010-101010101010', {
      signal: detailSignals[0],
    });
    expect(getEmployerMock).toHaveBeenNthCalledWith(2, '20202020-2020-4020-8020-202020202020', {
      signal: detailSignals[1],
    });
    expect(detailSignals[0]?.aborted).toBe(true);

    await act(async () => {
      firstDetail.resolve({
        ok: true,
        value: {
          employerId: '10101010-1010-4010-8010-101010101010',
          employerType: 'business',
          displayName: 'Late First Detail',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 1,
          updatedAt: '2026-08-11T04:30:00Z',
        },
      });
      await firstDetail.promise;
    });

    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');
    expect(screen.queryByText('Late First Detail')).not.toBeInTheDocument();

    await user.clear(nameInput);
    await user.type(nameInput, 'Rose Staffing');
    expect(detailSignals[1]?.aborted).toBe(true);
    expect(screen.queryByRole('status', { name: 'Loading employer detail.' })).not.toBeInTheDocument();

    await act(async () => {
      secondDetail.resolve({
        ok: true,
        value: {
          employerId: '20202020-2020-4020-8020-202020202020',
          employerType: 'household',
          displayName: 'Late Second Detail',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 1,
          updatedAt: '2026-08-11T04:31:00Z',
        },
      });
      await secondDetail.promise;
    });

    expect(screen.queryByText('Late Second Detail')).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Employer detail' })).not.toBeInTheDocument();

    await user.click(submitButton);
    await user.click(screen.getByRole('button', { name: 'Third Detail Target' }));
    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');

    await user.click(submitButton);
    await screen.findByRole('button', { name: 'Fourth Detail Target' });
    expect(detailSignals[2]?.aborted).toBe(true);

    await act(async () => {
      thirdDetail.resolve({
        ok: true,
        value: {
          employerId: '30303030-3030-4030-8030-303030303030',
          employerType: 'business',
          displayName: 'Late Third Detail',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 1,
          updatedAt: '2026-08-11T04:32:00Z',
        },
      });
      await thirdDetail.promise;
    });

    expect(screen.queryByText('Late Third Detail')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Fourth Detail Target' }));
    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');

    unmount();
    expect(detailSignals[3]?.aborted).toBe(true);

    await act(async () => {
      fourthDetail.resolve({
        ok: true,
        value: {
          employerId: '40404040-4040-4040-8040-404040404040',
          employerType: 'business',
          displayName: 'Late Fourth Detail',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 1,
          updatedAt: '2026-08-11T04:33:00Z',
        },
      });
      await fourthDetail.promise;
    });
  });

  it('maps detail failures without existence or data leakage', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();

    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '50505050-5050-4050-8050-505050505050',
            employerType: 'business',
            displayName: 'Failure Mapping Anchor',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });

    getEmployerMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '50505050-5050-4050-8050-505050505050',
          employerType: 'business',
          displayName: 'Previously Visible Detail',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 1,
          updatedAt: '2026-08-11T04:34:00Z',
        },
      })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'validation' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'not_found' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'forbidden' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unavailable' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unexpected' } });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Rose');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    const selectButton = await screen.findByRole('button', { name: 'Failure Mapping Anchor' });

    await user.click(selectButton);
    await screen.findByRole('heading', { name: 'Employer detail' });
    expect(screen.getByText('Previously Visible Detail')).toBeInTheDocument();

    await user.click(selectButton);

    let failureHeading = await screen.findByRole('heading', { name: 'Employer detail could not be displayed' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('Select the employer again from the current search results.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Failure Mapping Anchor' })).toBeInTheDocument();
    expect(screen.queryByText('Previously Visible Detail')).not.toBeInTheDocument();

    await user.click(selectButton);

    failureHeading = await screen.findByRole('heading', { name: 'Employer detail is no longer available' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('The selected employer detail could not be found for this staff workspace.')).toBeInTheDocument();
    expect(screen.queryByText('Previously Visible Detail')).not.toBeInTheDocument();
    expect(screen.queryByText('50505050-5050-4050-8050-505050505050')).not.toBeInTheDocument();

    await user.click(selectButton);

    failureHeading = await screen.findByRole('heading', { name: 'Employer detail is not available for this staff session' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('This staff session is not allowed to view the selected employer detail.')).toBeInTheDocument();

    await user.click(selectButton);

    failureHeading = await screen.findByRole('heading', { name: 'Employer detail requires a fresh search' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('Run the employer search again before reopening employer detail.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Failure Mapping Anchor' })).toBeInTheDocument();

    await user.click(selectButton);

    failureHeading = await screen.findByRole('heading', { name: 'Employer detail is temporarily unavailable' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('Retry selecting the employer detail when the service becomes available.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Failure Mapping Anchor' })).toBeInTheDocument();

    await user.click(selectButton);

    failureHeading = await screen.findByRole('heading', { name: 'Employer detail response could not be used' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('Select the employer again or run the search again before reopening employer detail.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Failure Mapping Anchor' })).toBeInTheDocument();
    expect(screen.queryByText('404 hidden existence')).not.toBeInTheDocument();
    expect(screen.queryByText('403 session denied')).not.toBeInTheDocument();
    expect(screen.queryByText('503 database offline')).not.toBeInTheDocument();
  });

  it('omits unapproved detail data and side effects', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();

    searchEmployersMock.mockResolvedValue({
      ok: true,
      value: {
        items: [
          {
            employerId: '60606060-6060-4060-8060-606060606060',
            employerType: 'business',
            displayName: 'Privacy Detail Anchor',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock.mockResolvedValue({
      ok: true,
      value: {
        employerId: '60606060-6060-4060-8060-606060606060',
        employerType: 'business',
        displayName: 'Privacy Detail Rendering',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 1,
        updatedAt: '2026-08-11T04:05:00Z',
      },
    });

    const replaceStateSpy = vi.spyOn(window.history, 'replaceState');
    const pushStateSpy = vi.spyOn(window.history, 'pushState');
    const localStorageSetItem = vi.spyOn(Storage.prototype, 'setItem');
    const localStorageGetItem = vi.spyOn(Storage.prototype, 'getItem');

    window.history.replaceState({}, '', '/employers');

    render(
      <LanguageProvider>
        <App />
      </LanguageProvider>,
    );

    replaceStateSpy.mockClear();
    pushStateSpy.mockClear();

    await user.type(screen.getByLabelText('Employer name'), 'Rose');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await user.click(screen.getByRole('button', { name: 'Privacy Detail Anchor' }));

    const detailRegion = await screen.findByRole('region', { name: 'Employer detail' });

    expect(within(detailRegion).queryByRole('button', { name: /edit/i })).not.toBeInTheDocument();
    expect(within(detailRegion).queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
    expect(within(detailRegion).queryByRole('button', { name: /export/i })).not.toBeInTheDocument();
    expect(within(detailRegion).queryByRole('button', { name: /audit/i })).not.toBeInTheDocument();
    expect(within(detailRegion).queryByText(/contact/i)).not.toBeInTheDocument();
    expect(within(detailRegion).queryByText(/worksite/i)).not.toBeInTheDocument();
    expect(within(detailRegion).queryByText(/request/i)).not.toBeInTheDocument();
    expect(within(detailRegion).queryByText('60606060-6060-4060-8060-606060606060')).not.toBeInTheDocument();
    expect(within(detailRegion).queryByText(/creator/i)).not.toBeInTheDocument();
    expect(within(detailRegion).queryByText(/cursor/i)).not.toBeInTheDocument();
    expect(within(detailRegion).queryByText(/command/i)).not.toBeInTheDocument();
    expect(within(detailRegion).queryByText(/event/i)).not.toBeInTheDocument();
    expect(within(detailRegion).queryByText('{')).not.toBeInTheDocument();
    expect(within(detailRegion).queryByText('"display_name"')).not.toBeInTheDocument();

    expect(window.location.pathname).toBe('/employers');
    expect(window.location.search).toBe('');
    expect(window.location.hash).toBe('');
    expect(replaceStateSpy).not.toHaveBeenCalled();
    expect(pushStateSpy).not.toHaveBeenCalled();
    expect(localStorageSetItem).not.toHaveBeenCalled();
    expect(localStorageGetItem).not.toHaveBeenCalled();
  });

  it('renders only the bounded fictional create form', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    createEmployerMock.mockReset();

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    expect(screen.getByRole('heading', { name: 'Create a draft employer' })).toBeInTheDocument();
    expect(screen.getByText('Create a draft only after search confirms this employer is not already listed.')).toBeInTheDocument();
    expect(screen.getByText('Search first before creating a new draft employer.')).toBeInTheDocument();
    expect(screen.getByLabelText('Draft employer type')).toBeInTheDocument();
    expect(screen.getByLabelText('Draft employer display name')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create draft employer' })).toBeInTheDocument();

    expect(screen.queryByLabelText('Employer contact')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Worksite')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Phone number')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Email address')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));
    expect(createEmployerMock).not.toHaveBeenCalled();
  });

  it('enforces the inclusive 200-code-point create boundary before fetch', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    createEmployerMock.mockReset();
    createEmployerMock.mockResolvedValue({ ok: false, failure: { kind: 'unexpected' } });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const typeSelect = screen.getByLabelText('Draft employer type');
    const nameInput = screen.getByLabelText('Draft employer display name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'business');
    fireEvent.change(nameInput, { target: { value: 'Á'.repeat(200) } });
    await user.click(submitButton);

    expect(createEmployerMock).toHaveBeenCalledTimes(1);
    expect(createEmployerMock).toHaveBeenCalledWith(
      expect.objectContaining({
        employerType: 'business',
        displayName: 'Á'.repeat(200),
      }),
    );

    await user.clear(nameInput);
    fireEvent.change(nameInput, { target: { value: 'A'.repeat(201) } });
    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent('Enter 1 to 200 visible characters for the employer name.');
    expect(nameInput).toHaveFocus();
    expect(createEmployerMock).toHaveBeenCalledTimes(1);

    await user.clear(nameInput);
    await user.type(nameInput, '   ');
    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent('Enter 1 to 200 visible characters for the employer name.');
    expect(nameInput).toHaveFocus();
    expect(createEmployerMock).toHaveBeenCalledTimes(1);

    fireEvent.change(nameInput, { target: { value: 'Rose\u0007' } });
    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent('Enter 1 to 200 visible characters for the employer name.');
    expect(nameInput).toHaveFocus();
    expect(createEmployerMock).toHaveBeenCalledTimes(1);

    await user.clear(nameInput);
    await user.type(nameInput, 'Valid Rose');
    fireEvent.change(typeSelect, { target: { value: 'unsupported' } });
    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent('Select either Business or Household before creating a draft employer.');
    expect(typeSelect).toHaveFocus();
    expect(createEmployerMock).toHaveBeenCalledTimes(1);

    fireEvent.change(typeSelect, { target: { value: '' } });
    await user.click(submitButton);
    expect(screen.getByRole('alert')).toHaveTextContent('Select either Business or Household before creating a draft employer.');
    expect(typeSelect).toHaveFocus();
    expect(createEmployerMock).toHaveBeenCalledTimes(1);
  });

  it('freezes one immutable create attempt while pending', async () => {
    const user = userEvent.setup();
    const pendingCreate = createDeferredPromise<Awaited<ReturnType<typeof createEmployer>>>();
    const createEmployerMock = vi.mocked(createEmployer);
    createEmployerMock.mockReset();
    createEmployerMock.mockReturnValue(pendingCreate.promise);

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('77777777-7777-4777-8777-777777777777');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const typeSelect = screen.getByLabelText('Draft employer type');
    const nameInput = screen.getByLabelText('Draft employer display name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'business');
    fireEvent.change(nameInput, { target: { value: 'Immutable Pending Rose' } });
    await user.click(submitButton);

    expect(createEmployerMock).toHaveBeenCalledTimes(1);
    expect(createEmployerMock).toHaveBeenCalledWith({
      commandId: '77777777-7777-4777-8777-777777777777',
      employerType: 'business',
      displayName: 'Immutable Pending Rose',
    });
    expect(typeSelect).toBeDisabled();
    expect(nameInput).toBeDisabled();
    expect(submitButton).toBeDisabled();

    await user.click(submitButton);
    expect(createEmployerMock).toHaveBeenCalledTimes(1);
    expect(createEmployerMock).toHaveBeenLastCalledWith({
      commandId: '77777777-7777-4777-8777-777777777777',
      employerType: 'business',
      displayName: 'Immutable Pending Rose',
    });

    await act(async () => {
      pendingCreate.resolve({ ok: false, failure: { kind: 'unexpected' } });
      await pendingCreate.promise;
    });

    randomUuidSpy.mockRestore();
  });

  it('accepts only valid 201 create success', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    const getEmployerMock = vi.mocked(getEmployer);
    createEmployerMock.mockReset();
    getEmployerMock.mockReset();
    createEmployerMock.mockResolvedValue({
      ok: true,
      value: {
        employerId: '99999999-9999-4999-8999-999999999999',
        employerType: 'household',
        displayName: '<script>alert("rose")</script>',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
      },
    });

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const typeSelect = screen.getByLabelText('Draft employer type');
    const nameInput = screen.getByLabelText('Draft employer display name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'household');
    await user.type(nameInput, '<script>alert("rose")</script>');
    await user.click(submitButton);

    const successHeading = await screen.findByRole('heading', { name: 'Draft employer created' });
    expect(successHeading).toHaveFocus();
    expect(getEmployerMock).not.toHaveBeenCalled();
    expect(typeSelect).toHaveValue('');
    expect(nameInput).toHaveValue('');
    expect(typeSelect).not.toBeDisabled();
    expect(nameInput).not.toBeDisabled();
    expect(submitButton).not.toBeDisabled();

    const successRegion = successHeading.closest('section');
    expect(successRegion).not.toBeNull();
    expect(within(successRegion as HTMLElement).getByText('<script>alert("rose")</script>')).toBeInTheDocument();
    expect(within(successRegion as HTMLElement).getByText('Household')).toBeInTheDocument();
    expect(within(successRegion as HTMLElement).getByText('Draft')).toBeInTheDocument();
    expect(within(successRegion as HTMLElement).getByText('Staff entry')).toBeInTheDocument();
    expect(within(successRegion as HTMLElement).queryByText('99999999-9999-4999-8999-999999999999')).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Employer detail is loading' })).not.toBeInTheDocument();
  });

  it('retries an unknown create outcome with the identical attempt', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    createEmployerMock.mockReset();
    createEmployerMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } });

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const typeSelect = screen.getByLabelText('Draft employer type');
    const nameInput = screen.getByLabelText('Draft employer display name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'business');
    fireEvent.change(nameInput, { target: { value: 'Unknown Outcome Rose' } });
    await user.click(submitButton);

    const warningHeading = await screen.findByRole('heading', { name: 'Create outcome is unknown' });
    const warningRegion = warningHeading.closest('section');
    expect(warningRegion).not.toBeNull();
    expect(within(warningRegion as HTMLElement).getByText('Retry the same create attempt because it may already have succeeded.')).toBeInTheDocument();
    expect(within(warningRegion as HTMLElement).getByRole('button', { name: 'Retry same create attempt' })).toBeInTheDocument();
    expect(within(warningRegion as HTMLElement).queryByText('Unknown Outcome Rose')).not.toBeInTheDocument();
    expect(typeSelect).toBeDisabled();
    expect(nameInput).toBeDisabled();
    expect(submitButton).toBeDisabled();
    expect(createEmployerMock).toHaveBeenCalledTimes(1);
    expect(createEmployerMock).toHaveBeenNthCalledWith(1, {
      commandId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
      employerType: 'business',
      displayName: 'Unknown Outcome Rose',
    });

    const beforeUnloadEvent = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(beforeUnloadEvent);
    expect(beforeUnloadEvent.defaultPrevented).toBe(true);

    await user.click(within(warningRegion as HTMLElement).getByRole('button', { name: 'Retry same create attempt' }));
    expect(createEmployerMock).toHaveBeenCalledTimes(2);
    expect(createEmployerMock).toHaveBeenNthCalledWith(2, {
      commandId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
      employerType: 'business',
      displayName: 'Unknown Outcome Rose',
    });

    randomUuidSpy.mockRestore();
  });

  it('serializes unknown create retry authority', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    const searchEmployersMock = vi.mocked(searchEmployers);
    createEmployerMock.mockReset();
    searchEmployersMock.mockReset();

    const deferredRetry = createDeferredPromise<Awaited<ReturnType<typeof createEmployer>>>();
    const deferredAbandonmentSearch = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();

    createEmployerMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } })
      .mockReturnValueOnce(deferredRetry.promise);
    searchEmployersMock.mockReturnValueOnce(deferredAbandonmentSearch.promise);

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('acacacac-acac-4cac-8cac-acacacacacac');
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Serialized Unknown Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));

    const warningHeading = await screen.findByRole('heading', { name: 'Create outcome is unknown' });
    const warningRegion = warningHeading.closest('section');
    expect(warningRegion).not.toBeNull();

    const retryButton = within(warningRegion as HTMLElement).getByRole('button', {
      name: 'Retry same create attempt',
    });
    const abandonButton = within(warningRegion as HTMLElement).getByRole('button', {
      name: 'Abandon unknown create and search',
    });

    fireEvent.click(retryButton);
    fireEvent.click(retryButton);

    expect(createEmployerMock).toHaveBeenCalledTimes(2);
    expect(createEmployerMock).toHaveBeenNthCalledWith(2, {
      commandId: 'acacacac-acac-4cac-8cac-acacacacacac',
      employerType: 'business',
      displayName: 'Serialized Unknown Rose',
    });
    expect(retryButton).toBeDisabled();
    expect(abandonButton).toBeDisabled();

    await user.click(abandonButton);
    expect(confirmSpy).not.toHaveBeenCalled();
    expect(searchEmployersMock).not.toHaveBeenCalled();

    await act(async () => {
      deferredRetry.resolve({
        ok: true,
        value: {
          employerId: 'adadadad-adad-4dad-8dad-adadadadadad',
          employerType: 'business',
          displayName: 'Serialized Unknown Rose',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
        },
      });
      await deferredRetry.promise;
    });

    expect(await screen.findByRole('heading', { name: 'Draft employer created' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Create outcome is unknown' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry same create attempt' })).not.toBeInTheDocument();

    fireEvent.click(abandonButton);
    expect(searchEmployersMock).not.toHaveBeenCalled();

    randomUuidSpy.mockRestore();
    confirmSpy.mockRestore();
  });

  it('warns before unload while a create request is still pending', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    createEmployerMock.mockReset();

    const deferredCreate = createDeferredPromise<Awaited<ReturnType<typeof createEmployer>>>();
    createEmployerMock.mockReturnValue(deferredCreate.promise);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Pending Create Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));

    const beforeUnloadEvent = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(beforeUnloadEvent);
    expect(beforeUnloadEvent.defaultPrevented).toBe(true);

    await act(async () => {
      deferredCreate.resolve({ ok: false, failure: { kind: 'unknown_outcome' } });
      await deferredCreate.promise;
    });
  });

  it('does not restore abandonment search recovery state after pagehide', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    const searchEmployersMock = vi.mocked(searchEmployers);
    const deferredSearch = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    createEmployerMock.mockReset();
    searchEmployersMock.mockReset();
    createEmployerMock.mockResolvedValue({ ok: false, failure: { kind: 'unknown_outcome' } });
    searchEmployersMock.mockReturnValueOnce(deferredSearch.promise);

    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Late Abandonment Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));

    const warningHeading = await screen.findByRole('heading', { name: 'Create outcome is unknown' });
    const warningRegion = warningHeading.closest('section');
    expect(warningRegion).not.toBeNull();

    await user.click(within(warningRegion as HTMLElement).getByRole('button', { name: 'Abandon unknown create and search' }));
    expect(searchEmployersMock).toHaveBeenCalledTimes(1);

    act(() => {
      window.dispatchEvent(new Event('pagehide'));
    });

    await act(async () => {
      deferredSearch.resolve({ ok: false, failure: { kind: 'unavailable' } });
      await deferredSearch.promise;
    });

    expect(screen.queryByRole('heading', { name: 'Create outcome is unknown' })).not.toBeInTheDocument();
    expect(
      screen.queryByText(
        'The required follow-up search could not complete. Retry the search before starting a changed create attempt.',
      ),
    ).not.toBeInTheDocument();
    expect(screen.getByLabelText('Draft employer display name')).toHaveValue('');

    confirmSpy.mockRestore();
  });

  it('keeps unknown create authority frozen when the required abandonment search fails', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    const searchEmployersMock = vi.mocked(searchEmployers);
    createEmployerMock.mockReset();
    searchEmployersMock.mockReset();
    createEmployerMock.mockResolvedValue({ ok: false, failure: { kind: 'unknown_outcome' } });
    searchEmployersMock.mockResolvedValue({ ok: false, failure: { kind: 'unavailable' } });

    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const typeSelect = screen.getByLabelText('Draft employer type');
    const nameInput = screen.getByLabelText('Draft employer display name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'business');
    await user.type(nameInput, 'Prior Unknown Rose');
    await user.click(submitButton);

    const warningHeading = await screen.findByRole('heading', { name: 'Create outcome is unknown' });
    const warningRegion = warningHeading.closest('section');
    expect(warningRegion).not.toBeNull();

    await user.click(within(warningRegion as HTMLElement).getByRole('button', { name: 'Abandon unknown create and search' }));

    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(searchEmployersMock).toHaveBeenCalledWith({
      displayNameQuery: 'Prior Unknown Rose',
      employerType: undefined,
      cursor: null,
    });
    expect(typeSelect).toBeDisabled();
    expect(nameInput).toBeDisabled();
    expect(submitButton).toBeDisabled();
    expect(screen.getByRole('alert')).toHaveTextContent(
      'The required follow-up search could not complete. Retry the search before starting a changed create attempt.',
    );

    const beforeUnloadEvent = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(beforeUnloadEvent);
    expect(beforeUnloadEvent.defaultPrevented).toBe(true);

    confirmSpy.mockRestore();
  });

  it('requires abandonment and search before changed resubmission', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    const searchEmployersMock = vi.mocked(searchEmployers);
    createEmployerMock.mockReset();
    searchEmployersMock.mockReset();
    createEmployerMock.mockResolvedValue({ ok: false, failure: { kind: 'unknown_outcome' } });
    searchEmployersMock.mockResolvedValue({ ok: true, value: { items: [], nextCursor: null } });

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb');
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const typeSelect = screen.getByLabelText('Draft employer type');
    const nameInput = screen.getByLabelText('Draft employer display name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'business');
    await user.type(nameInput, 'Prior Unknown Rose');
    await user.click(submitButton);

    const warningHeading = await screen.findByRole('heading', { name: 'Create outcome is unknown' });
    const warningRegion = warningHeading.closest('section');
    expect(warningRegion).not.toBeNull();
    expect(within(warningRegion as HTMLElement).getByText('The prior create may already have succeeded. Search for it before starting a changed create attempt.')).toBeInTheDocument();
    const abandonButton = within(warningRegion as HTMLElement).getByRole('button', { name: 'Abandon unknown create and search' });

    expect(typeSelect).toBeDisabled();
    expect(nameInput).toBeDisabled();
    expect(submitButton).toBeDisabled();

    await user.click(abandonButton);

    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(searchEmployersMock).toHaveBeenCalledWith({
      displayNameQuery: 'Prior Unknown Rose',
      employerType: undefined,
      cursor: null,
    });
    expect(typeSelect).not.toBeDisabled();
    expect(nameInput).not.toBeDisabled();
    expect(submitButton).not.toBeDisabled();

    const beforeUnloadEvent = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(beforeUnloadEvent);
    expect(beforeUnloadEvent.defaultPrevented).toBe(false);

    randomUuidSpy.mockRestore();
    confirmSpy.mockRestore();
  });

  it('disposes create identity by operation-specific status', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    const searchEmployersMock = vi.mocked(searchEmployers);
    createEmployerMock.mockReset();
    searchEmployersMock.mockReset();
    createEmployerMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'validation' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'conflict' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } });
    searchEmployersMock.mockResolvedValue({ ok: true, value: { items: [], nextCursor: null } });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('11111111-1111-4111-8111-111111111111')
      .mockReturnValueOnce('22222222-2222-4222-8222-222222222222')
      .mockReturnValueOnce('33333333-3333-4333-8333-333333333333');
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const typeSelect = screen.getByLabelText('Draft employer type');
    const nameInput = screen.getByLabelText('Draft employer display name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'business');
    await user.type(nameInput, 'Validation Rose');
    await user.click(submitButton);

    expect(createEmployerMock).toHaveBeenNthCalledWith(1, {
      commandId: '11111111-1111-4111-8111-111111111111',
      employerType: 'business',
      displayName: 'Validation Rose',
    });
    expect(typeSelect).not.toBeDisabled();
    expect(nameInput).not.toBeDisabled();
    expect(submitButton).not.toBeDisabled();

    await user.clear(nameInput);
    await user.type(nameInput, 'Conflict Rose');
    await user.click(submitButton);

    expect(createEmployerMock).toHaveBeenNthCalledWith(2, {
      commandId: '22222222-2222-4222-8222-222222222222',
      employerType: 'business',
      displayName: 'Conflict Rose',
    });

    const conflictHeading = await screen.findByRole('heading', { name: 'Create is blocked until you search first' });
    const conflictRegion = conflictHeading.closest('section');
    expect(conflictRegion).not.toBeNull();
    expect(within(conflictRegion as HTMLElement).queryByRole('button', { name: 'Retry same create attempt' })).not.toBeInTheDocument();
    const abandonButton = within(conflictRegion as HTMLElement).getByRole('button', { name: 'Abandon blocked create and search' });
    expect(typeSelect).toBeDisabled();
    expect(nameInput).toBeDisabled();
    expect(submitButton).toBeDisabled();

    await user.click(abandonButton);

    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(searchEmployersMock).toHaveBeenCalledWith({
      displayNameQuery: 'Conflict Rose',
      employerType: undefined,
      cursor: null,
    });

    await user.selectOptions(typeSelect, 'business');
    await user.clear(nameInput);
    await user.type(nameInput, 'Unknown Rose');
    await user.click(submitButton);

    expect(createEmployerMock).toHaveBeenNthCalledWith(3, {
      commandId: '33333333-3333-4333-8333-333333333333',
      employerType: 'business',
      displayName: 'Unknown Rose',
    });

    const unknownHeading = await screen.findByRole('heading', { name: 'Create outcome is unknown' });
    const unknownRegion = unknownHeading.closest('section');
    expect(unknownRegion).not.toBeNull();
    await user.click(within(unknownRegion as HTMLElement).getByRole('button', { name: 'Retry same create attempt' }));
    expect(createEmployerMock).toHaveBeenNthCalledWith(4, {
      commandId: '33333333-3333-4333-8333-333333333333',
      employerType: 'business',
      displayName: 'Unknown Rose',
    });

    randomUuidSpy.mockRestore();
    confirmSpy.mockRestore();
  });

  it('renders bounded create validation guidance and releases the old command identity', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    createEmployerMock.mockReset();
    createEmployerMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'validation' } })
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '51515151-5151-4515-8515-515151515151',
          employerType: 'business',
          displayName: 'Corrected Rose',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
        },
      });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('44444444-4444-4444-8444-444444444444')
      .mockReturnValueOnce('55555555-5555-4555-8555-555555555555');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const typeSelect = screen.getByLabelText('Draft employer type');
    const nameInput = screen.getByLabelText('Draft employer display name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'business');
    await user.type(nameInput, 'Validation Rose');
    await user.click(submitButton);

    const validationHeading = await screen.findByRole('heading', { name: 'Create draft employer could not be completed' });
    expect(validationHeading).toHaveFocus();
    const validationRegion = validationHeading.closest('section');
    expect(validationRegion).not.toBeNull();
    expect(validationRegion).toHaveAttribute('aria-live', 'assertive');
    expect(within(validationRegion as HTMLElement).getByText(
      'Review the employer type or employer name and correct the draft employer before trying again.',
    )).toBeInTheDocument();
    expect(typeSelect).toHaveValue('business');
    expect(nameInput).toHaveValue('Validation Rose');
    expect(typeSelect).not.toBeDisabled();
    expect(nameInput).not.toBeDisabled();
    expect(submitButton).not.toBeDisabled();
    expect(document.body.textContent).not.toContain('44444444-4444-4444-8444-444444444444');
    expect(screen.queryByRole('heading', { name: 'Create outcome is unknown' })).not.toBeInTheDocument();

    await user.clear(nameInput);
    await user.type(nameInput, 'Corrected Rose');
    await user.click(submitButton);

    expect(createEmployerMock).toHaveBeenNthCalledWith(1, {
      commandId: '44444444-4444-4444-8444-444444444444',
      employerType: 'business',
      displayName: 'Validation Rose',
    });
    expect(createEmployerMock).toHaveBeenNthCalledWith(2, {
      commandId: '55555555-5555-4555-8555-555555555555',
      employerType: 'business',
      displayName: 'Corrected Rose',
    });
    expect(await screen.findByRole('heading', { name: 'Draft employer created' })).toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('renders bounded create forbidden guidance and releases the old command identity', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    createEmployerMock.mockReset();
    createEmployerMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'forbidden' } })
      .mockResolvedValueOnce({
        ok: true,
        value: {
          employerId: '62626262-6262-4626-8626-626262626262',
          employerType: 'household',
          displayName: 'Authorized Rose',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
        },
      });

    const randomUuidSpy = vi
      .spyOn(globalThis.crypto, 'randomUUID')
      .mockReturnValueOnce('66666666-6666-4666-8666-666666666666')
      .mockReturnValueOnce('77777777-7777-4777-8777-777777777777');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const typeSelect = screen.getByLabelText('Draft employer type');
    const nameInput = screen.getByLabelText('Draft employer display name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'household');
    await user.type(nameInput, 'Forbidden Rose');
    await user.click(submitButton);

    const forbiddenHeading = await screen.findByRole('heading', {
      name: 'Create draft employer is not available for this staff session',
    });
    expect(forbiddenHeading).toHaveFocus();
    const forbiddenRegion = forbiddenHeading.closest('section');
    expect(forbiddenRegion).not.toBeNull();
    expect(forbiddenRegion).toHaveAttribute('aria-live', 'assertive');
    expect(within(forbiddenRegion as HTMLElement).getByText(
      'This staff session is not allowed to create draft employers.',
    )).toBeInTheDocument();
    expect(document.body.textContent).not.toContain('403');
    expect(document.body.textContent).not.toContain('Forbidden Rose');
    expect(document.body.textContent).not.toContain('66666666-6666-4666-8666-666666666666');
    expect(typeSelect).toHaveValue('household');
    expect(nameInput).toHaveValue('Forbidden Rose');
    expect(typeSelect).not.toBeDisabled();
    expect(nameInput).not.toBeDisabled();
    expect(submitButton).not.toBeDisabled();

    await user.clear(nameInput);
    await user.type(nameInput, 'Authorized Rose');
    await user.click(submitButton);

    expect(createEmployerMock).toHaveBeenNthCalledWith(1, {
      commandId: '66666666-6666-4666-8666-666666666666',
      employerType: 'household',
      displayName: 'Forbidden Rose',
    });
    expect(createEmployerMock).toHaveBeenNthCalledWith(2, {
      commandId: '77777777-7777-4777-8777-777777777777',
      employerType: 'household',
      displayName: 'Authorized Rose',
    });
    expect(await screen.findByRole('heading', { name: 'Draft employer created' })).toBeInTheDocument();

    randomUuidSpy.mockRestore();
  });

  it('keeps conflict create authority frozen when the required abandonment search cannot complete', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    const searchEmployersMock = vi.mocked(searchEmployers);
    createEmployerMock.mockReset();
    searchEmployersMock.mockReset();
    createEmployerMock.mockResolvedValue({ ok: false, failure: { kind: 'conflict' } });
    searchEmployersMock.mockResolvedValue(null);

    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const typeSelect = screen.getByLabelText('Draft employer type');
    const nameInput = screen.getByLabelText('Draft employer display name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'business');
    await user.type(nameInput, 'Conflict Rose');
    await user.click(submitButton);

    const conflictHeading = await screen.findByRole('heading', { name: 'Create is blocked until you search first' });
    const conflictRegion = conflictHeading.closest('section');
    expect(conflictRegion).not.toBeNull();

    await user.click(within(conflictRegion as HTMLElement).getByRole('button', { name: 'Abandon blocked create and search' }));

    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(searchEmployersMock).toHaveBeenCalledWith({
      displayNameQuery: 'Conflict Rose',
      employerType: undefined,
      cursor: null,
    });
    expect(typeSelect).toBeDisabled();
    expect(nameInput).toBeDisabled();
    expect(submitButton).toBeDisabled();
    expect(screen.getByRole('alert')).toHaveTextContent(
      'The required follow-up search could not complete. Retry the search before starting a changed create attempt.',
    );

    confirmSpy.mockRestore();
  });

  it('keeps create authority data out of browser side channels', async () => {
    const user = userEvent.setup();
    const createEmployerMock = vi.mocked(createEmployer);
    createEmployerMock.mockReset();
    createEmployerMock.mockResolvedValue({ ok: false, failure: { kind: 'unknown_outcome' } });

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('cccccccc-cccc-4ccc-8ccc-cccccccccccc');
    const replaceStateSpy = vi.spyOn(window.history, 'replaceState');
    const pushStateSpy = vi.spyOn(window.history, 'pushState');
    const localStorageSetItem = vi.spyOn(Storage.prototype, 'setItem');
    const localStorageGetItem = vi.spyOn(Storage.prototype, 'getItem');
    const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => undefined);
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined);

    window.history.replaceState({}, '', '/employers');

    render(
      <LanguageProvider>
        <App />
      </LanguageProvider>,
    );

    replaceStateSpy.mockClear();
    pushStateSpy.mockClear();

    const typeSelect = await screen.findByLabelText('Draft employer type');
    const nameInput = screen.getByLabelText('Draft employer display name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    expect(nameInput).toHaveAttribute('autocomplete', 'off');
    expect(nameInput).toHaveAttribute('autocorrect', 'off');
    expect(nameInput).toHaveAttribute('autocapitalize', 'none');
    expect(nameInput).toHaveAttribute('spellcheck', 'false');

    await user.selectOptions(typeSelect, 'business');
    await user.type(nameInput, 'SYNTHETIC_CREATE_BODY_SECRET');
    await user.click(submitButton);

    await screen.findByRole('heading', { name: 'Create outcome is unknown' });

    expect(document.body.textContent).not.toContain('SYNTHETIC_CREATE_BODY_SECRET');
    expect(document.body.textContent).not.toContain('cccccccc-cccc-4ccc-8ccc-cccccccccccc');
    expect(screen.queryByDisplayValue('SYNTHETIC_CREATE_BODY_SECRET')).not.toBeInTheDocument();

    expect(window.location.pathname).toBe('/employers');
    expect(window.location.search).toBe('');
    expect(window.location.hash).toBe('');
    expect(replaceStateSpy).not.toHaveBeenCalled();
    expect(pushStateSpy).not.toHaveBeenCalled();
    expect(localStorageSetItem).not.toHaveBeenCalled();
    expect(localStorageGetItem).not.toHaveBeenCalled();
    expect(consoleLog).not.toHaveBeenCalled();
    expect(consoleWarn).not.toHaveBeenCalled();
    expect(consoleError).not.toHaveBeenCalled();

    const dataAttributeValues = Array.from(document.querySelectorAll<HTMLElement>('*')).flatMap((element) =>
      element.getAttributeNames()
        .filter((attributeName) => attributeName.startsWith('data-'))
        .map((attributeName) => element.getAttribute(attributeName) ?? ''),
    );

    expect(dataAttributeValues.join(' ')).not.toContain('SYNTHETIC_CREATE_BODY_SECRET');
    expect(dataAttributeValues.join(' ')).not.toContain('cccccccc-cccc-4ccc-8ccc-cccccccccccc');

    render(<div>SYNTHETIC_EMPLOYER_SECRET SYNTHETIC_API_CURSOR</div>);

    let redactedDiagnostic = '';

    try {
      screen.getByRole('heading', { name: 'Missing create diagnostic target' });
    } catch (error) {
      redactedDiagnostic = error instanceof Error ? error.message : String(error);
    }

    expect(redactedDiagnostic).toContain(VALUE_SAFE_TESTING_LIBRARY_MESSAGE);
    expect(redactedDiagnostic).not.toContain('SYNTHETIC_EMPLOYER_SECRET');
    expect(redactedDiagnostic).not.toContain('SYNTHETIC_API_CURSOR');
    expect(redactedDiagnostic).not.toContain('cccccccc-cccc-4ccc-8ccc-cccccccccccc');

    randomUuidSpy.mockRestore();
  });

  it('revision flow never accesses Cache API or service workers and never exposes values in browser or diagnostic channels', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const reviseEmployerMock = vi.mocked(reviseEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    reviseEmployerMock.mockReset();

    searchEmployersMock.mockResolvedValueOnce({
      ok: true,
      value: {
        items: [
          {
            employerId: 'd5d5d5d5-d5d5-45d5-85d5-d5d5d5d5d5d5',
            employerType: 'business',
            displayName: 'Revision Privacy Draft',
            lifecycleStatus: 'draft',
          },
        ],
        nextCursor: null,
      },
    });
    getEmployerMock.mockResolvedValueOnce({
      ok: true,
      value: {
        employerId: 'd5d5d5d5-d5d5-45d5-85d5-d5d5d5d5d5d5',
        employerType: 'business',
        displayName: 'Revision Privacy Draft',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
        version: 7,
        updatedAt: '2026-08-11T09:10:00Z',
      },
    });
    reviseEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } });

    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('dddddddd-dddd-4ddd-8ddd-dddddddddddd');
    const replaceStateSpy = vi.spyOn(window.history, 'replaceState');
    const pushStateSpy = vi.spyOn(window.history, 'pushState');
    const localStorageSetItem = vi.spyOn(Storage.prototype, 'setItem');
    const localStorageGetItem = vi.spyOn(Storage.prototype, 'getItem');
    const sessionStorageSetItem = vi.spyOn(Storage.prototype, 'setItem');
    const sessionStorageGetItem = vi.spyOn(Storage.prototype, 'getItem');
    const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => undefined);
    const consoleInfo = vi.spyOn(console, 'info').mockImplementation(() => undefined);
    const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined);
    const cacheOpenSpy = vi.fn();
    const cachesGetterSpy = vi.fn(() => ({ open: cacheOpenSpy }));
    const originalCachesDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'caches');
    Object.defineProperty(globalThis, 'caches', {
      configurable: true,
      get: cachesGetterSpy,
    });
    const serviceWorkerRegister = vi.fn();
    const originalServiceWorkerDescriptor = Object.getOwnPropertyDescriptor(navigator, 'serviceWorker');
    Object.defineProperty(navigator, 'serviceWorker', {
      configurable: true,
      value: { register: serviceWorkerRegister },
    });

    window.history.replaceState({}, '', '/employers');

    render(
      <LanguageProvider>
        <App />
      </LanguageProvider>,
    );

    replaceStateSpy.mockClear();
    pushStateSpy.mockClear();

    await user.type(screen.getByLabelText('Employer name'), 'Revision');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await user.click(screen.getByRole('button', { name: 'Revision Privacy Draft' }));
    await screen.findByRole('region', { name: 'Employer detail' });
    await user.click(screen.getByRole('button', { name: 'Edit draft employer' }));
    await user.selectOptions(screen.getByLabelText('Revision employer type'), 'household');
    await user.clear(screen.getByLabelText('Revision employer name'));
    await user.type(screen.getByLabelText('Revision employer name'), 'SYNTHETIC_REVISION_BODY_SECRET');
    await user.click(screen.getByRole('button', { name: 'Save draft employer revision' }));

    await screen.findByRole('heading', { name: 'Revision outcome is unknown' });

    expect(document.body.textContent).not.toContain('SYNTHETIC_REVISION_BODY_SECRET');
    expect(document.body.textContent).not.toContain('dddddddd-dddd-4ddd-8ddd-dddddddddddd');
    expect(document.body.textContent).not.toContain('version: 7');
    expect(screen.queryByDisplayValue('SYNTHETIC_REVISION_BODY_SECRET')).not.toBeInTheDocument();

    expect(window.location.pathname).toBe('/employers');
    expect(window.location.search).toBe('');
    expect(window.location.hash).toBe('');
    expect(replaceStateSpy).not.toHaveBeenCalled();
    expect(pushStateSpy).not.toHaveBeenCalled();
    expect(localStorageSetItem).not.toHaveBeenCalled();
    expect(localStorageGetItem).not.toHaveBeenCalled();
    expect(sessionStorageSetItem).not.toHaveBeenCalled();
    expect(sessionStorageGetItem).not.toHaveBeenCalled();
    expect(consoleLog).not.toHaveBeenCalled();
    expect(consoleInfo).not.toHaveBeenCalled();
    expect(consoleWarn).not.toHaveBeenCalled();
    expect(consoleError).not.toHaveBeenCalled();
    expect(cachesGetterSpy).not.toHaveBeenCalled();
    expect(cacheOpenSpy).not.toHaveBeenCalled();
    expect(serviceWorkerRegister).not.toHaveBeenCalled();

    const dataAttributeValues = Array.from(document.querySelectorAll<HTMLElement>('*')).flatMap((element) =>
      element.getAttributeNames()
        .filter((attributeName) => attributeName.startsWith('data-'))
        .map((attributeName) => element.getAttribute(attributeName) ?? ''),
    );

    expect(dataAttributeValues.join(' ')).not.toContain('SYNTHETIC_REVISION_BODY_SECRET');
    expect(dataAttributeValues.join(' ')).not.toContain('dddddddd-dddd-4ddd-8ddd-dddddddddddd');
    expect(dataAttributeValues.join(' ')).not.toContain('7');

    render(<div>SYNTHETIC_REVISION_DIAGNOSTIC SECRET_EXPECTED_VERSION_7</div>);

    let redactedDiagnostic = '';

    try {
      screen.getByRole('heading', { name: 'Missing revision diagnostic target' });
    } catch (error) {
      redactedDiagnostic = error instanceof Error ? error.message : String(error);
    }

    expect(redactedDiagnostic).toContain(VALUE_SAFE_TESTING_LIBRARY_MESSAGE);
    expect(redactedDiagnostic).not.toContain('SYNTHETIC_REVISION_DIAGNOSTIC');
    expect(redactedDiagnostic).not.toContain('SECRET_EXPECTED_VERSION_7');
    expect(redactedDiagnostic).not.toContain('dddddddd-dddd-4ddd-8ddd-dddddddddddd');

    randomUuidSpy.mockRestore();
    if (originalCachesDescriptor === undefined) {
      Reflect.deleteProperty(globalThis, 'caches');
    } else {
      Object.defineProperty(globalThis, 'caches', originalCachesDescriptor);
    }
    if (originalServiceWorkerDescriptor === undefined) {
      Reflect.deleteProperty(navigator, 'serviceWorker');
    } else {
      Object.defineProperty(navigator, 'serviceWorker', originalServiceWorkerDescriptor);
    }
  });

  it('keeps created detail authoritative over stale reads', async () => {
    const user = userEvent.setup();
    const stalePage = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const staleDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const createEmployerMock = vi.mocked(createEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    createEmployerMock.mockReset();
    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '12121212-1212-4212-8212-121212121212',
              employerType: 'business',
              displayName: 'Stale Search Rose',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: 'opaque-page-after-create',
        },
      })
      .mockReturnValueOnce(stalePage.promise);
    getEmployerMock.mockReturnValueOnce(staleDetail.promise);
    createEmployerMock.mockResolvedValueOnce({
      ok: true,
      value: {
        employerId: '34343434-3434-4434-8434-343434343434',
        employerType: 'business',
        displayName: 'Authoritative Create Rose',
        lifecycleStatus: 'draft',
        sourceChannel: 'staff_entry',
      },
    });
    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('dddddddd-dddd-4ddd-8ddd-dddddddddddd');

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Rose');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });

    await user.click(screen.getByRole('button', { name: 'Stale Search Rose' }));
    await user.click(screen.getByRole('button', { name: 'Load more employers' }));

    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await user.type(screen.getByLabelText('Draft employer display name'), 'Authoritative Create Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));

    const successHeading = await screen.findByRole('heading', { name: 'Draft employer created' });
    expect(successHeading).toHaveFocus();
    expect(screen.queryByRole('heading', { name: 'Search results' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Stale Search Rose' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Load more employers' })).not.toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(screen.queryByRole('region', { name: 'Employer detail' })).not.toBeInTheDocument();

    await act(async () => {
      stalePage.resolve({
        ok: true,
        value: {
          items: [
            {
              employerId: '56565656-5656-4565-8565-565656565656',
              employerType: 'household',
              displayName: 'Late Page Rose',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });
      staleDetail.resolve({ ok: false, failure: { kind: 'unavailable' } });
      await Promise.all([stalePage.promise, staleDetail.promise]);
    });

    expect(screen.queryByRole('heading', { name: 'Search results' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Late Page Rose' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Stale Search Rose' })).not.toBeInTheDocument();
    expect(screen.queryByText('Try loading another employer detail in a moment.')).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Employer detail is unavailable' })).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Draft employer created' })).toHaveFocus();

    randomUuidSpy.mockRestore();
  });

  it('does not restore Employer state from browser back-forward cache', async () => {
    const user = userEvent.setup();
    const stalePage = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const staleDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const abandonmentSearch = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    const createEmployerMock = vi.mocked(createEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    createEmployerMock.mockReset();
    searchEmployersMock
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: '67676767-6767-4676-8676-676767676767',
              employerType: 'business',
              displayName: 'BFCache Search Rose',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: 'opaque-bfcache-page',
        },
      })
      .mockReturnValueOnce(stalePage.promise)
      .mockReturnValueOnce(abandonmentSearch.promise);
    getEmployerMock.mockReturnValueOnce(staleDetail.promise);
    createEmployerMock.mockResolvedValueOnce({ ok: false, failure: { kind: 'unknown_outcome' } });
    const randomUuidSpy = vi.spyOn(globalThis.crypto, 'randomUUID').mockReturnValue('eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee');
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    const canonicalReloadSpy = vi.fn();

    render(
      <LanguageProvider>
        <EmployerWorkspace onPersistedRestore={canonicalReloadSpy} />
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Rose');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    await screen.findByRole('heading', { name: 'Search results' });

    await user.click(screen.getByRole('button', { name: 'BFCache Search Rose' }));
    await user.click(screen.getByRole('button', { name: 'Load more employers' }));
    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');

    await user.selectOptions(screen.getByLabelText('Draft employer type'), 'business');
    await user.type(screen.getByLabelText('Draft employer display name'), 'BFCache Unknown Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));

    const unknownHeading = await screen.findByRole('heading', { name: 'Create outcome is unknown' });
    const unknownRegion = unknownHeading.closest('section');
    expect(unknownRegion).not.toBeNull();

    await user.click(within(unknownRegion as HTMLElement).getByRole('button', { name: 'Abandon unknown create and search' }));
    expect(confirmSpy).toHaveBeenCalledTimes(1);

    const pageHideEvent = new Event('pagehide');
    act(() => {
      window.dispatchEvent(pageHideEvent);
    });

    expect(screen.queryByRole('heading', { name: 'Search results' })).not.toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Create outcome is unknown' })).not.toBeInTheDocument();
    expect(screen.getByLabelText('Draft employer display name')).toHaveValue('');

    const pageShowEvent = new Event('pageshow');
    Object.defineProperty(pageShowEvent, 'persisted', { configurable: true, value: true });
    act(() => {
      window.dispatchEvent(pageShowEvent);
    });

    expect(canonicalReloadSpy).toHaveBeenCalledTimes(1);
    expect(createEmployerMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      stalePage.resolve({
        ok: true,
        value: {
          items: [
            {
              employerId: '78787878-7878-4787-8787-787878787878',
              employerType: 'household',
              displayName: 'Late BFCache Page Rose',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });
      staleDetail.resolve({ ok: false, failure: { kind: 'unavailable' } });
      abandonmentSearch.resolve({ ok: true, value: { items: [], nextCursor: null } });
      await Promise.all([stalePage.promise, staleDetail.promise, abandonmentSearch.promise]);
    });

    expect(screen.queryByRole('button', { name: 'Late BFCache Page Rose' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Employer detail is unavailable' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Create outcome is unknown' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Retry same create attempt' })).not.toBeInTheDocument();
    expect(screen.getByText('Use a bounded employer name fragment to find an existing draft employer before creating another one.')).toBeInTheDocument();

    randomUuidSpy.mockRestore();
    confirmSpy.mockRestore();
  });

  it('uses text and structure for every status', async () => {
    const user = userEvent.setup();
    const deferredSearch = createDeferredPromise<Awaited<ReturnType<typeof searchEmployers>>>();
    const deferredDetail = createDeferredPromise<Awaited<ReturnType<typeof getEmployer>>>();
    const searchEmployersMock = vi.mocked(searchEmployers);
    const getEmployerMock = vi.mocked(getEmployer);
    searchEmployersMock.mockReset();
    getEmployerMock.mockReset();
    searchEmployersMock
      .mockReturnValueOnce(deferredSearch.promise)
      .mockResolvedValueOnce({
        ok: true,
        value: {
          items: [
            {
              employerId: 'abababab-abab-4bab-8bab-abababababab',
              employerType: 'business',
              displayName: 'Status Rose',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });
    getEmployerMock.mockReturnValueOnce(deferredDetail.promise);

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    const searchValidationAlert = screen.getByRole('alert');
    expect(searchValidationAlert).toHaveTextContent('Enter 2 to 100 visible characters from the employer name.');
    expect(searchValidationAlert.closest('section[aria-live]')).not.toBeNull();

    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));
    const alerts = screen.getAllByRole('alert');
    const createValidationAlert = alerts.find((alert) => alert.textContent.includes('Select either Business or Household'));
    expect(createValidationAlert).toBeDefined();
    if (createValidationAlert === undefined) {
      throw new Error('Expected create validation alert');
    }
    expect(createValidationAlert.closest('section[aria-live]')).not.toBeNull();

    await user.type(screen.getByLabelText('Employer name'), 'Rose');
    await user.click(screen.getByRole('button', { name: 'Search employers' }));
    const searchBusyStatus = screen.getByRole('status');
    expect(searchBusyStatus).toHaveTextContent('Searching employers.');
    expect(searchBusyStatus.closest('section[aria-live]')).not.toBeNull();

    await act(async () => {
      deferredSearch.resolve({
        ok: true,
        value: {
          items: [
            {
              employerId: 'abababab-abab-4bab-8bab-abababababab',
              employerType: 'business',
              displayName: 'Status Rose',
              lifecycleStatus: 'draft',
            },
          ],
          nextCursor: null,
        },
      });
      await deferredSearch.promise;
    });

    await user.click(screen.getByRole('button', { name: 'Status Rose' }));
    const detailLoadingStatus = screen.getByRole('status');
    expect(detailLoadingStatus).toHaveTextContent('Loading employer detail.');
    const detailLoadingSection = detailLoadingStatus.closest('section');
    expect(detailLoadingSection).not.toBeNull();
    expect(within(detailLoadingSection as HTMLElement).getByRole('heading', { name: 'Employer detail' })).toBeInTheDocument();

    await act(async () => {
      deferredDetail.resolve({
        ok: true,
        value: {
          employerId: 'abababab-abab-4bab-8bab-abababababab',
          employerType: 'business',
          displayName: 'Status Rose',
          lifecycleStatus: 'draft',
          sourceChannel: 'staff_entry',
          version: 1,
          updatedAt: '2026-08-11T04:35:00Z',
        },
      });
      await deferredDetail.promise;
    });
  });

  it('keeps workspace query failures value-independent', async () => {
    const user = userEvent.setup();

    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    await user.type(screen.getByLabelText('Employer name'), 'Golden Lantern Staffing');

    try {
      screen.getByText('Missing workspace diagnostic anchor');
    } catch (error) {
      const diagnosticError = error as Error;
      expect(diagnosticError.message).toContain(VALUE_SAFE_TESTING_LIBRARY_MESSAGE);
      expect(diagnosticError.message).not.toContain('Golden Lantern Staffing');
      return;
    }

    throw new Error('Expected workspace query failure');
  });

  it('honors reduced motion and narrow single-column structure', () => {
    render(
      <LanguageProvider>
        <MemoryRouter initialEntries={['/employers']}>
          <AppRoutes />
        </MemoryRouter>
      </LanguageProvider>,
    );

    const workspaceRegion = screen.getByRole('region', { name: 'Employers workspace' });
    const createForm = screen.getByRole('form', { name: 'Create a draft employer' });
    const searchForm = screen.getByRole('form', { name: 'Employer search' });

    expect(workspaceRegion).toHaveClass('workspace-stack');
    expect(workspaceRegion).toHaveAttribute('data-motion-safe', 'true');
    expect(createForm).toHaveClass('workspace-form');
    expect(searchForm).toHaveClass('workspace-form');
  });
});
