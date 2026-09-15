import { useEffect, useState } from 'react';
import { createBrowserRouter, RouterProvider, Navigate, Route, Routes } from 'react-router';
import { NavigationGuard } from './NavigationGuard';
import { routerWindow } from '../browser/routerWindow';

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
  const [router] = useState(() => {
    const instance = createBrowserRouter([{ path: '*', element: <NavigationGuard><AppRoutes /></NavigationGuard> }], { window: routerWindow() });
    instance.dispose();
    return instance;
  });
  useEffect(() => {
    router.initialize();
    return () => { router.dispose(); };
  }, [router]);
  return (
    <LanguageProvider>
      <RouterProvider router={router} />
    </LanguageProvider>
  );
}
