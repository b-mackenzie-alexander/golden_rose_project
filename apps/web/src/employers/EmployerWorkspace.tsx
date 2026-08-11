import { useEffect, useRef, useState } from 'react';

import type { RevisionEmployerDetail } from '../api/employerContracts';
import { EmployerCreateForm } from './EmployerCreateForm';
import { EmployerRevisionForm } from './EmployerRevisionForm';
import { EmployerSearch } from './EmployerSearch';
import { useLanguage } from '../i18n/LanguageProvider';

type EmployerWorkspaceProps = {
  onPersistedRestore: () => void;
};

export function EmployerWorkspace({ onPersistedRestore }: EmployerWorkspaceProps) {
  const { messages } = useLanguage();
  const [searchResetVersion, setSearchResetVersion] = useState(0);
  const [formResetVersion, setFormResetVersion] = useState(0);
  const [selectedRevisionDetail, setSelectedRevisionDetail] = useState<RevisionEmployerDetail | null>(null);
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

  useEffect(() => {
    function handlePageHide() {
      setSearchResetVersion((current) => current + 1);
      setFormResetVersion((current) => current + 1);
      setSelectedRevisionDetail(null);
      setWorkspaceCommandOwner(null);
      setRevisionRefreshRequest(null);
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
    <section aria-label={messages.employersWorkspaceLabel} className="workspace-stack" data-motion-safe="true">
      <h2>{messages.employerSearchHeading}</h2>
      <p>{messages.employerSearchInstructions}</p>
      <EmployerCreateForm
        onAuthorityChange={handleCreateAuthorityChange}
        onCreateSuccess={() => {
          setSearchResetVersion((current) => current + 1);
          setSelectedRevisionDetail(null);
        }}
        resetSignal={formResetVersion}
        workspaceCommandOwner={workspaceCommandOwner}
      />
      <EmployerSearch
        onSelectedDetailChange={setSelectedRevisionDetail}
        onRefreshRequestSettled={({ outcome, token }) => {
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
  );
}
