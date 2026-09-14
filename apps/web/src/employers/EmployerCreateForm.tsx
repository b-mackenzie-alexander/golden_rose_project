import type { ChangeEvent, SyntheticEvent } from 'react';
import { useEffect, useRef, useState } from 'react';

import { createEmployer, searchEmployers } from '../api/employerClient';
import type { CreateEmployerInput, EmployerDetail, EmployerType } from '../api/employerContracts';
import { useLanguage } from '../i18n/LanguageProvider';

function hasControlCharacters(value: string) {
  return /[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}]/u.test(value);
}

function isValidDisplayName(value: string) {
  const normalized = value.normalize('NFC');
  return normalized === value && value.trim().length > 0 && Array.from(value).length <= 200 && !hasControlCharacters(value);
}

function createCommandId() {
  return globalThis.crypto.randomUUID();
}

type EmployerCreateFormProps = {
  onAuthorityChange?: (state: { owner: 'create' | null; locked: boolean }) => void;
  onCreateSuccess?: (detail: EmployerDetail) => void;
  resetSignal?: number;
  searchCheckpoint?: 'empty' | 'none' | 'results';
  workspaceCommandOwner?: 'create' | 'revision' | null;
};

type CreateFailureKind = 'validation' | 'forbidden';

export function EmployerCreateForm({
  onAuthorityChange,
  onCreateSuccess,
  resetSignal = 0,
  searchCheckpoint = 'none',
  workspaceCommandOwner = null,
}: EmployerCreateFormProps) {
  const { messages } = useLanguage();
  const typeSelectRef = useRef<HTMLSelectElement>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);
  const successHeadingRef = useRef<HTMLHeadingElement>(null);
  const createFailureHeadingRef = useRef<HTMLHeadingElement>(null);
  const previousResetSignalRef = useRef(resetSignal);
  const operationGenerationRef = useRef(0);
  const authorityOperationLockRef = useRef(false);
  const lastAuthorityLockedRef = useRef(false);
  const [employerType, setEmployerType] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [createFailure, setCreateFailure] = useState<CreateFailureKind | null>(null);
  const [createdDetail, setCreatedDetail] = useState<EmployerDetail | null>(null);
  const [unknownAttempt, setUnknownAttempt] = useState<CreateEmployerInput | null>(null);
  const [conflictAttempt, setConflictAttempt] = useState<CreateEmployerInput | null>(null);
  const [isAbandonSearchPending, setIsAbandonSearchPending] = useState(false);
  const [abandonSearchFailure, setAbandonSearchFailure] = useState<string | null>(null);
  const [pendingAttempt, setPendingAttempt] = useState<{
    commandId: string;
    employerType: EmployerType;
    displayName: string;
  } | null>(null);
  const authorityLocked =
    pendingAttempt !== null || unknownAttempt !== null || conflictAttempt !== null || isAbandonSearchPending;
  const blockedByWorkspace = workspaceCommandOwner !== null && workspaceCommandOwner !== 'create';
  const searchCheckpointMessage =
    searchCheckpoint === 'empty'
      ? messages.employerCreateSearchCheckpointEmpty
      : searchCheckpoint === 'results'
        ? messages.employerCreateSearchCheckpointResults
        : messages.employerCreateSearchCheckpointNoSearch;

  useEffect(() => {
    if (lastAuthorityLockedRef.current === authorityLocked) {
      return;
    }

    lastAuthorityLockedRef.current = authorityLocked;
    onAuthorityChange?.({ owner: authorityLocked ? 'create' : null, locked: authorityLocked });
  }, [authorityLocked, onAuthorityChange]);

  useEffect(() => {
    if (createdDetail !== null) {
      successHeadingRef.current?.focus();
    }
  }, [createdDetail]);

  useEffect(() => {
    if (createFailure !== null) {
      createFailureHeadingRef.current?.focus();
    }
  }, [createFailure]);

  useEffect(() => {
    function retireCreateAuthority() {
      operationGenerationRef.current += 1;
      authorityOperationLockRef.current = false;
    }

    window.addEventListener('pagehide', retireCreateAuthority);
    return () => {
      window.removeEventListener('pagehide', retireCreateAuthority);
    };
  }, []);

  useEffect(() => {
    if (pendingAttempt === null && unknownAttempt === null) {
      return undefined;
    }

    function handleBeforeUnload(event: BeforeUnloadEvent) {
      event.preventDefault();
      // Required for current browser beforeunload prompt behavior in this bounded tracer.
      // eslint-disable-next-line @typescript-eslint/no-deprecated
      event.returnValue = '';
    }

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [pendingAttempt, unknownAttempt]);

  useEffect(() => {
    if (previousResetSignalRef.current === resetSignal) {
      return;
    }

    previousResetSignalRef.current = resetSignal;
    operationGenerationRef.current += 1;
    authorityOperationLockRef.current = false;
    setEmployerType('');
    setDisplayName('');
    setFormError(null);
    setCreateFailure(null);
    setCreatedDetail(null);
    setUnknownAttempt(null);
    setConflictAttempt(null);
    setIsAbandonSearchPending(false);
    setAbandonSearchFailure(null);
    setPendingAttempt(null);
  }, [resetSignal]);

  function handleTypeChange(event: ChangeEvent<HTMLSelectElement>) {
    if (blockedByWorkspace || unknownAttempt !== null || conflictAttempt !== null) {
      return;
    }
    setEmployerType(event.target.value);
    setAbandonSearchFailure(null);
    if (createFailure !== null) {
      setCreateFailure(null);
    }
    if (formError !== null) {
      setFormError(null);
    }
  }

  function handleNameChange(event: ChangeEvent<HTMLInputElement>) {
    if (blockedByWorkspace || unknownAttempt !== null || conflictAttempt !== null) {
      return;
    }
    setDisplayName(event.target.value);
    setAbandonSearchFailure(null);
    if (createFailure !== null) {
      setCreateFailure(null);
    }
    if (formError !== null) {
      setFormError(null);
    }
  }

  async function submitAttempt(attempt: CreateEmployerInput) {
    if (authorityOperationLockRef.current) {
      return;
    }

    authorityOperationLockRef.current = true;
    const operationGeneration = operationGenerationRef.current + 1;
    operationGenerationRef.current = operationGeneration;
    setPendingAttempt(attempt);
    setAbandonSearchFailure(null);
    setCreateFailure(null);

    try {
      const result = await createEmployer(attempt);
      if (operationGeneration !== operationGenerationRef.current) {
        return;
      }

      if (result.ok) {
        setCreateFailure(null);
        setConflictAttempt(null);
        setUnknownAttempt(null);
        setIsAbandonSearchPending(false);
        setAbandonSearchFailure(null);
        setCreatedDetail(result.value);
        setEmployerType('');
        setDisplayName('');
        onCreateSuccess?.(result.value);
        return;
      }

      if (result.failure.kind === 'unknown_outcome') {
        setCreateFailure(null);
        setEmployerType('');
        setDisplayName('');
        setConflictAttempt(null);
        setUnknownAttempt(attempt);
      } else if (result.failure.kind === 'conflict') {
        setCreateFailure(null);
        setEmployerType('');
        setDisplayName('');
        setUnknownAttempt(null);
        setConflictAttempt(attempt);
      } else if (result.failure.kind === 'validation' || result.failure.kind === 'forbidden') {
        setCreatedDetail(null);
        setUnknownAttempt(null);
        setConflictAttempt(null);
        setIsAbandonSearchPending(false);
        setAbandonSearchFailure(null);
        setCreateFailure(result.failure.kind);
      }
    } finally {
      if (operationGeneration === operationGenerationRef.current) {
        setPendingAttempt(null);
        authorityOperationLockRef.current = false;
      }
    }
  }

  async function completeAbandonSearch(attempt: CreateEmployerInput, clearAttempt: () => void) {
    if (authorityOperationLockRef.current) {
      return;
    }

    authorityOperationLockRef.current = true;
    const operationGeneration = operationGenerationRef.current + 1;
    operationGenerationRef.current = operationGeneration;
    setIsAbandonSearchPending(true);
    setAbandonSearchFailure(null);

    try {
      const result = await searchEmployers({
        displayNameQuery: attempt.displayName,
        employerType: undefined,
        cursor: null,
      });

      if (operationGeneration !== operationGenerationRef.current) {
        return;
      }

      if (result === null || !result.ok) {
        setAbandonSearchFailure(messages.employerCreateAbandonSearchFailure);
        return;
      }

      clearAttempt();
      setEmployerType('');
      setDisplayName('');
      setAbandonSearchFailure(null);
    } finally {
      if (operationGeneration === operationGenerationRef.current) {
        setIsAbandonSearchPending(false);
        authorityOperationLockRef.current = false;
      }
    }
  }

  async function handleAbandonUnknownAttempt() {
    if (unknownAttempt === null || pendingAttempt !== null || isAbandonSearchPending || authorityOperationLockRef.current) {
      return;
    }

    if (!window.confirm(messages.employerCreateAbandonBody)) {
      return;
    }

    await completeAbandonSearch(unknownAttempt, () => {
      setUnknownAttempt(null);
    });
  }

  async function handleAbandonConflictAttempt() {
    if (conflictAttempt === null || pendingAttempt !== null || isAbandonSearchPending || authorityOperationLockRef.current) {
      return;
    }

    if (!window.confirm(messages.employerCreateAbandonBody)) {
      return;
    }

    await completeAbandonSearch(conflictAttempt, () => {
      setConflictAttempt(null);
    });
  }

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();

    if (blockedByWorkspace || pendingAttempt !== null || unknownAttempt !== null || conflictAttempt !== null || isAbandonSearchPending) {
      return;
    }

    if (employerType !== 'business' && employerType !== 'household') {
      setFormError(messages.employerCreateTypeError);
      typeSelectRef.current?.focus();
      return;
    }

    if (!isValidDisplayName(displayName)) {
      setFormError(messages.employerCreateNameError);
      nameInputRef.current?.focus();
      return;
    }

    setFormError(null);
    const nextAttempt: CreateEmployerInput = {
      commandId: createCommandId(),
      employerType,
      displayName,
    };
    await submitAttempt(nextAttempt);
  }

  return (
    <form
      aria-label={messages.employerCreateHeading}
      className="workspace-form"
      onSubmit={(event) => {
        void handleSubmit(event);
      }}
    >
      <h3 id="employer-create-heading">{messages.employerCreateHeading}</h3>
      <p>{messages.employerCreateWarning}</p>
      <p className="workflow-note">{searchCheckpointMessage}</p>
      {formError === null ? null : (
        <section aria-label={messages.employerCreateHeading} aria-live="assertive">
          <p role="alert">{formError}</p>
        </section>
      )}

      {abandonSearchFailure === null ? null : (
        <section aria-label={messages.employerCreateHeading} aria-live="assertive">
          <p role="alert">{abandonSearchFailure}</p>
        </section>
      )}

      {createFailure === null ? null : (
        <section aria-label={messages.employerCreateHeading} aria-live="assertive">
          <h3 ref={createFailureHeadingRef} tabIndex={-1}>
            {createFailure === 'validation'
              ? messages.employerCreateValidationFailureHeading
              : messages.employerCreateForbiddenFailureHeading}
          </h3>
          <p>
            {createFailure === 'validation'
              ? messages.employerCreateValidationFailureBody
              : messages.employerCreateForbiddenFailureBody}
          </p>
        </section>
      )}

      <div>
        <label htmlFor="create-employer-type">{messages.employerCreateTypeLabel}</label>
        <select
          className="focus-ring control-44"
          id="create-employer-type"
          name="createEmployerType"
          disabled={blockedByWorkspace || pendingAttempt !== null || unknownAttempt !== null || conflictAttempt !== null || isAbandonSearchPending}
          onChange={handleTypeChange}
          ref={typeSelectRef}
          value={employerType}
        >
          <option value="">{messages.employerSearchTypeAnyOption}</option>
          <option value="business">{messages.employerTypeBusiness}</option>
          <option value="household">{messages.employerTypeHousehold}</option>
        </select>
      </div>

      <div>
        <label htmlFor="create-employer-name">{messages.employerCreateNameLabel}</label>
        <input
          autoCapitalize="none"
          autoComplete="off"
          autoCorrect="off"
          className="focus-ring control-44"
          id="create-employer-name"
          name="createEmployerName"
          disabled={blockedByWorkspace || pendingAttempt !== null || unknownAttempt !== null || conflictAttempt !== null || isAbandonSearchPending}
          onChange={handleNameChange}
          ref={nameInputRef}
          spellCheck={false}
          type="text"
          value={displayName}
        />
      </div>

      <button
        className="focus-ring control-44"
        disabled={blockedByWorkspace || pendingAttempt !== null || unknownAttempt !== null || conflictAttempt !== null || isAbandonSearchPending}
        type="submit"
      >
        {messages.employerCreateSubmit}
      </button>

      {conflictAttempt === null ? null : (
        <section aria-live="assertive">
          <h3>{messages.employerCreateConflictHeading}</h3>
          <p>{messages.employerCreateAbandonBody}</p>
          <button
            className="focus-ring control-44"
            disabled={pendingAttempt !== null || isAbandonSearchPending}
            onClick={() => {
              void handleAbandonConflictAttempt();
            }}
            type="button"
          >
            {messages.employerCreateConflictAction}
          </button>
        </section>
      )}

      {unknownAttempt === null ? null : (
        <section aria-live="assertive">
          <h3>{messages.employerCreateUnknownHeading}</h3>
          <p>{messages.employerCreateUnknownBody}</p>
          <button
            className="focus-ring control-44"
            disabled={pendingAttempt !== null || isAbandonSearchPending}
            onClick={() => {
              if (pendingAttempt !== null || isAbandonSearchPending) {
                return;
              }
              void submitAttempt(unknownAttempt);
            }}
            type="button"
          >
            {messages.employerCreateUnknownRetry}
          </button>
          <p>{messages.employerCreateAbandonBody}</p>
          <button
            className="focus-ring control-44"
            disabled={pendingAttempt !== null || isAbandonSearchPending}
            onClick={() => {
              void handleAbandonUnknownAttempt();
            }}
            type="button"
          >
            {messages.employerCreateAbandonAction}
          </button>
        </section>
      )}

      {createdDetail === null ? null : (
        <section aria-live="polite">
          <h3 ref={successHeadingRef} tabIndex={-1}>
            {messages.employerCreateSuccessHeading}
          </h3>
          <dl>
            <div>
              <dt>{messages.employerDetailNameLabel}</dt>
              <dd>{createdDetail.displayName}</dd>
            </div>
            <div>
              <dt>{messages.employerDetailTypeLabel}</dt>
              <dd>{createdDetail.employerType === 'business' ? messages.employerTypeBusiness : messages.employerTypeHousehold}</dd>
            </div>
            <div>
              <dt>{messages.employerDetailLifecycleLabel}</dt>
              <dd>{messages.employerLifecycleDraft}</dd>
            </div>
            <div>
              <dt>{messages.employerDetailSourceLabel}</dt>
              <dd>{messages.employerSourceStaffEntry}</dd>
            </div>
          </dl>
        </section>
      )}
    </form>
  );
}
