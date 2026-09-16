import { useEffect, useState } from 'react';
import { createBrowserRouter, RouterProvider, Route, Routes } from 'react-router';
import { NavigationGuard } from './NavigationGuard';
import { routerWindow } from '../browser/routerWindow';

import { WorkInterestCatalog } from '../intakes/WorkInterests';
import { CanonicalOutput } from '../intakes/CanonicalOutput';
import { IntakeWorkspace } from '../intakes/IntakeWorkspace';
import { AppShell } from './AppShell';
import { Dashboard } from '../dashboard/Dashboard';
import { NotFoundPage } from './NotFoundPage';
import { reloadCanonicalDocument } from '../browser/privacyLifecycle';
import { EmployerWorkspace } from '../employers/EmployerWorkspace';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { useLanguage } from '../i18n/LanguageProvider';

function StaffModulePlaceholder({ module }: { module: 'calendar' | 'map' | 'queues' | 'reports' }) {
  const { language } = useLanguage();
  const moduleNames = {
    calendar: language === 'en' ? 'Calendar' : 'Calendario',
    map: language === 'en' ? 'Map' : 'Mapa',
    queues: language === 'en' ? 'Work queues' : 'Colas de trabajo',
    reports: language === 'en' ? 'Reports' : 'Informes',
  };

  return (
    <section className="module-placeholder" aria-labelledby={`${module}-placeholder-heading`}>
      <p className="module-placeholder__eyebrow">{language === 'en' ? 'Dashboard module' : 'Modulo del panel'}</p>
      <h2 id={`${module}-placeholder-heading`}>{moduleNames[module]}</h2>
      <p>
        {language === 'en'
          ? 'This staff workspace route is now reserved in navigation and can be connected to its workflow data in a later implementation pass.'
          : 'Esta ruta del espacio de trabajo ya esta reservada en la navegacion y puede conectarse a sus datos en una implementacion posterior.'}
      </p>
    </section>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AppShell />}>
        <Route index element={<Dashboard />} />
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
        <Route path="staff/calendar" element={<StaffModulePlaceholder module="calendar" />} />
        <Route path="staff/queues" element={<StaffModulePlaceholder module="queues" />} />
        <Route path="staff/map" element={<StaffModulePlaceholder module="map" />} />
        <Route path="staff/reports" element={<StaffModulePlaceholder module="reports" />} />
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
