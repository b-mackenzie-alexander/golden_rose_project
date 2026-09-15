import { BrowserRouter, Navigate, Route, Routes } from 'react-router';

import { WorkInterestCatalog } from '../intakes/WorkInterests';
import { CanonicalOutput } from '../intakes/CanonicalOutput';
import { IntakeWorkspace } from '../intakes/IntakeWorkspace';
import { AppShell } from './AppShell';
import { NotFoundPage } from './NotFoundPage';
import { reloadCanonicalDocument } from '../browser/privacyLifecycle';
import { EmployerWorkspace } from '../employers/EmployerWorkspace';
import { LanguageProvider } from '../i18n/LanguageProvider';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<Navigate to="/employers" replace />} />
        <Route
          path="employers"
          element={<EmployerWorkspace onPersistedRestore={reloadCanonicalDocument} />}
        />
        <Route path="staff/intakes/workers" element={<IntakeWorkspace key="worker" kind="worker" />} />
        <Route
          path="staff/intakes/employers"
          element={<IntakeWorkspace key="employer" kind="employer" />}
        />
        <Route path="staff/work-interests" element={<WorkInterestCatalog />} />
        <Route path="staff/intakes/:intakeId/outputs/:output" element={<CanonicalOutput />} />
        <Route path="staff/intakes/:intakeId" element={<IntakeWorkspace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <LanguageProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </LanguageProvider>
  );
}
