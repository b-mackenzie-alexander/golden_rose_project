import { useEffect, useState } from 'react';
import { createBrowserRouter, RouterProvider, Route, Routes } from 'react-router';
import { NavigationGuard } from './NavigationGuard';
import { routerWindow } from '../browser/routerWindow';

import { WorkInterestCatalog } from '../intakes/WorkInterests';
import { CanonicalOutput } from '../intakes/CanonicalOutput';
import { IntakeWorkspace } from '../intakes/IntakeWorkspace';
import { AppShell } from './AppShell';
import { Dashboard } from '../dashboard/Dashboard';
import { StaffCalendar } from '../calendar/StaffCalendar';
import { WorkQueues } from '../queues/WorkQueues';
import { NotFoundPage } from './NotFoundPage';
import { reloadCanonicalDocument } from '../browser/privacyLifecycle';
import { EmployerWorkspace } from '../employers/EmployerWorkspace';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { useLanguage } from '../i18n/LanguageProvider';
import { IconSymbol, ZoneMapArtwork } from '../dashboard/artwork';

function StaffMapPreview() {
  const { language } = useLanguage();
  const areas = [
    { count: 18, intensity: 'high' as const, label: 'Manhattan', name: 'Manhattan' as const },
    { count: 14, intensity: 'mediumHigh' as const, label: 'Brooklyn', name: 'Brooklyn' as const },
    { count: 12, intensity: 'medium' as const, label: 'Bronx', name: 'Bronx' as const },
    { count: 9, intensity: 'medium' as const, label: 'Queens', name: 'Queens' as const },
    { count: 3, intensity: 'low' as const, label: 'Staten Island', name: 'Staten Island' as const },
  ];

  return (
    <section className="module-preview-page" aria-labelledby="staff-map-heading">
      <div className="module-preview-hero">
        <p className="module-preview-eyebrow">{language === 'en' ? 'Service zones' : 'Zonas de servicio'}</p>
        <h2 id="staff-map-heading">{language === 'en' ? 'Activity map' : 'Mapa de actividad'}</h2>
        <p>
          {language === 'en'
            ? 'Broad-area activity for demo planning. Exact household and worksite locations remain restricted.'
            : 'Actividad por zona amplia para planificacion de demo. Las direcciones exactas siguen restringidas.'}
        </p>
      </div>
      <div className="module-preview-grid">
        <section className="module-preview-panel module-preview-map" aria-label={language === 'en' ? 'NYC activity by area' : 'Actividad por zona de NYC'}>
          <ZoneMapArtwork areas={areas} />
        </section>
        <section className="module-preview-panel" aria-labelledby="service-zone-heading">
          <h3 id="service-zone-heading">{language === 'en' ? 'Zone snapshot' : 'Resumen de zonas'}</h3>
          <ol className="module-metric-list">
            {areas.map((area) => (
              <li key={area.name}>
                <span>{area.label}</span>
                <strong>{area.count}</strong>
              </li>
            ))}
          </ol>
        </section>
      </div>
      <section className="module-preview-panel" aria-labelledby="privacy-boundary-heading">
        <h3 id="privacy-boundary-heading">{language === 'en' ? 'Privacy boundary' : 'Limite de privacidad'}</h3>
        <p>{language === 'en'
          ? 'This view intentionally stays at borough/service-zone level. Individual worker residence and worksite address reveals remain permission-gated inside intake workflows.'
          : 'Esta vista se mantiene a nivel de zona amplia. Los domicilios de trabajadores y direcciones de trabajo siguen protegidos por permisos dentro de los registros.'}</p>
      </section>
    </section>
  );
}

function StaffReportsPreview() {
  const { language } = useLanguage();
  const metrics = language === 'en'
    ? [
        ['Worker drafts reviewed', '12', '4 urgent'],
        ['Employer follow-ups', '8', '3 due today'],
        ['Open queue items', '5', '1 high priority'],
        ['New calendar items', '2', 'Local planner'],
      ]
    : [
        ['Borradores revisados', '12', '4 urgentes'],
        ['Seguimientos', '8', '3 vencen hoy'],
        ['Elementos abiertos', '5', '1 alta prioridad'],
        ['Eventos nuevos', '2', 'Planificador local'],
      ];

  return (
    <section className="module-preview-page" aria-labelledby="staff-reports-heading">
      <div className="module-preview-hero">
        <p className="module-preview-eyebrow">{language === 'en' ? 'Operational snapshot' : 'Resumen operativo'}</p>
        <h2 id="staff-reports-heading">{language === 'en' ? 'Reports' : 'Informes'}</h2>
        <p>{language === 'en'
          ? 'Demo-ready staff metrics that summarize intake, follow-up, calendar, and queue activity.'
          : 'Metricas de demo para registros, seguimientos, calendario y colas.'}</p>
      </div>
      <div className="module-report-grid">
        {metrics.map(([label, value, meta]) => (
          <section className="module-report-card" key={label}>
            <span aria-hidden="true" className="dashboard-icon"><IconSymbol name="reports" /></span>
            <strong>{value}</strong>
            <span>{label}</span>
            <small>{meta}</small>
          </section>
        ))}
      </div>
      <section className="module-preview-panel" aria-labelledby="report-boundary-heading">
        <h3 id="report-boundary-heading">{language === 'en' ? 'Reporting boundary' : 'Limite de informes'}</h3>
        <p>{language === 'en'
          ? 'These metrics are a static operational preview for the demo. Export and authoritative reporting should be wired to backend records before shared use.'
          : 'Estas metricas son una vista previa estatica para la demo. La exportacion y los informes oficiales deben conectarse a registros del servidor antes de uso compartido.'}</p>
        <button className="module-disabled-action focus-ring" disabled type="button">
          {language === 'en' ? 'Export requires report permission' : 'Exportar requiere permiso de informes'}
        </button>
      </section>
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
        <Route path="staff/calendar" element={<StaffCalendar />} />
        <Route path="staff/queues" element={<WorkQueues />} />
        <Route path="staff/map" element={<StaffMapPreview />} />
        <Route path="staff/reports" element={<StaffReportsPreview />} />
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
