import { useEffect, useState } from 'react';
import { createBrowserRouter, Link, RouterProvider, Route, Routes } from 'react-router';
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
import { StaffAccountAdmin } from '../staffAccounts/StaffAccountAdmin';
import { StaffAccountProfile } from '../staffAccounts/StaffAccountProfile';
import { LanguageProvider } from '../i18n/LanguageProvider';
import { useLanguage } from '../i18n/LanguageProvider';
import { IconSymbol } from '../dashboard/artwork';
import { getOperationsProjection, type OperationsAreaSummaryItem, type OperationsProjection, type OperationsProjectionFailureKind } from '../api/operationsProjectionClient';
import { getStaticOperationalFallbackPolicy, staticOperationalFallbackNotice, staticOperationalFallbacksAllowed, type StaticOperationalFallbackPolicy } from '../api/runtimeEnvironmentClient';
import { NYCZoneMap } from '../map/NYCZoneMap';
import { aggregateAreaSummary, aggregateSummaryText, emptyOperationsAreaSummary } from '../map/NYCZoneMapData';

type ProjectionStatus = 'loading' | 'ready' | OperationsProjectionFailureKind;

const fallbackAreaSummary: OperationsAreaSummaryItem[] = [
  { areaKey: 'bronx', areaLabel: 'Bronx', pendingReviewCount: 5, requestCount: 6, shiftCount: 6, workerSlots: 12 },
  { areaKey: 'brooklyn', areaLabel: 'Brooklyn', pendingReviewCount: 6, requestCount: 7, shiftCount: 7, workerSlots: 14 },
  { areaKey: 'manhattan', areaLabel: 'Manhattan', pendingReviewCount: 8, requestCount: 8, shiftCount: 8, workerSlots: 18 },
  { areaKey: 'queens', areaLabel: 'Queens', pendingReviewCount: 4, requestCount: 5, shiftCount: 5, workerSlots: 9 },
  { areaKey: 'staten_island', areaLabel: 'Staten Island', pendingReviewCount: 1, requestCount: 2, shiftCount: 2, workerSlots: 3 },
];

function isProjectionFailure(status: ProjectionStatus) {
  return status !== 'loading' && status !== 'ready';
}

function projectionNotice(status: ProjectionStatus, language: 'en' | 'es', fallbackPolicy: StaticOperationalFallbackPolicy) {
  const fallbackNotice = staticOperationalFallbackNotice(fallbackPolicy, language);
  if (!isProjectionFailure(status)) return null;
  const reason = {
    forbidden: {
      en: 'this account is not authorized to read broad operational aggregates',
      es: 'esta cuenta no tiene autorizacion para leer agregados operativos amplios',
    },
    validation: {
      en: 'the aggregate projection response could not be validated',
      es: 'no se pudo validar la respuesta de agregados',
    },
    unavailable: {
      en: 'the aggregate projection service is unavailable',
      es: 'el servicio de agregados no esta disponible',
    },
    unexpected: {
      en: 'the aggregate projection response was unexpected',
      es: 'la respuesta de agregados fue inesperada',
    },
  }[status][language];
  const suffix = fallbackNotice === null
    ? language === 'es'
      ? 'Se muestran datos de respaldo y ninguna direccion exacta.'
      : 'Fallback data is shown and no exact addresses are exposed.'
    : fallbackNotice;
  return language === 'es'
    ? `No se pudieron leer los agregados porque ${reason}. ${suffix}`
    : `Operational aggregates could not be read because ${reason}. ${suffix}`;
}

function areaSummaryFromProjection(projection: OperationsProjection | null, status: ProjectionStatus, fallbackPolicy: StaticOperationalFallbackPolicy): OperationsAreaSummaryItem[] {
  if (projection === null || isProjectionFailure(status) || status === 'loading') {
    return staticOperationalFallbacksAllowed(fallbackPolicy) ? fallbackAreaSummary : emptyOperationsAreaSummary;
  }
  return aggregateAreaSummary(projection.areaSummary);
}

function useOperationsProjection() {
  const [projection, setProjection] = useState<OperationsProjection | null>(null);
  const [status, setStatus] = useState<ProjectionStatus>('loading');
  const [fallbackPolicy, setFallbackPolicy] = useState<StaticOperationalFallbackPolicy>('loading');
  useEffect(() => {
    let cancelled = false;
    void Promise.all([
      getOperationsProjection().catch(() => ({ ok: false as const, failure: { kind: 'unavailable' as const } })),
      getStaticOperationalFallbackPolicy().catch(() => 'deny' as const),
    ])
      .then(([result, policy]) => {
        if (cancelled) return;
        setProjection(result.ok ? result.value : null);
        setStatus(result.ok ? 'ready' : result.failure.kind);
        setFallbackPolicy(policy);
      })
      .catch(() => {
        if (cancelled) return;
        setProjection(null);
        setStatus('unavailable');
        setFallbackPolicy('deny');
      });
    return () => {
      cancelled = true;
    };
  }, []);
  return { fallbackPolicy, projection, status };
}

function StaffMapPreview() {
  const { language } = useLanguage();
  const { fallbackPolicy, projection, status } = useOperationsProjection();
  const areaSummary = areaSummaryFromProjection(projection, status, fallbackPolicy);
  const zoneSummary = projection && status === 'ready' ? projection.zoneSummary ?? [] : [];
  const notice = projectionNotice(status, language, fallbackPolicy);
  const totalWorkerSlots = projection && status === 'ready'
    ? projection.reportSummary.workerSlots
    : areaSummary.reduce((total, area) => total + area.workerSlots, 0);
  const totalLabel = language === 'en' ? 'projected slots awaiting zone assignment' : 'cupos proyectados por asignar';

  return (
    <section className="module-preview-page" aria-labelledby="staff-map-heading">
      <div className="module-preview-hero">
        <p className="module-preview-eyebrow">{language === 'en' ? 'Service zones' : 'Zonas de servicio'}</p>
        <h2 id="staff-map-heading">{language === 'en' ? 'NYC zone map' : 'Mapa de zonas de NYC'}</h2>
        <p>
          {language === 'en'
            ? 'A real NYC basemap with named pilot zones for staff planning. Exact household and worksite locations remain restricted.'
            : 'Un mapa base real de NYC con zonas piloto nombradas para planificacion del personal. Las direcciones exactas siguen restringidas.'}
        </p>
        <div className="module-preview-actions">
          <Link className="staff-secondary-button focus-ring" to="/">
            {language === 'en' ? 'Back to dashboard' : 'Volver al panel'}
          </Link>
        </div>
      </div>
      {notice ? <p className="projection-status-notice" role="status">{notice}</p> : null}
      <div className="module-preview-grid">
        <section className="module-preview-panel module-preview-map" aria-label={language === 'en' ? 'NYC activity by area' : 'Actividad por zona de NYC'}>
          <NYCZoneMap areaSummary={areaSummary} language={language} zoneSummary={zoneSummary} />
        </section>
        <section className="module-preview-panel" aria-labelledby="service-zone-heading">
          <h3 id="service-zone-heading">{language === 'en' ? 'Pilot zone snapshot' : 'Resumen de zonas piloto'}</h3>
          <p className="module-preview-total"><strong>{totalWorkerSlots}</strong> {totalLabel}</p>
          <p className="module-preview-helper">
            {zoneSummary.length > 0
              ? language === 'en'
                ? 'Zone counts use coarse locality and postal-code assignment, including saved unfinalized intake addresses as planning signals. Exact addresses stay hidden.'
                : 'Los conteos por zona usan localidad y codigo postal de forma general e incluyen direcciones guardadas de registros sin finalizar como senales de planificacion. Las direcciones exactas permanecen ocultas.'
              : language === 'en'
                ? 'Current demand is still stored by borough while the zone projection loads.'
                : 'La demanda actual todavia se muestra por condado mientras carga la proyeccion por zona.'}
          </p>
          <ol className="module-metric-list">
            {areaSummary.map((area) => (
              <li key={area.areaKey}>
                <span>{area.areaLabel}</span>
                <strong>{aggregateSummaryText(area, language)}</strong>
              </li>
            ))}
          </ol>
        </section>
      </div>
      <section className="module-preview-panel" aria-labelledby="privacy-boundary-heading">
        <h3 id="privacy-boundary-heading">{language === 'en' ? 'Privacy boundary' : 'Limite de privacidad'}</h3>
        <p>{language === 'en'
          ? 'This view intentionally uses aggregate zone counts only, including intake-stage planning signals before finalization. It does not drop pins for individual workers, households, employers, or worksites, and address reveals remain permission-gated inside intake workflows.'
          : 'Esta vista usa solo conteos agregados por zona, incluidas senales de planificacion de registros antes de finalizar. No coloca puntos de trabajadores, hogares, empleadores ni lugares de trabajo individuales, y las direcciones siguen protegidas por permisos dentro de los registros.'}</p>
      </section>
    </section>
  );
}

function StaffReportsPreview() {
  const { language } = useLanguage();
  const { fallbackPolicy, projection, status } = useOperationsProjection();
  const notice = projectionNotice(status, language, fallbackPolicy);
  const summary = projection && status === 'ready' ? projection.reportSummary : null;
  const metrics = summary
    ? language === 'en'
      ? [
          ['Requests in projection', String(summary.requestCount), `${String(summary.pendingReviewCount)} pending review`],
          ['Projected shifts', String(summary.shiftCount), `${String(summary.workerSlots)} worker slots`],
          ['Active service areas', String(summary.activeAreaCount), `${String(summary.unmappedRequestCount)} unmapped requests`],
          ['Export status', '0', 'Export remains disabled'],
        ]
      : [
          ['Solicitudes proyectadas', String(summary.requestCount), `${String(summary.pendingReviewCount)} en revision`],
          ['Turnos proyectados', String(summary.shiftCount), `${String(summary.workerSlots)} cupos`],
          ['Zonas activas', String(summary.activeAreaCount), `${String(summary.unmappedRequestCount)} solicitudes sin zona`],
          ['Estado de exportacion', '0', 'La exportacion sigue deshabilitada'],
        ]
    : staticOperationalFallbacksAllowed(fallbackPolicy) ? language === 'en'
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
      ]
    : language === 'en'
    ? [
        ['Requests in projection', '0', 'Projection unavailable'],
        ['Projected shifts', '0', 'Projection unavailable'],
        ['Active service areas', '0', 'Projection unavailable'],
        ['Export status', '0', 'Export remains disabled'],
      ]
    : [
        ['Solicitudes proyectadas', '0', 'Proyeccion no disponible'],
        ['Turnos proyectados', '0', 'Proyeccion no disponible'],
        ['Zonas activas', '0', 'Proyeccion no disponible'],
        ['Estado de exportacion', '0', 'La exportacion sigue deshabilitada'],
      ];

  return (
    <section className="module-preview-page" aria-labelledby="staff-reports-heading">
      <div className="module-preview-hero">
        <p className="module-preview-eyebrow">{language === 'en' ? 'Operational snapshot' : 'Resumen operativo'}</p>
        <h2 id="staff-reports-heading">{language === 'en' ? 'Reports' : 'Informes'}</h2>
        <p>{language === 'en'
          ? 'Staff metrics that summarize intake, follow-up, calendar, and queue activity.'
          : 'Metricas del personal para registros, seguimientos, calendario y colas.'}</p>
      </div>
      {notice ? <p className="projection-status-notice" role="status">{notice}</p> : null}
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
          ? 'These metrics summarize the current staff workflow surface. Export and authoritative reporting should be wired to backend records before shared use.'
          : 'Estas metricas resumen la superficie operativa actual. La exportacion y los informes oficiales deben conectarse a registros del servidor antes de uso compartido.'}</p>
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
        <Route path="staff/account" element={<StaffAccountProfile />} />
        <Route path="staff/admin/accounts" element={<StaffAccountAdmin />} />
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
