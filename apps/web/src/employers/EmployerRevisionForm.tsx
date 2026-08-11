import { useEffect, useRef, useState, type ChangeEvent, type SyntheticEvent } from 'react';

import { reviseEmployer } from '../api/employerClient';
import type { ReviseEmployerInput, RevisionEmployerDetail, ReviseEmployerResult } from '../api/employerContracts';
import { useLanguage } from '../i18n/LanguageProvider';

function hasControlCharacters(value: string) {
  return /[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}]/u.test(value);
}

function isValidDisplayName(value: string) {
  const normalized = value.normalize('NFC');
  return normalized === value && value.trim().length > 0 && Array.from(value).length <= 200 && !hasControlCharacters(value);
}

function isNormalizedNoOpEdit(detail: RevisionEmployerDetail, employerType: string, displayName: string) {
  return detail.employerType === employerType && detail.displayName.normalize('NFC') === displayName.normalize('NFC');
}

function createCommandId() {
  return globalThis.crypto.randomUUID();
}

type EmployerRevisionFormProps = {
  detail: RevisionEmployerDetail | null;
  onAuthorityChange?: (state: { owner: 'revision' | null; locked: boolean }) => void;
  onCanonicalReload?: () => void | 'success' | 'not_found' | Promise<void | 'success' | 'not_found'>;
  onRevisionSuccess?: (result: ReviseEmployerResult) => void;
  onReset?: () => void;
  resetSignal?: number;
  workspaceCommandOwner?: 'create' | 'revision' | null;
};

type RevisionFailureKind = 'validation' | 'forbidden';
type RevisionFormErrorKind = 'name' | 'type' | 'no_op';

export function EmployerRevisionForm(props: EmployerRevisionFormProps) {
  const { messages } = useLanguage();
  const typeSelectRef = useRef<HTMLSelectElement>(null);
  const nameInputRef = useRef<HTMLInputElement>(null);
  const successHeadingRef = useRef<HTMLHeadingElement>(null);
  const revisionFailureHeadingRef = useRef<HTMLHeadingElement>(null);
  const unknownHeadingRef = useRef<HTMLHeadingElement>(null);
  const conflictHeadingRef = useRef<HTMLHeadingElement>(null);
  const staleHeadingRef = useRef<HTMLHeadingElement>(null);
  const refreshFailureHeadingRef = useRef<HTMLHeadingElement>(null);
  const notFoundHeadingRef = useRef<HTMLHeadingElement>(null);
  const previousResetSignalRef = useRef(props.resetSignal ?? 0);
  const previousDetailIdentityRef = useRef<string | null>(null);
  const operationGenerationRef = useRef(0);
  const lastAuthorityLockedRef = useRef(false);
  const [isEditing, setIsEditing] = useState(false);
  const [employerType, setEmployerType] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [formErrorKind, setFormErrorKind] = useState<RevisionFormErrorKind | null>(null);
  const [revisionFailure, setRevisionFailure] = useState<RevisionFailureKind | null>(null);
  const [terminalNotFound, setTerminalNotFound] = useState(false);
  const [refreshFailure, setRefreshFailure] = useState(false);
  const [isPending, setIsPending] = useState(false);
  const [unknownAttempt, setUnknownAttempt] = useState<ReviseEmployerInput | null>(null);
  const [conflictAttempt, setConflictAttempt] = useState<ReviseEmployerInput | null>(null);
  const [staleRecoveryRequired, setStaleRecoveryRequired] = useState(false);
  const [isRecoveryPending, setIsRecoveryPending] = useState(false);
  const [successResult, setSuccessResult] = useState<ReviseEmployerResult | null>(null);
  const authorityLocked = isPending || isRecoveryPending || unknownAttempt !== null || conflictAttempt !== null || staleRecoveryRequired;
  const workspaceCommandOwner = props.workspaceCommandOwner ?? null;
  const blockedByWorkspace = workspaceCommandOwner !== null && workspaceCommandOwner !== 'revision';

  useEffect(() => {
    function retireRevisionAuthority() {
      operationGenerationRef.current += 1;
    }

    window.addEventListener('pagehide', retireRevisionAuthority);
    return () => {
      window.removeEventListener('pagehide', retireRevisionAuthority);
      operationGenerationRef.current += 1;
    };
  }, []);

  useEffect(() => {
    if (lastAuthorityLockedRef.current === authorityLocked) {
      return;
    }

    lastAuthorityLockedRef.current = authorityLocked;
    props.onAuthorityChange?.({ owner: authorityLocked ? 'revision' : null, locked: authorityLocked });
  }, [authorityLocked, props.onAuthorityChange]);

  useEffect(() => {
    if (!isPending && unknownAttempt === null) {
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
  }, [isPending, unknownAttempt]);

  useEffect(() => {
    if (successResult !== null) {
      successHeadingRef.current?.focus();
    }
  }, [successResult]);

  useEffect(() => {
    if (revisionFailure !== null) {
      revisionFailureHeadingRef.current?.focus();
    }
  }, [revisionFailure]);

  useEffect(() => {
    if (unknownAttempt !== null) {
      unknownHeadingRef.current?.focus();
    }
  }, [unknownAttempt]);

  useEffect(() => {
    if (conflictAttempt !== null) {
      conflictHeadingRef.current?.focus();
    }
  }, [conflictAttempt]);

  useEffect(() => {
    if (staleRecoveryRequired) {
      staleHeadingRef.current?.focus();
    }
  }, [staleRecoveryRequired]);

  useEffect(() => {
    if (refreshFailure) {
      refreshFailureHeadingRef.current?.focus();
    }
  }, [refreshFailure]);

  useEffect(() => {
    if (terminalNotFound) {
      notFoundHeadingRef.current?.focus();
    }
  }, [terminalNotFound]);

  useEffect(() => {
    const nextResetSignal = props.resetSignal ?? 0;
    if (previousResetSignalRef.current === nextResetSignal) {
      return;
    }

    previousResetSignalRef.current = nextResetSignal;
    operationGenerationRef.current += 1;
    setIsEditing(false);
    setEmployerType('');
    setDisplayName('');
    setFormErrorKind(null);
    setRevisionFailure(null);
    setTerminalNotFound(false);
    setRefreshFailure(false);
    setIsPending(false);
    setUnknownAttempt(null);
    setConflictAttempt(null);
    setStaleRecoveryRequired(false);
    setIsRecoveryPending(false);
    setSuccessResult(null);
    props.onReset?.();
  }, [props, props.resetSignal]);

  const detail = props.detail;
  const detailIdentity = detail === null ? null : `${detail.employerId}:${detail.version}`;

  useEffect(() => {
    if (detailIdentity === null) {
      previousDetailIdentityRef.current = null;
      return;
    }

    if (previousDetailIdentityRef.current === detailIdentity) {
      return;
    }

    previousDetailIdentityRef.current = detailIdentity;
    setTerminalNotFound(false);
    setSuccessResult(null);
  }, [detailIdentity]);

  if (detail === null) {
    return null;
  }

  const selectedDetail = detail;

  function openEditor() {
    if (blockedByWorkspace) {
      return;
    }

    setIsEditing(true);
    setEmployerType(selectedDetail.employerType);
    setDisplayName(selectedDetail.displayName);
    setFormErrorKind(null);
    setRefreshFailure(false);
    setSuccessResult(null);
  }

  function handleTypeChange(event: ChangeEvent<HTMLSelectElement>) {
    if (blockedByWorkspace || conflictAttempt !== null) {
      return;
    }
    setEmployerType(event.target.value);
    setRefreshFailure(false);
    if (revisionFailure !== null) {
      setRevisionFailure(null);
    }
    if (formErrorKind !== null) {
      setFormErrorKind(null);
    }
  }

  function handleNameChange(event: ChangeEvent<HTMLInputElement>) {
    if (blockedByWorkspace || unknownAttempt !== null || conflictAttempt !== null) {
      return;
    }
    setDisplayName(event.target.value);
    setRefreshFailure(false);
    if (revisionFailure !== null) {
      setRevisionFailure(null);
    }
    if (formErrorKind !== null) {
      setFormErrorKind(null);
    }
  }

  async function submitAttempt(attempt: ReviseEmployerInput) {
    setFormErrorKind(null);
    setRevisionFailure(null);
    setRefreshFailure(false);
    setIsPending(true);
    const operationGeneration = operationGenerationRef.current + 1;
    operationGenerationRef.current = operationGeneration;

    try {
      const result = await reviseEmployer(attempt);

      if (operationGeneration !== operationGenerationRef.current) {
        return;
      }

      if (result.ok) {
        setRevisionFailure(null);
        setUnknownAttempt(null);
        setConflictAttempt(null);
        setStaleRecoveryRequired(false);
        setRefreshFailure(false);
        setIsEditing(false);
        if (props.onRevisionSuccess) {
          props.onRevisionSuccess(result.value);
        } else {
          setSuccessResult(result.value);
        }
        return;
      }

      if (result.failure.kind === 'unknown_outcome') {
        setRevisionFailure(null);
        setConflictAttempt(null);
        setStaleRecoveryRequired(false);
        setUnknownAttempt(attempt);
      } else if (result.failure.kind === 'conflict') {
        setRevisionFailure(null);
        setUnknownAttempt(null);
        setStaleRecoveryRequired(false);
        setConflictAttempt(attempt);
      } else if (result.failure.kind === 'stale') {
        setRevisionFailure(null);
        setUnknownAttempt(null);
        setConflictAttempt(null);
        setStaleRecoveryRequired(true);
      } else if (result.failure.kind === 'validation' || result.failure.kind === 'forbidden') {
        setUnknownAttempt(null);
        setConflictAttempt(null);
        setStaleRecoveryRequired(false);
        setRevisionFailure(result.failure.kind);
      } else if (result.failure.kind === 'not_found') {
        setUnknownAttempt(null);
        setConflictAttempt(null);
        setStaleRecoveryRequired(false);
        setRevisionFailure(null);
        setTerminalNotFound(true);
        setEmployerType('');
        setDisplayName('');
        setIsEditing(false);
      }
    } finally {
      if (operationGeneration === operationGenerationRef.current) {
        setIsPending(false);
      }
    }
  }

  async function handleConflictReload() {
    if (blockedByWorkspace || conflictAttempt === null || isPending || isRecoveryPending) {
      return;
    }

    setIsRecoveryPending(true);
    setRefreshFailure(false);

    try {
      await props.onCanonicalReload?.();
      setConflictAttempt(null);
      setIsEditing(false);
    } catch {
      setRefreshFailure(true);
      return;
    } finally {
      setIsRecoveryPending(false);
    }
  }

  async function handleStaleReload() {
    if (blockedByWorkspace || !staleRecoveryRequired || isPending || isRecoveryPending) {
      return;
    }

    setIsRecoveryPending(true);
    setRefreshFailure(false);

    try {
      const reloadResult = await props.onCanonicalReload?.();
      if (reloadResult === 'success' || reloadResult === undefined) {
        setStaleRecoveryRequired(false);
        setIsEditing(false);
      } else if (reloadResult === 'not_found') {
        setStaleRecoveryRequired(false);
        setTerminalNotFound(true);
        setEmployerType('');
        setDisplayName('');
        setIsEditing(false);
      }
    } catch {
      setRefreshFailure(true);
      return;
    } finally {
      setIsRecoveryPending(false);
    }
  }

  async function handleUnknownReload() {
    if (blockedByWorkspace || unknownAttempt === null || isPending || isRecoveryPending) {
      return;
    }

    setIsRecoveryPending(true);
    setRefreshFailure(false);

    try {
      const reloadResult = await props.onCanonicalReload?.();
      if (reloadResult === 'success' || reloadResult === 'not_found' || reloadResult === undefined) {
        setUnknownAttempt(null);
        setIsEditing(false);
      }
    } catch {
      setRefreshFailure(true);
      return;
    } finally {
      setIsRecoveryPending(false);
    }
  }

  async function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();

    if (
      blockedByWorkspace ||
      isPending ||
      isRecoveryPending ||
      unknownAttempt !== null ||
      conflictAttempt !== null ||
      staleRecoveryRequired
    ) {
      return;
    }

    if (employerType !== 'business' && employerType !== 'household') {
      setFormErrorKind('type');
      typeSelectRef.current?.focus();
      return;
    }

    if (!isValidDisplayName(displayName)) {
      setFormErrorKind('name');
      nameInputRef.current?.focus();
      return;
    }

    if (isNormalizedNoOpEdit(selectedDetail, employerType, displayName)) {
      setFormErrorKind('no_op');
      nameInputRef.current?.focus();
      return;
    }

    await submitAttempt({
      employerId: selectedDetail.employerId,
      commandId: createCommandId(),
      expectedVersion: selectedDetail.version,
      employerType,
      displayName,
    });
  }

  if (!isEditing) {
    if (terminalNotFound) {
      return (
        <section aria-live="assertive" className="workspace-panel" role="alert">
          <h3 ref={notFoundHeadingRef} tabIndex={-1}>
            {messages.employerRevisionNotFoundHeading}
          </h3>
          <p>{messages.employerRevisionNotFoundBody}</p>
        </section>
      );
    }

    if (successResult !== null) {
      return (
        <section aria-live="polite" className="workspace-panel" role="status">
          <h3 ref={successHeadingRef} tabIndex={-1}>
            {messages.employerRevisionSuccessHeading}
          </h3>
          <p>{messages.employerRevisionSuccessBody}</p>
        </section>
      );
    }

    return (
      <section aria-label={messages.employerRevisionHeading} className="workspace-panel">
        <button className="focus-ring" disabled={blockedByWorkspace} onClick={openEditor} type="button">
          {messages.employerRevisionEditAction}
        </button>
      </section>
    );
  }

  const hidesSubmittedValues = unknownAttempt !== null || conflictAttempt !== null;
  const formError =
    formErrorKind === 'type'
      ? messages.employerRevisionTypeError
      : formErrorKind === 'name'
        ? messages.employerRevisionNameError
        : formErrorKind === 'no_op'
          ? messages.employerRevisionNoOpError
          : null;

  return (
    <form
      aria-label={messages.employerRevisionHeading}
      className="workspace-panel"
      onSubmit={(event) => {
        void handleSubmit(event);
      }}
    >
      <h3>{messages.employerRevisionHeading}</h3>
      <p>{messages.employerRevisionWarning}</p>
      {formError === null ? null : (
        <section aria-label={messages.employerRevisionHeading} aria-live="assertive" role="alert">
          <p>{formError}</p>
        </section>
      )}
      {revisionFailure === null ? null : (
        <section aria-label={messages.employerRevisionHeading} aria-live="assertive" role="alert">
          <h3 ref={revisionFailureHeadingRef} tabIndex={-1}>
            {revisionFailure === 'validation'
              ? messages.employerRevisionValidationFailureHeading
              : messages.employerRevisionForbiddenFailureHeading}
          </h3>
          <p>
            {revisionFailure === 'validation'
              ? messages.employerRevisionValidationFailureBody
              : messages.employerRevisionForbiddenFailureBody}
          </p>
        </section>
      )}
      {!refreshFailure ? null : (
        <section aria-label={messages.employerRevisionHeading} aria-live="assertive" role="alert">
          <h3 ref={refreshFailureHeadingRef} tabIndex={-1}>
            {messages.employerRevisionRefreshFailureHeading}
          </h3>
          <p>{messages.employerRevisionRefreshFailureBody}</p>
        </section>
      )}
      {hidesSubmittedValues ? null : (
        <>
          <div>
            <label htmlFor="revision-employer-type">{messages.employerRevisionTypeLabel}</label>
            <select
              id="revision-employer-type"
              name="revisionEmployerType"
              className="focus-ring"
              disabled={blockedByWorkspace || isPending || isRecoveryPending || staleRecoveryRequired}
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
            <label htmlFor="revision-employer-name">{messages.employerRevisionNameLabel}</label>
            <input
              id="revision-employer-name"
              name="revisionEmployerName"
              type="text"
              autoCapitalize="none"
              autoComplete="off"
              autoCorrect="off"
              spellCheck={false}
              className="focus-ring"
              disabled={blockedByWorkspace || isPending || isRecoveryPending || staleRecoveryRequired}
              onChange={handleNameChange}
              ref={nameInputRef}
              value={displayName}
            />
          </div>
          <button
            className="focus-ring"
            disabled={blockedByWorkspace || isPending || isRecoveryPending || staleRecoveryRequired}
            type="submit"
          >
            {messages.employerRevisionSubmit}
          </button>
        </>
      )}
      {unknownAttempt === null ? null : (
        <section aria-live="assertive" role="alert">
          <h3 ref={unknownHeadingRef} tabIndex={-1}>
            {messages.employerRevisionUnknownHeading}
          </h3>
          <p>{messages.employerRevisionUnknownBody}</p>
          <button
            className="focus-ring"
            disabled={isPending}
            onClick={() => {
              if (isPending) {
                return;
              }
              void submitAttempt(unknownAttempt);
            }}
            type="button"
          >
            {messages.employerRevisionUnknownRetry}
          </button>
          <button
            className="focus-ring"
            disabled={isPending || isRecoveryPending}
            onClick={() => {
              void handleUnknownReload();
            }}
            type="button"
          >
            {messages.employerRevisionConflictReload}
          </button>
        </section>
      )}
      {conflictAttempt === null ? null : (
        <section aria-live="assertive" role="alert">
          <h3 ref={conflictHeadingRef} tabIndex={-1}>
            {messages.employerRevisionConflictHeading}
          </h3>
          <p>{messages.employerRevisionConflictBody}</p>
          <button
            className="focus-ring"
            disabled={isPending || isRecoveryPending}
            onClick={() => {
              void handleConflictReload();
            }}
            type="button"
          >
            {messages.employerRevisionConflictReload}
          </button>
        </section>
      )}
      {!staleRecoveryRequired ? null : (
        <section aria-live="assertive" role="alert">
          <h3 ref={staleHeadingRef} tabIndex={-1}>
            {messages.employerRevisionStaleHeading}
          </h3>
          <p>{messages.employerRevisionStaleBody}</p>
          <button
            className="focus-ring"
            disabled={isPending || isRecoveryPending}
            onClick={() => {
              void handleStaleReload();
            }}
            type="button"
          >
            {messages.employerRevisionStaleReload}
          </button>
        </section>
      )}
    </form>
  );
}
