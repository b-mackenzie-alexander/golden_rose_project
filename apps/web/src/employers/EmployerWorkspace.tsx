import { useEffect, useState } from 'react';

import { EmployerCreateForm } from './EmployerCreateForm';
import { EmployerSearch } from './EmployerSearch';
import { useLanguage } from '../i18n/LanguageProvider';

type EmployerWorkspaceProps = {
  onPersistedRestore?: () => void;
};

export function EmployerWorkspace({ onPersistedRestore }: EmployerWorkspaceProps) {
  const { messages } = useLanguage();
  const [searchResetVersion, setSearchResetVersion] = useState(0);
  const [formResetVersion, setFormResetVersion] = useState(0);

  useEffect(() => {
    function handlePageHide() {
      setSearchResetVersion((current) => current + 1);
      setFormResetVersion((current) => current + 1);
    }

    function handlePageShow(event: Event) {
      if ((event as Event & { persisted?: boolean }).persisted === true) {
        onPersistedRestore?.();
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
        onCreateSuccess={() => {
          setSearchResetVersion((current) => current + 1);
        }}
        resetSignal={formResetVersion}
      />
      <EmployerSearch resetSignal={searchResetVersion} />
    </section>
  );
}
