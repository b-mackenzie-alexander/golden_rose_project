import { Link } from 'react-router';

import { IconSymbol, MissionStatementMark, SkylineArtwork, ZoneMapArtwork } from './artwork';
import type { IconName } from './artwork';
import { useLanguage } from '../i18n/LanguageProvider';

type DashboardCopy = {
  activityHeading: string;
  activityLink: string;
  activityRows: Array<{ icon: IconName; meta: string; title: string }>;
  greeting: string;
  kpis: Array<{ accent: 'danger' | 'info' | 'success' | 'warning'; href: string; icon: IconName; label: string; meta: string; value: string }>;
  primaryQueueHeading: string;
  primaryQueueLink: string;
  queueRows: Array<{ days: string; icon: IconName; name: string; next: string; ref: string; status: 'draft' | 'in_review' | 'incomplete' | 'pending'; type: 'employer' | 'worker' }>;
  quickActions: Array<{ href: string; label: string }>;
  quickHeading: string;
  recentEmployerHeading: string;
  recentWorkerHeading: string;
  recentRows: Array<{ href: string; meta: string; name: string; status: 'complete' | 'draft' | 'in_review' | 'incomplete' | 'pending' }>;
  scheduleHeading: string;
  scheduleLink: string;
  scheduleRows: Array<{ dot: 'danger' | 'info' | 'success' | 'warning'; meta: string; time: string; title: string }>;
  searchPlaceholder: string;
  subtitle: string;
  zoneAreas: Array<{ count: number; intensity: 'high' | 'low' | 'medium' | 'mediumHigh'; label: string; name: 'Bronx' | 'Brooklyn' | 'Manhattan' | 'Queens' | 'Staten Island' }>;
  zonesHeading: string;
  zonesMetric: string;
  zonesMeta: string;
};

const englishDashboard: DashboardCopy = {
  activityHeading: 'Recent activity',
  activityLink: 'View all activity',
  activityRows: [
    { icon: 'worker', meta: '2 hours ago - Carlos Ramirez', title: 'Ana Torres record updated' },
    { icon: 'document', meta: '3 hours ago - Mariela Torres', title: 'Preview worker draft created' },
    { icon: 'building', meta: '5 hours ago - Sofia Diaz', title: 'Clean Homes LLC added' },
  ],
  greeting: 'Good morning, Mariela',
  kpis: [
    { accent: 'danger', href: '/staff/intakes/workers', icon: 'document', label: 'Worker intakes', meta: 'need review', value: '12' },
    { accent: 'success', href: '/employers', icon: 'workers', label: 'Employer follow-ups', meta: 'scheduled today', value: '8' },
    { accent: 'warning', href: '/staff/queues', icon: 'warning', label: 'Urgent requests', meta: 'require response', value: '4' },
    { accent: 'info', href: '/staff/calendar', icon: 'calendar', label: 'Interviews', meta: 'on the calendar', value: '6' },
  ],
  primaryQueueHeading: "Today's priorities",
  primaryQueueLink: 'View all',
  queueRows: [
    { days: '9:00 a.m.', icon: 'worker', name: 'Urgent intake review', next: 'Missing residential address', ref: 'Fictional Q Person', status: 'incomplete', type: 'worker' },
    { days: '10:30 a.m.', icon: 'building', name: 'Employer follow-up', next: 'Confirm contact details', ref: 'Restaurante La Esperanza', status: 'pending', type: 'employer' },
    { days: '11:00 a.m.', icon: 'worker', name: 'Complete pending interview', next: 'Review availability', ref: 'Jason Meme', status: 'pending', type: 'worker' },
    { days: '1:00 p.m.', icon: 'document', name: 'Review new drafts', next: 'Three records waiting', ref: 'Staff queue', status: 'draft', type: 'worker' },
    { days: '3:00 p.m.', icon: 'catalog', name: 'Update interest catalog', next: 'Review new skill labels', ref: 'Catalog', status: 'in_review', type: 'employer' },
  ],
  quickActions: [
    { href: '/staff/intakes/workers', label: 'New worker intake' },
    { href: '/staff/intakes/employers', label: 'New employer intake' },
    { href: '/staff/calendar', label: 'View calendar' },
    { href: '/employers', label: 'Search records' },
  ],
  quickHeading: 'Quick actions',
  recentEmployerHeading: 'Recent employer intakes',
  recentWorkerHeading: 'Recent worker intakes',
  recentRows: [
    { href: '/staff/intakes/workers', meta: '2 days ago', name: 'Maria Lopez', status: 'incomplete' },
    { href: '/staff/intakes/workers', meta: '1 day ago', name: 'Carlos Rojas', status: 'in_review' },
    { href: '/staff/intakes/workers', meta: '2 days ago', name: 'Lucia Torres', status: 'draft' },
  ],
  scheduleHeading: "Today's schedule",
  scheduleLink: 'View calendar',
  scheduleRows: [
    { dot: 'danger', meta: 'Staff meeting', time: '9:00 AM', title: 'Team check-in' },
    { dot: 'warning', meta: 'Employer intake', time: '10:30 AM', title: 'Call Restaurante La Esperanza' },
    { dot: 'success', meta: 'Worker registration', time: '12:00 PM', title: 'Interview with Ana Quispe' },
    { dot: 'info', meta: 'Operations', time: '2:00 PM', title: 'Team meeting' },
    { dot: 'success', meta: 'Verify documents', time: '4:00 PM', title: 'Follow-up with Maria Lopez' },
  ],
  searchPlaceholder: 'Search workers, employers, or intake references...',
  subtitle: "Here's the summary of today in Nuestro Corazón Dorado.",
  zoneAreas: [
    { count: 18, intensity: 'high', label: 'Manhattan', name: 'Manhattan' },
    { count: 14, intensity: 'mediumHigh', label: 'Brooklyn', name: 'Brooklyn' },
    { count: 12, intensity: 'medium', label: 'Bronx', name: 'Bronx' },
    { count: 9, intensity: 'medium', label: 'Queens', name: 'Queens' },
    { count: 3, intensity: 'low', label: 'Staten Island', name: 'Staten Island' },
  ],
  zonesHeading: 'Activity by area',
  zonesMetric: '56',
  zonesMeta: 'People served this week',
};

const spanishDashboard: DashboardCopy = {
  activityHeading: 'Actividad reciente',
  activityLink: 'Ver toda la actividad',
  activityRows: [
    { icon: 'worker', meta: 'hace 2 horas - Carlos Ramirez', title: 'Se actualizo el registro de Ana Torres' },
    { icon: 'document', meta: 'hace 3 horas - Mariela Torres', title: 'Nuevo borrador de trabajador creado' },
    { icon: 'building', meta: 'hace 5 horas - Sofia Diaz', title: 'Se agrego Clean Homes LLC' },
  ],
  greeting: 'Buenos días, Mariela',
  kpis: [
    { accent: 'danger', href: '/staff/intakes/workers', icon: 'document', label: 'Registros pendientes', meta: 'requieren revision', value: '12' },
    { accent: 'success', href: '/employers', icon: 'workers', label: 'Seguimientos hoy', meta: 'contactos programados', value: '8' },
    { accent: 'warning', href: '/staff/queues', icon: 'warning', label: 'Solicitudes urgentes', meta: 'requieren respuesta', value: '4' },
    { accent: 'info', href: '/staff/calendar', icon: 'calendar', label: 'Entrevistas programadas', meta: 'hoy en tu calendario', value: '6' },
  ],
  primaryQueueHeading: 'Prioridades de hoy',
  primaryQueueLink: 'Ver todas',
  queueRows: [
    { days: '9:00 a. m.', icon: 'worker', name: 'Revisar solicitud urgente', next: 'Falta domicilio residencial', ref: 'Fictional Q Person', status: 'incomplete', type: 'worker' },
    { days: '10:30 a. m.', icon: 'building', name: 'Hacer seguimiento con empleador', next: 'Confirmar contacto', ref: 'Restaurante La Esperanza', status: 'pending', type: 'employer' },
    { days: '11:00 a. m.', icon: 'worker', name: 'Completar entrevista pendiente', next: 'Revisar disponibilidad', ref: 'Jason Meme', status: 'pending', type: 'worker' },
    { days: '1:00 p. m.', icon: 'document', name: 'Revisar nuevos borradores', next: 'Tres registros sin revisar', ref: 'Cola del personal', status: 'draft', type: 'worker' },
    { days: '3:00 p. m.', icon: 'catalog', name: 'Actualizar catalogo de intereses', next: 'Revisar nuevas habilidades', ref: 'Catalogo', status: 'in_review', type: 'employer' },
  ],
  quickActions: [
    { href: '/staff/intakes/workers', label: 'Nuevo registro de trabajador' },
    { href: '/staff/intakes/employers', label: 'Nuevo registro de empleador' },
    { href: '/staff/calendar', label: 'Ver calendario' },
    { href: '/employers', label: 'Buscar registros' },
  ],
  quickHeading: 'Acciones rapidas',
  recentEmployerHeading: 'Registros recientes de empleadores',
  recentWorkerHeading: 'Registros recientes de trabajadores',
  recentRows: [
    { href: '/staff/intakes/workers', meta: 'hace 2 dias', name: 'Maria Lopez', status: 'incomplete' },
    { href: '/staff/intakes/workers', meta: 'hace 1 dia', name: 'Carlos Rojas', status: 'in_review' },
    { href: '/staff/intakes/workers', meta: 'hace 2 dias', name: 'Lucia Torres', status: 'draft' },
  ],
  scheduleHeading: 'Agenda de hoy',
  scheduleLink: 'Ver calendario',
  scheduleRows: [
    { dot: 'danger', meta: 'Reunion del equipo', time: '9:00 a. m.', title: 'Revision diaria' },
    { dot: 'warning', meta: 'Seguimiento de empleador', time: '10:30 a. m.', title: 'Llamada con Restaurante La Esperanza' },
    { dot: 'success', meta: 'Registro de trabajador', time: '12:00 p. m.', title: 'Entrevista con Ana Quispe' },
    { dot: 'info', meta: 'Operaciones', time: '2:00 p. m.', title: 'Reunion de equipo' },
    { dot: 'success', meta: 'Verificar documentos', time: '4:00 p. m.', title: 'Seguimiento con Maria Lopez' },
  ],
  searchPlaceholder: 'Buscar trabajadores, empleadores o referencias...',
  subtitle: 'Aquí está el resumen de hoy en Nuestro Corazón Dorado.',
  zoneAreas: [
    { count: 18, intensity: 'high', label: 'Manhattan', name: 'Manhattan' },
    { count: 14, intensity: 'mediumHigh', label: 'Brooklyn', name: 'Brooklyn' },
    { count: 12, intensity: 'medium', label: 'Bronx', name: 'Bronx' },
    { count: 9, intensity: 'medium', label: 'Queens', name: 'Queens' },
    { count: 3, intensity: 'low', label: 'Staten Island', name: 'Staten Island' },
  ],
  zonesHeading: 'Actividad por zonas',
  zonesMetric: '56',
  zonesMeta: 'Personas atendidas esta semana',
};

const statusLabels = {
  complete: { en: 'Complete', es: 'Completo' },
  draft: { en: 'Draft', es: 'Borrador' },
  in_review: { en: 'In review', es: 'En revision' },
  incomplete: { en: 'Incomplete', es: 'Incompleto' },
  pending: { en: 'Pending', es: 'Pendiente' },
};

function statusLabel(status: keyof typeof statusLabels, language: 'en' | 'es') {
  return statusLabels[status][language];
}

function IconMark({ name }: { name: IconName }) {
  return (
    <span aria-hidden="true" className="dashboard-icon">
      <IconSymbol name={name} />
    </span>
  );
}

export function Dashboard() {
  const { language } = useLanguage();
  const copy = language === 'es' ? spanishDashboard : englishDashboard;

  return (
    <section aria-labelledby="dashboard-heading" className="dashboard-page">
      <div className="dashboard-hero">
        <div className="dashboard-hero__copy">
          <h2 id="dashboard-heading">{copy.greeting}<span aria-hidden="true" className="dashboard-hero__wave">👋</span></h2>
          <p>{copy.subtitle}</p>
        </div>
        <div className="dashboard-skyline">
          <SkylineArtwork />
          <span className="dashboard-skyline__statement">
            <MissionStatementMark />
          </span>
        </div>
      </div>

      <label className="dashboard-mobile-search">
        <span className="sr-only">{language === 'es' ? 'Busqueda global' : 'Global search'}</span>
        <input className="focus-ring" placeholder={copy.searchPlaceholder} type="search" />
      </label>

      <div className="dashboard-kpis" aria-label={language === 'es' ? 'Metricas principales' : 'Summary metrics'}>
        {copy.kpis.map((kpi) => (
          <Link className="dashboard-card dashboard-kpi focus-ring" data-accent={kpi.accent} key={kpi.label} to={kpi.href}>
            <IconMark name={kpi.icon} />
            <span className="dashboard-kpi__number">{kpi.value}</span>
            <span className="dashboard-kpi__label">{kpi.label}</span>
            <span className="dashboard-kpi__meta">{kpi.meta}</span>
            <span aria-hidden="true" className="dashboard-card__arrow">&gt;</span>
          </Link>
        ))}
      </div>

      <div className="dashboard-main-grid">
        <section className="dashboard-card dashboard-card--queue" aria-labelledby="priority-heading">
          <div className="dashboard-section-header">
            <h3 id="priority-heading"><IconMark name="queue" /> {copy.primaryQueueHeading}</h3>
            <Link className="dashboard-text-link focus-ring" to="/staff/queues">{copy.primaryQueueLink}</Link>
          </div>
          <div className="dashboard-queue" aria-label={copy.primaryQueueHeading}>
            <div className="dashboard-queue__head">
              <span>{language === 'es' ? 'Tipo' : 'Type'}</span>
              <span>{language === 'es' ? 'Nombre / referencia' : 'Name / reference'}</span>
              <span>{language === 'es' ? 'Estado' : 'Status'}</span>
              <span>{language === 'es' ? 'Siguiente paso' : 'Next step'}</span>
              <span>{language === 'es' ? 'Hora' : 'Time'}</span>
            </div>
            {copy.queueRows.map((row) => (
              <Link className="dashboard-queue__row focus-ring" key={`${row.name}-${row.days}`} to={row.type === 'worker' ? '/staff/intakes/workers' : '/staff/intakes/employers'}>
                <span><IconMark name={row.icon} /></span>
                <span>
                  <strong>{row.name}</strong>
                  <small>{row.ref}</small>
                </span>
                <span><span className="status-chip" data-status={row.status}>{statusLabel(row.status, language)}</span></span>
                <span>{row.next}</span>
                <span>{row.days}</span>
              </Link>
            ))}
          </div>
        </section>

        <section className="dashboard-card dashboard-card--schedule" aria-labelledby="schedule-heading">
          <div className="dashboard-section-header">
            <h3 id="schedule-heading"><IconMark name="calendar" /> {copy.scheduleHeading}</h3>
            <Link className="dashboard-text-link focus-ring" to="/staff/calendar">{copy.scheduleLink}</Link>
          </div>
          <ol className="schedule-list">
            {copy.scheduleRows.map((row) => (
              <li className="schedule-row" data-dot={row.dot} key={`${row.time}-${row.title}`}>
                <time>{row.time}</time>
                <span aria-hidden="true" className="schedule-dot" />
                <div>
                  <strong>{row.title}</strong>
                  <span>{row.meta}</span>
                </div>
              </li>
            ))}
          </ol>
        </section>
      </div>

      <div className="dashboard-bottom-grid">
        <section className="dashboard-card" aria-labelledby="recent-workers-heading">
          <div className="dashboard-section-header">
            <h3 id="recent-workers-heading"><IconMark name="worker" /> {copy.recentWorkerHeading}</h3>
            <Link className="dashboard-text-link focus-ring" to="/staff/intakes/workers">{copy.primaryQueueLink}</Link>
          </div>
          <RecentRows rows={copy.recentRows} language={language} />
        </section>

        <section className="dashboard-card" aria-labelledby="recent-employers-heading">
          <div className="dashboard-section-header">
            <h3 id="recent-employers-heading"><IconMark name="building" /> {copy.recentEmployerHeading}</h3>
            <Link className="dashboard-text-link focus-ring" to="/staff/intakes/employers">{copy.primaryQueueLink}</Link>
          </div>
          <RecentRows
            language={language}
            rows={[
              { href: '/staff/intakes/employers', meta: language === 'es' ? 'hoy' : 'Today', name: 'Sunshine Home Care', status: 'pending' },
              { href: '/staff/intakes/employers', meta: language === 'es' ? 'hace 1 dia' : '1 day ago', name: 'Family First LLC', status: 'incomplete' },
              { href: '/staff/intakes/employers', meta: language === 'es' ? 'hace 2 dias' : '2 days ago', name: 'Caring Hands', status: 'complete' },
            ]}
          />
        </section>

        <section className="dashboard-card dashboard-card--actions" aria-labelledby="quick-actions-heading">
          <h3 id="quick-actions-heading"><IconMark name="check" /> {copy.quickHeading}</h3>
          <div className="quick-action-list">
            {copy.quickActions.map((action, index) => (
              <Link className="quick-action focus-ring" data-primary={index === 0 ? 'true' : undefined} key={action.label} to={action.href}>
                {action.label}
              </Link>
            ))}
          </div>
        </section>
      </div>

      <div className="dashboard-side-grid">
        <section className="dashboard-card dashboard-map-card" aria-labelledby="zones-heading">
          <div>
            <h3 id="zones-heading"><IconMark name="map" /> {copy.zonesHeading}</h3>
            <p><strong>{copy.zonesMetric}</strong> {copy.zonesMeta}</p>
          </div>
          <div aria-hidden="true" className="dashboard-map">
            <ZoneMapArtwork areas={copy.zoneAreas} />
          </div>
        </section>

        <section className="dashboard-card" aria-labelledby="activity-heading">
          <div className="dashboard-section-header">
            <h3 id="activity-heading">{copy.activityHeading}</h3>
            <Link className="dashboard-text-link focus-ring" to="/staff/queues">{copy.activityLink}</Link>
          </div>
          <ol className="activity-list">
            {copy.activityRows.map((row) => (
              <li key={row.title}>
                <IconMark name={row.icon} />
                <div>
                  <strong>{row.title}</strong>
                  <span>{row.meta}</span>
                </div>
              </li>
            ))}
          </ol>
        </section>
      </div>
    </section>
  );
}

function RecentRows({ language, rows }: { language: 'en' | 'es'; rows: DashboardCopy['recentRows'] }) {
  return (
    <ol className="recent-list">
      {rows.map((row) => (
        <li key={`${row.name}-${row.meta}`}>
          <Link className="focus-ring" to={row.href}>
            <span>
              <strong>{row.name}</strong>
              <small>{row.meta}</small>
            </span>
            <span className="status-chip" data-status={row.status}>{statusLabel(row.status, language)}</span>
            <span aria-hidden="true">&gt;</span>
          </Link>
        </li>
      ))}
    </ol>
  );
}
