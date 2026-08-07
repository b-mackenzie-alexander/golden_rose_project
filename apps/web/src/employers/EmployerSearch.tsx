import { useCallback, useEffect, useMemo, useRef, useState, type ChangeEvent, type SyntheticEvent } from 'react';

import { getEmployer, searchEmployers } from '../api/employerClient';
import type {
  ApiFailureKind,
  EmployerDetail as EmployerDetailRecord,
  EmployerSummary,
  EmployerType,
  SearchEmployersInput,
} from '../api/employerContracts';
import { useLanguage } from '../i18n/LanguageProvider';
import { EmployerDetail } from './EmployerDetail';

type SearchUiState = 'idle' | 'empty' | 'results' | 'failure';

type SearchFailureState = {
  kind: Extract<ApiFailureKind, 'validation' | 'forbidden' | 'unavailable' | 'unexpected'>;
};

type PaginationFailureState = {
  kind: Extract<ApiFailureKind, 'unavailable'>;
};

type DetailFailureState = {
  kind: Extract<ApiFailureKind, 'not_found' | 'forbidden' | 'unavailable'>;
};

function isValidName(value: string) {
  const trimmed = value.trim();
  const codePoints = Array.from(trimmed).length;

  return codePoints >= 2 && codePoints <= 100 && !/[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}]/u.test(value);
}

type EmployerSearchProps = {
  resetSignal?: number;
};

export function EmployerSearch({ resetSignal = 0 }: EmployerSearchProps) {
  const { messages } = useLanguage();
  const emptyHeadingRef = useRef<HTMLHeadingElement>(null);
  const resultsHeadingRef = useRef<HTMLHeadingElement>(null);
  const failureHeadingRef = useRef<HTMLHeadingElement>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);
  const resultButtonRefs = useRef(new Map<string, HTMLButtonElement>());
  const pendingResultsFocusIdRef = useRef<string | null>(null);
  const activeSearchControllerRef = useRef<AbortController | null>(null);
  const activeDetailControllerRef = useRef<AbortController | null>(null);
  const detailRequestVersionRef = useRef(0);
  const previousResetSignalRef = useRef(resetSignal);
  const [displayNameQuery, setDisplayNameQuery] = useState('');
  const [employerType, setEmployerType] = useState('');
  const [nameError, setNameError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [searchState, setSearchState] = useState<SearchUiState>('idle');
  const [results, setResults] = useState<EmployerSummary[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [failureState, setFailureState] = useState<SearchFailureState | null>(null);
  const [paginationFailureState, setPaginationFailureState] = useState<PaginationFailureState | null>(null);
  const [submittedSearch, setSubmittedSearch] = useState<Pick<SearchEmployersInput, 'displayNameQuery' | 'employerType'> | null>(null);
  const [detail, setDetail] = useState<EmployerDetailRecord | null>(null);
  const [detailFailureState, setDetailFailureState] = useState<DetailFailureState | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  const currentSearch = useMemo(
    () => ({
      displayNameQuery: displayNameQuery.trim(),
      employerType: employerType === '' ? undefined : (employerType as EmployerType),
    }),
    [displayNameQuery, employerType],
  );

  const isDuplicatePendingSearch =
    isSearching &&
    submittedSearch?.displayNameQuery === currentSearch.displayNameQuery &&
    submittedSearch.employerType === currentSearch.employerType;

  const submittedSearchSummary =
    searchState === 'empty' || submittedSearch === null
      ? null
      : `${messages.employerSearchSubmittedLabel}: ${submittedSearch.displayNameQuery}${
          submittedSearch.employerType === undefined
            ? ''
            : ` · ${submittedSearch.employerType === 'business' ? messages.employerTypeBusiness : messages.employerTypeHousehold}`
        }`;

  const failureCopy = useMemo(() => {
    if (failureState === null) {
      return null;
    }

    switch (failureState.kind) {
      case 'validation':
        return {
          heading: messages.employerSearchValidationFailureHeading,
          body: messages.employerSearchValidationFailureBody,
          retryable: false,
        };
      case 'forbidden':
        return {
          heading: messages.employerSearchForbiddenFailureHeading,
          body: messages.employerSearchForbiddenFailureBody,
          retryable: false,
        };
      case 'unavailable':
        return {
          heading: messages.employerSearchUnavailableFailureHeading,
          body: messages.employerSearchUnavailableFailureBody,
          retryable: true,
        };
      case 'unexpected':
        return {
          heading: messages.employerSearchUnexpectedFailureHeading,
          body: messages.employerSearchUnexpectedFailureBody,
          retryable: false,
        };
    }
  }, [failureState, messages]);

  useEffect(() => {
    if (searchState === 'empty') {
      emptyHeadingRef.current?.focus();
    }
  }, [searchState]);

  useEffect(() => {
    if (searchState === 'results') {
      if (pendingResultsFocusIdRef.current !== null) {
        resultButtonRefs.current.get(pendingResultsFocusIdRef.current)?.focus();
        pendingResultsFocusIdRef.current = null;
        return;
      }

      resultsHeadingRef.current?.focus();
    }
  }, [results, searchState]);

  useEffect(() => {
    if (searchState === 'failure') {
      failureHeadingRef.current?.focus();
    }
  }, [searchState]);

  const invalidatePendingDetail = useCallback(() => {
    if (activeDetailControllerRef.current !== null) {
      activeDetailControllerRef.current.abort();
      activeDetailControllerRef.current = null;
    }

    detailRequestVersionRef.current += 1;
    setDetail(null);
    setDetailFailureState(null);
    setIsDetailLoading(false);
  }, []);

  const invalidatePendingSearch = useCallback((options?: { preserveSubmittedSearch?: boolean }) => {
    if (activeSearchControllerRef.current !== null) {
      activeSearchControllerRef.current.abort();
      activeSearchControllerRef.current = null;
    }

    setIsSearching(false);
    setIsLoadingMore(false);
    setSearchState('idle');
    setResults([]);
    setNextCursor(null);
    setFailureState(null);
    setPaginationFailureState(null);
    invalidatePendingDetail();
    pendingResultsFocusIdRef.current = null;

    if (options?.preserveSubmittedSearch === false) {
      setSubmittedSearch(null);
    }
  }, [invalidatePendingDetail]);

  useEffect(() => {
    return () => {
      invalidatePendingSearch({ preserveSubmittedSearch: false });
    };
  }, [invalidatePendingSearch]);

  useEffect(() => {
    if (previousResetSignalRef.current === resetSignal) {
      return;
    }

    previousResetSignalRef.current = resetSignal;
    invalidatePendingSearch({ preserveSubmittedSearch: false });
  }, [invalidatePendingSearch, resetSignal]);

  function handleNameChange(event: ChangeEvent<HTMLInputElement>) {
    setDisplayNameQuery(event.target.value);
    invalidatePendingSearch();
    if (nameError !== null) {
      setNameError(null);
    }
  }

  function handleTypeChange(event: ChangeEvent<HTMLSelectElement>) {
    setEmployerType(event.target.value);
    invalidatePendingSearch();
  }

  async function runSearch(
    nextSubmittedSearch: Pick<SearchEmployersInput, 'displayNameQuery' | 'employerType'>,
    options?: { append?: boolean; cursor?: string | null },
  ) {
    const controller = new AbortController();
    const isPaginationRequest = options?.append === true;

    activeSearchControllerRef.current = controller;
    setSubmittedSearch(nextSubmittedSearch);
    if (isPaginationRequest) {
      setPaginationFailureState(null);
      setIsLoadingMore(true);
    } else {
      setFailureState(null);
      setPaginationFailureState(null);
      setIsSearching(true);
    }

    try {
      const result = await searchEmployers({
        ...nextSubmittedSearch,
        cursor: options?.cursor ?? null,
        signal: controller.signal,
      });

      if (activeSearchControllerRef.current !== controller || result === null) {
        return;
      }

      if (result.ok) {
        setNextCursor(result.value.nextCursor);
        if (isPaginationRequest) {
          setResults((currentResults) => {
            const seenIds = new Set(currentResults.map((item) => item.employerId));
            const appendedItems = result.value.items.filter((item) => {
              if (seenIds.has(item.employerId)) {
                return false;
              }

              seenIds.add(item.employerId);
              return true;
            });

            pendingResultsFocusIdRef.current = appendedItems[0]?.employerId ?? null;

            return [...currentResults, ...appendedItems];
          });
          setSearchState('results');
        } else {
          setResults(result.value.items);
          pendingResultsFocusIdRef.current = null;
          setSearchState(result.value.items.length === 0 ? 'empty' : 'results');
        }
        return;
      }

      if (
        result.failure.kind === 'validation' ||
        result.failure.kind === 'forbidden' ||
        result.failure.kind === 'unavailable' ||
        result.failure.kind === 'unexpected'
      ) {
        if (isPaginationRequest) {
          if (result.failure.kind === 'unavailable') {
            setPaginationFailureState({ kind: 'unavailable' });
          }
          return;
        }

        setResults([]);
        setFailureState({ kind: result.failure.kind });
        setSearchState('failure');
      }
    } finally {
      if (activeSearchControllerRef.current === controller) {
        activeSearchControllerRef.current = null;
        if (isPaginationRequest) {
          setIsLoadingMore(false);
        } else {
          setIsSearching(false);
        }
      }
    }
  }

  function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!isValidName(displayNameQuery)) {
      setNameError(messages.employerSearchNameError);
      nameInputRef.current?.focus();
      return;
    }

    if (isDuplicatePendingSearch) {
      return;
    }

    setNameError(null);
    invalidatePendingSearch();

    void runSearch({
      displayNameQuery: currentSearch.displayNameQuery,
      employerType: currentSearch.employerType,
    });
  }

  function handleRetry() {
    if (submittedSearch === null || isSearching || failureState?.kind !== 'unavailable') {
      return;
    }

    invalidatePendingSearch();
    void runSearch(submittedSearch);
  }

  function handleLoadMore() {
    if (submittedSearch === null || nextCursor === null || isLoadingMore || isSearching) {
      return;
    }

    void runSearch(submittedSearch, { append: true, cursor: nextCursor });
  }

  function handleRetryLoadMore() {
    if (submittedSearch === null || nextCursor === null || isLoadingMore || paginationFailureState?.kind !== 'unavailable') {
      return;
    }

    void runSearch(submittedSearch, { append: true, cursor: nextCursor });
  }

  async function handleSelectEmployer(employerId: string) {
    const controller = new AbortController();
    const requestVersion = detailRequestVersionRef.current + 1;

    if (activeDetailControllerRef.current !== null) {
      activeDetailControllerRef.current.abort();
    }

    activeDetailControllerRef.current = controller;
    detailRequestVersionRef.current = requestVersion;
    setDetail(null);
    setDetailFailureState(null);
    setIsDetailLoading(true);

    try {
      const result = await getEmployer(employerId, { signal: controller.signal });

      if (detailRequestVersionRef.current !== requestVersion || result === null) {
        return;
      }

      if (result.ok && result.value.employerId === employerId) {
        setDetail(result.value);
      } else if (
        !result.ok &&
        (result.failure.kind === 'not_found' || result.failure.kind === 'forbidden' || result.failure.kind === 'unavailable')
      ) {
        setDetailFailureState({ kind: result.failure.kind });
      }
    } finally {
      if (activeDetailControllerRef.current === controller) {
        activeDetailControllerRef.current = null;
      }

      if (detailRequestVersionRef.current === requestVersion) {
        setIsDetailLoading(false);
      }
    }
  }

  return (
    <form aria-label={messages.employerSearchFormLabel} autoComplete="off" className="workspace-panel" onSubmit={handleSubmit}>
      <div>
        <label htmlFor="employer-name-query">{messages.employerSearchNameLabel}</label>
        <input
          aria-describedby={nameError === null ? undefined : 'employer-search-error'}
          aria-invalid={nameError === null ? undefined : 'true'}
          autoCapitalize="none"
          autoComplete="off"
          autoCorrect="off"
          className="focus-ring"
          id="employer-name-query"
          name="displayNameQuery"
          onChange={handleNameChange}
          ref={nameInputRef}
          spellCheck={false}
          type="text"
          value={displayNameQuery}
        />
      </div>

      {nameError === null ? null : (
        <section aria-label={messages.employerSearchValidationFailureHeading} aria-live="assertive">
          <p id="employer-search-error" role="alert">
            {nameError}
          </p>
        </section>
      )}

      {isSearching ? (
        <section aria-label={messages.employerSearchBusy} aria-live="polite">
          <p role="status">{messages.employerSearchBusy}</p>
        </section>
      ) : null}

      {submittedSearchSummary === null ? null : <p>{submittedSearchSummary}</p>}

      {searchState !== 'empty' ? null : (
        <div>
          <h3 ref={emptyHeadingRef} tabIndex={-1}>
            {messages.employerSearchEmptyHeading}
          </h3>
          <p>{messages.employerSearchEmptyBody}</p>
        </div>
      )}

      {searchState !== 'failure' || failureCopy === null ? null : (
        <section aria-live="assertive">
          <h3 ref={failureHeadingRef} tabIndex={-1}>
            {failureCopy.heading}
          </h3>
          <p>{failureCopy.body}</p>
          {failureCopy.retryable ? (
            <button className="focus-ring" onClick={handleRetry} type="button">
              {messages.employerSearchRetry}
            </button>
          ) : null}
        </section>
      )}

      {searchState !== 'results' ? null : (
        <section aria-label={messages.employerSearchResultsHeading}>
          <h3 ref={resultsHeadingRef} tabIndex={-1}>
            {messages.employerSearchResultsHeading}
          </h3>
          <ul>
            {results.map((result) => (
              <li key={result.employerId}>
                <button
                  className="focus-ring"
                  onClick={() => {
                    void handleSelectEmployer(result.employerId);
                  }}
                  ref={(element) => {
                    if (element === null) {
                      resultButtonRefs.current.delete(result.employerId);
                      return;
                    }

                    resultButtonRefs.current.set(result.employerId, element);
                  }}
                  type="button"
                >
                  {result.displayName}
                </button>
                <p>{result.employerType === 'business' ? messages.employerTypeBusiness : messages.employerTypeHousehold}</p>
                <p>{messages.employerLifecycleDraft}</p>
              </li>
            ))}
          </ul>
          {paginationFailureState?.kind !== 'unavailable' ? null : (
            <div aria-live="assertive">
              <p>{messages.employerSearchPageUnavailableBody}</p>
              <button className="focus-ring" onClick={handleRetryLoadMore} type="button">
                {messages.employerSearchRetryLoadMore}
              </button>
            </div>
          )}
          {nextCursor === null ? null : (
            <button className="focus-ring" disabled={isLoadingMore} onClick={handleLoadMore} type="button">
              {messages.employerSearchLoadMore}
            </button>
          )}
          <EmployerDetail detail={detail} failureKind={detailFailureState?.kind ?? null} isLoading={isDetailLoading} />
        </section>
      )}

      <div>
        <label htmlFor="employer-type">{messages.employerSearchTypeLabel}</label>
        <select className="focus-ring" id="employer-type" name="employerType" onChange={handleTypeChange} value={employerType}>
          <option value="">{messages.employerSearchTypeAnyOption}</option>
          <option value="business">{messages.employerTypeBusiness}</option>
          <option value="household">{messages.employerTypeHousehold}</option>
        </select>
      </div>

      <button className="focus-ring" disabled={isDuplicatePendingSearch} type="submit">
        {messages.employerSearchSubmit}
      </button>
    </form>
  );
}
