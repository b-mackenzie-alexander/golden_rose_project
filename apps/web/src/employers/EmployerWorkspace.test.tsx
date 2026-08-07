import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router';
import { vi } from 'vitest';

import { createEmployer, getEmployer, searchEmployers } from '../api/employerClient';
import { App, AppRoutes } from '../app/App';
import { EmployerWorkspace } from './EmployerWorkspace';
import { LanguageProvider } from '../i18n/LanguageProvider';

vi.mock('../api/employerClient', () => ({
  createEmployer: vi.fn(),
  getEmployer: vi.fn(),
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
        <EmployerWorkspace />
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

    expect(screen.getByRole('heading', { name: 'Search for an employer' })).toBeInTheDocument();
    expect(
      screen.getByText('Use a bounded employer name fragment to begin a staff-only synthetic search.'),
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

  it('maps search failures to bounded localized states', async () => {
    const user = userEvent.setup();
    const searchEmployersMock = vi.mocked(searchEmployers);
    searchEmployersMock.mockReset();
    searchEmployersMock
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'validation' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'forbidden' } })
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

    failureHeading = await screen.findByRole('heading', { name: 'Search is temporarily unavailable' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('Retry the same employer search when the service becomes available.')).toBeInTheDocument();

    const retryButton = screen.getByRole('button', { name: 'Retry search' });
    await user.click(retryButton);

    expect(searchEmployersMock).toHaveBeenNthCalledWith(
      4,
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

    expect(redactedDiagnostic).toContain('[REDACTED]');
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
    expect(screen.getByRole('button', { name: 'Load more employers' })).toBeInTheDocument();

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
    expect(screen.getByRole('heading', { name: 'Employer detail' })).toBeInTheDocument();
    expect(screen.getByRole('status')).toHaveTextContent('Loading employer detail.');

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
        },
      })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'not_found' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'forbidden' } })
      .mockResolvedValueOnce({ ok: false, failure: { kind: 'unavailable' } });

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

    let failureHeading = await screen.findByRole('heading', { name: 'Employer detail is no longer available' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('The selected employer detail could not be found for this staff workspace.')).toBeInTheDocument();
    expect(screen.queryByText('Previously Visible Detail')).not.toBeInTheDocument();
    expect(screen.queryByText('50505050-5050-4050-8050-505050505050')).not.toBeInTheDocument();

    await user.click(selectButton);

    failureHeading = await screen.findByRole('heading', { name: 'Employer detail is not available for this staff session' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('This staff session is not allowed to view the selected employer detail.')).toBeInTheDocument();

    await user.click(selectButton);

    failureHeading = await screen.findByRole('heading', { name: 'Employer detail is temporarily unavailable' });
    expect(failureHeading).toHaveFocus();
    expect(screen.getByText('Retry selecting the employer detail when the service becomes available.')).toBeInTheDocument();
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
    expect(screen.getByText('Create only fictional synthetic draft employers in this local staff workspace.')).toBeInTheDocument();
    expect(screen.getByLabelText('Create employer type')).toBeInTheDocument();
    expect(screen.getByLabelText('Create employer name')).toBeInTheDocument();
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

    const typeSelect = screen.getByLabelText('Create employer type');
    const nameInput = screen.getByLabelText('Create employer name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'business');
    await user.type(nameInput, 'Á'.repeat(200));
    await user.click(submitButton);

    expect(createEmployerMock).toHaveBeenCalledTimes(1);
    expect(createEmployerMock).toHaveBeenCalledWith(
      expect.objectContaining({
        employerType: 'business',
        displayName: 'Á'.repeat(200),
      }),
    );

    await user.clear(nameInput);
    await user.type(nameInput, 'A'.repeat(201));
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

    const typeSelect = screen.getByLabelText('Create employer type');
    const nameInput = screen.getByLabelText('Create employer name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'business');
    await user.type(nameInput, 'Immutable Pending Rose');
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

    const typeSelect = screen.getByLabelText('Create employer type');
    const nameInput = screen.getByLabelText('Create employer name');
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

    const typeSelect = screen.getByLabelText('Create employer type');
    const nameInput = screen.getByLabelText('Create employer name');
    const submitButton = screen.getByRole('button', { name: 'Create draft employer' });

    await user.selectOptions(typeSelect, 'business');
    await user.type(nameInput, 'Unknown Outcome Rose');
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

    await user.selectOptions(screen.getByLabelText('Create employer type'), 'business');
    await user.type(screen.getByLabelText('Create employer name'), 'Pending Create Rose');
    await user.click(screen.getByRole('button', { name: 'Create draft employer' }));

    const beforeUnloadEvent = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(beforeUnloadEvent);
    expect(beforeUnloadEvent.defaultPrevented).toBe(true);

    await act(async () => {
      deferredCreate.resolve({ ok: false, failure: { kind: 'unknown_outcome' } });
      await deferredCreate.promise;
    });
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

    const typeSelect = screen.getByLabelText('Create employer type');
    const nameInput = screen.getByLabelText('Create employer name');
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

    const typeSelect = screen.getByLabelText('Create employer type');
    const nameInput = screen.getByLabelText('Create employer name');
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

    const typeSelect = screen.getByLabelText('Create employer type');
    const nameInput = screen.getByLabelText('Create employer name');
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

    const typeSelect = screen.getByLabelText('Create employer type');
    const nameInput = screen.getByLabelText('Create employer name');
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

    const typeSelect = await screen.findByLabelText('Create employer type');
    const nameInput = screen.getByLabelText('Create employer name');
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

    expect(redactedDiagnostic).toContain('[REDACTED]');
    expect(redactedDiagnostic).not.toContain('SYNTHETIC_EMPLOYER_SECRET');
    expect(redactedDiagnostic).not.toContain('SYNTHETIC_API_CURSOR');
    expect(redactedDiagnostic).not.toContain('cccccccc-cccc-4ccc-8ccc-cccccccccccc');

    randomUuidSpy.mockRestore();
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

    await user.selectOptions(screen.getByLabelText('Create employer type'), 'business');
    await user.type(screen.getByLabelText('Create employer name'), 'Authoritative Create Rose');
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

    await user.selectOptions(screen.getByLabelText('Create employer type'), 'business');
    await user.type(screen.getByLabelText('Create employer name'), 'BFCache Unknown Rose');
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
    expect(screen.getByLabelText('Create employer name')).toHaveValue('');

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
    expect(screen.getByText('Use a bounded employer name fragment to begin a staff-only synthetic search.')).toBeInTheDocument();

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
        },
      });
      await deferredDetail.promise;
    });
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
    expect(createForm).toHaveClass('workspace-panel');
    expect(searchForm).toHaveClass('workspace-panel');
  });
});
