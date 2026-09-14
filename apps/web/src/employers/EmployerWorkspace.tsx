import { useCallback, useEffect, useRef, useState } from 'react';

import type { EmployerDetail, RevisionEmployerDetail } from '../api/employerContracts';
import { EmployerCreateForm } from './EmployerCreateForm';
import { EmployerRevisionForm } from './EmployerRevisionForm';
import { EmployerSearch } from './EmployerSearch';
import { useLanguage } from '../i18n/LanguageProvider';

type EmployerWorkspaceProps = {
  onPersistedRestore: () => void;
};

type CurrentSessionEmployer = Pick<EmployerDetail, 'displayName' | 'employerType' | 'lifecycleStatus'>;

type CurrentWorkStatus = 'created' | 'revised' | 'selected';

type CurrentWork = {
  detail: CurrentSessionEmployer;
  status: CurrentWorkStatus;
};

type SessionActivity = {
  action: CurrentWorkStatus;
  displayName: string;
  id: number;
};

function currentWorkStatusMessage(status: CurrentWorkStatus, messages: ReturnType<typeof useLanguage>['messages']) {
  if (status === 'created') {
    return messages.employerCurrentWorkCreatedStatus;
  }

  if (status === 'revised') {
    return messages.employerCurrentWorkRevisedStatus;
  }

  return messages.employerCurrentWorkSelectedStatus;
}

function activityActionMessage(action: CurrentWorkStatus, messages: ReturnType<typeof useLanguage>['messages']) {
  if (action === 'created') {
    return messages.employerSessionActivityCreated;
  }

  if (action === 'revised') {
    return messages.employerSessionActivityRevised;
  }

  return messages.employerSessionActivitySelected;
}

function currentWorkNextStepMessage(status: CurrentWorkStatus, messages: ReturnType<typeof useLanguage>['messages']) {
  if (status === 'created') {
    return messages.employerCurrentWorkCreatedNextStep;
  }

  if (status === 'revised') {
    return messages.employerCurrentWorkRevisedNextStep;
  }

  return messages.employerCurrentWorkSelectedNextStep;
}

function workflowStepState(
  step: 'create' | 'review' | 'search',
  currentWork: CurrentWork | null,
  searchCheckpoint: 'empty' | 'none' | 'results',
) {
  if (step === 'search') {
    return currentWork === null && searchCheckpoint === 'none' ? 'current' : 'complete';
  }

  if (step === 'create') {
    if (currentWork?.status === 'created') {
      return 'complete';
    }

    return currentWork === null && searchCheckpoint === 'empty' ? 'current' : undefined;
  }

  return currentWork === null && searchCheckpoint !== 'results' ? undefined : 'current';
}

export function EmployerWorkspace({ onPersistedRestore }: EmployerWorkspaceProps) {
  const { messages } = useLanguage();
  const [searchResetVersion, setSearchResetVersion] = useState(0);
  const [formResetVersion, setFormResetVersion] = useState(0);
  const [selectedRevisionDetail, setSelectedRevisionDetail] = useState<RevisionEmployerDetail | null>(null);
  const [currentWork, setCurrentWork] = useState<CurrentWork | null>(null);
  const [sessionActivity, setSessionActivity] = useState<SessionActivity[]>([]);
  const [searchCheckpoint, setSearchCheckpoint] = useState<'empty' | 'none' | 'results'>('none');
  const [workspaceCommandOwner, setWorkspaceCommandOwner] = useState<'create' | 'revision' | null>(null);
  const [revisionRefreshRequest, setRevisionRefreshRequest] = useState<{
    employerId: string;
    minimumVersion?: number;
    reason: 'canonical_reload' | 'confirmed_save';
    token: number;
  } | null>(null);
  const pendingCanonicalReloadRef = useRef<{
    reject: (error: Error) => void;
    resolve: (result: 'not_found' | 'success') => void;
    token: number;
  } | null>(null);
  const pendingConfirmedRevisionRefreshRef = useRef(false);

  function handleCreateAuthorityChange(state: { owner: 'create' | null; locked: boolean }) {
    setWorkspaceCommandOwner((currentOwner) => {
      if (state.locked) {
        return 'create';
      }

      return currentOwner === 'create' ? null : currentOwner;
    });
  }

  function handleRevisionAuthorityChange(state: { owner: 'revision' | null; locked: boolean }) {
    setWorkspaceCommandOwner((currentOwner) => {
      if (state.locked) {
        return 'revision';
      }

      return currentOwner === 'revision' ? null : currentOwner;
    });
  }

  const recordCurrentSessionWork = useCallback((action: CurrentWorkStatus, detail: CurrentSessionEmployer) => {
    setCurrentWork({ detail, status: action });
    setSessionActivity((current) => [
      { action, displayName: detail.displayName, id: current.length + 1 },
      ...current,
    ].slice(0, 5));
  }, []);

  const handleSelectedDetailChange = useCallback((detail: RevisionEmployerDetail | null) => {
    setSelectedRevisionDetail(detail);
    if (detail !== null) {
      if (pendingConfirmedRevisionRefreshRef.current) {
        pendingConfirmedRevisionRefreshRef.current = false;
        recordCurrentSessionWork('revised', detail);
        return;
      }

      recordCurrentSessionWork('selected', detail);
    }
  }, [recordCurrentSessionWork]);

  useEffect(() => {
    function handlePageHide() {
      setSearchResetVersion((current) => current + 1);
      setFormResetVersion((current) => current + 1);
      setSelectedRevisionDetail(null);
      setCurrentWork(null);
      setSessionActivity([]);
      setSearchCheckpoint('none');
      setWorkspaceCommandOwner(null);
      setRevisionRefreshRequest(null);
      pendingConfirmedRevisionRefreshRef.current = false;
      pendingCanonicalReloadRef.current?.reject(new Error('pagehide invalidated canonical reload'));
      pendingCanonicalReloadRef.current = null;
    }

    function handlePageShow(event: Event) {
      if ((event as Event & { persisted?: boolean }).persisted === true) {
        onPersistedRestore();
      }
    }

    window.addEventListener('pagehide', handlePageHide);
    window.addEventListener('pageshow', handlePageShow);
    return () => {
      window.removeEventListener('pagehide', handlePageHide);
      window.removeEventListener('pageshow', handlePageShow);
    };
  }, [onPersistedRestore]);

  return (
    <section aria-label={messages.employersWorkspaceLabel} className="workspace-stack" data-layout="employer-workspace" data-motion-safe="true">
      <div className="workspace-hero">
        <h2>{messages.employerWorkspaceTitle}</h2>
        <p>{messages.employerWorkspaceIntro}</p>
      </div>

      <section aria-labelledby="workspace-overview-heading" className="workspace-panel workspace-overview">
        <h3 id="workspace-overview-heading">{messages.employerWorkspaceOverviewHeading}</h3>
        <p>{messages.employerWorkspaceOverviewBody}</p>
      </section>

      <section aria-labelledby="employer-workflow-guide-heading" className="workspace-panel workflow-guide">
        <h3 id="employer-workflow-guide-heading">{messages.employerWorkflowGuideHeading}</h3>
        <ol className="workflow-step-list">
          {[
            {
              body: messages.employerWorkflowGuideSearchBody,
              state: workflowStepState('search', currentWork, searchCheckpoint),
              title: messages.employerWorkflowGuideSearchStep,
            },
            {
              body: messages.employerWorkflowGuideCreateBody,
              state: workflowStepState('create', currentWork, searchCheckpoint),
              title: messages.employerWorkflowGuideCreateStep,
            },
            {
              body: messages.employerWorkflowGuideReviewBody,
              state: workflowStepState('review', currentWork, searchCheckpoint),
              title: messages.employerWorkflowGuideReviewStep,
            },
          ].map((step) => (
            <li className="workflow-step" data-state={step.state} key={step.title}>
              <span aria-hidden="true" className="workflow-step__marker" />
              <div>
                <h4>{step.title}</h4>
                <p>{step.body}</p>
                {step.state === undefined ? null : (
                  <p className="workflow-step__state">
                    {step.state === 'current'
                      ? messages.employerWorkflowCurrentStepLabel
                      : messages.employerWorkflowCompleteStepLabel}
                  </p>
                )}
              </div>
            </li>
          ))}
        </ol>
      </section>

      <div className="workspace-grid">
        <section aria-labelledby="employer-search-heading" className="workspace-panel workspace-panel--search">
          <h3 id="employer-search-heading">{messages.employerSearchHeading}</h3>
          <p>{messages.employerSearchInstructions}</p>
          <EmployerSearch
            detailOutletId="employer-work-area-detail-outlet"
            onSearchCheckpointChange={setSearchCheckpoint}
            onSelectedDetailChange={handleSelectedDetailChange}
            onRefreshRequestSettled={({ outcome, token }) => {
              if (
                pendingConfirmedRevisionRefreshRef.current &&
                revisionRefreshRequest?.reason === 'confirmed_save' &&
                revisionRefreshRequest.token === token &&
                outcome !== 'success'
              ) {
                pendingConfirmedRevisionRefreshRef.current = false;
              }

              const pendingCanonicalReload = pendingCanonicalReloadRef.current;
              if (pendingCanonicalReload === null || pendingCanonicalReload.token !== token) {
                return;
              }

              if (outcome === 'success') {
                pendingCanonicalReload.resolve('success');
              } else if (outcome === 'not_found') {
                pendingCanonicalReload.resolve('not_found');
              } else {
                pendingCanonicalReload.reject(new Error('canonical reload failed'));
              }

              pendingCanonicalReloadRef.current = null;
            }}
            refreshRequest={revisionRefreshRequest}
            resetSignal={searchResetVersion}
            workspaceCommandOwner={workspaceCommandOwner}
          />
        </section>

        <section aria-labelledby="employer-create-heading" className="workspace-panel workspace-panel--create">
          <EmployerCreateForm
            onAuthorityChange={handleCreateAuthorityChange}
            onCreateSuccess={(detail) => {
              setSearchResetVersion((current) => current + 1);
              setSearchCheckpoint('none');
              setSelectedRevisionDetail(null);
              recordCurrentSessionWork('created', detail);
            }}
            resetSignal={formResetVersion}
            searchCheckpoint={searchCheckpoint}
            workspaceCommandOwner={workspaceCommandOwner}
          />
        </section>
      </div>

      <section aria-labelledby="employer-work-area-heading" className="workspace-panel workspace-work-area">
        <h3 id="employer-work-area-heading">{messages.employerWorkAreaHeading}</h3>
        <section aria-labelledby="employer-current-work-heading" className="session-panel session-panel--current">
          <h4 id="employer-current-work-heading">{messages.employerCurrentWorkHeading}</h4>
          {currentWork === null ? (
            <>
              <p>{messages.employerCurrentWorkEmpty}</p>
              <p className="workflow-note">{messages.employerCurrentWorkEmptyNextStep}</p>
            </>
          ) : (
            <dl className="session-summary">
              <div>
                <dt>{messages.employerCurrentWorkNameLabel}</dt>
                <dd>{messages.employerCurrentWorkNameLabel}: {currentWork.detail.displayName}</dd>
              </div>
              <div>
                <dt>{messages.employerDetailTypeLabel}</dt>
                <dd>{currentWork.detail.employerType === 'business' ? messages.employerTypeBusiness : messages.employerTypeHousehold}</dd>
              </div>
              <div>
                <dt>{messages.employerDetailLifecycleLabel}</dt>
                <dd>{messages.employerLifecycleDraft}</dd>
              </div>
              <div>
                <dt>{messages.employerCurrentWorkStatusLabel}</dt>
                <dd>{currentWorkStatusMessage(currentWork.status, messages)}</dd>
              </div>
              <div>
                <dt>{messages.employerCurrentWorkNextStepLabel}</dt>
                <dd>{currentWorkNextStepMessage(currentWork.status, messages)}</dd>
              </div>
            </dl>
          )}
        </section>
        <section aria-labelledby="employer-session-activity-heading" className="session-panel session-panel--activity">
          <h4 id="employer-session-activity-heading">{messages.employerSessionActivityHeading}</h4>
          {sessionActivity.length === 0 ? (
            <p>{messages.employerSessionActivityEmpty}</p>
          ) : (
            <ol className="session-activity-list">
              {sessionActivity.map((activity) => (
                <li key={activity.id}>
                  <span>{activityActionMessage(activity.action, messages)}</span> — {activity.displayName}
                </li>
              ))}
            </ol>
          )}
        </section>
        <div id="employer-work-area-detail-outlet" />
        <EmployerRevisionForm
          detail={selectedRevisionDetail}
          onAuthorityChange={handleRevisionAuthorityChange}
          onCanonicalReload={() => {
          if (selectedRevisionDetail === null) {
            return Promise.resolve('not_found');
          }

          pendingCanonicalReloadRef.current?.reject(new Error('superseded canonical reload'));

          return new Promise<'not_found' | 'success'>((resolve, reject) => {
            setRevisionRefreshRequest((current) => {
              const token = (current?.token ?? 0) + 1;
              pendingCanonicalReloadRef.current = { reject, resolve, token };

              return {
                employerId: selectedRevisionDetail.employerId,
                minimumVersion: undefined,
                reason: 'canonical_reload',
                token,
              };
            });
          });
        }}
        onRevisionSuccess={(result) => {
          setSearchResetVersion((current) => current + 1);
          setFormResetVersion((current) => current + 1);
          setSelectedRevisionDetail(null);
          pendingConfirmedRevisionRefreshRef.current = true;
          setRevisionRefreshRequest((current) => ({
            employerId: result.detail.employerId,
            minimumVersion: Math.max(result.detail.version, result.resultVersion),
            reason: 'confirmed_save',
            token: (current?.token ?? 0) + 1,
          }));
        }}
        resetSignal={formResetVersion}
        workspaceCommandOwner={workspaceCommandOwner}
      />
      </section>
    </section>
  );
}
