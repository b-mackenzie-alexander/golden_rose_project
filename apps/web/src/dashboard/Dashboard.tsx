import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router';

import { IconSymbol, MissionStatementMark, SkylineArtwork, ZoneMapArtwork } from './artwork';
import type { IconName } from './artwork';
import { queryIntakes } from '../api/intakeClient';
import type { IntakeKind, IntakeSummary } from '../api/intakeContracts';
import { getOperationsProjection, type OperationsProjection, type OperationsProjectionFailureKind, type OperationsRequestItem, type OperationsShiftItem } from '../api/operationsProjectionClient';
import { useLanguage } from '../i18n/LanguageProvider';

type DashboardStatus = 'complete' | 'draft' | 'in_review' | 'incomplete' | 'pending';
type ProjectionStatus = 'loading' | 'ready' | OperationsProjectionFailureKind;
type DashboardIntakes = {
  employers: IntakeSummary[];
  loaded: boolean;
  operations: OperationsProjection | null;
  operationsStatus: ProjectionStatus;
  workers: IntakeSummary[];
};

type DashboardCopy = {
  activityHeading: string;
  activityLink: string;
  activityRows: Array<{ icon: IconName; meta: string; title: string }>;
  emptyQueue: string;
  emptySchedule: string;
  greeting: string;
  kpis: Array<{ accent: 'danger' | 'info' | 'success' | 'warning'; href: string; icon: IconName; label: string; meta: string; value: string }>;
  primaryQueueHeading: string;
  primaryQueueLink: string;
  queueRows: Array<{ days: string; href: string; icon: IconName; name: string; next: string; ref: string; status: Exclude<DashboardStatus, 'complete'> }>;
  quickActions: Array<{ href: string; label: string }>;
  quickHeading: string;
  recentEmployerHeading: string;
  recentWorkerHeading: string;
  recentRows: Array<{ href: string; meta: string; name: string; status: DashboardStatus }>;
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
  emptyQueue: 'No request, shift, or intake work is waiting in the projection.',
  emptySchedule: 'No projected shifts are scheduled for this view.',
  greeting: 'Good morning, Mariela',
  kpis: [
    { accent: 'danger', href: '/staff/intakes/workers?queue=review', icon: 'document', label: 'Worker intakes', meta: 'need review', value: '12' },
    { accent: 'success', href: '/employers', icon: 'workers', label: 'Employer follow-ups', meta: 'scheduled today', value: '8' },
    { accent: 'warning', href: '/staff/queues', icon: 'warning', label: 'Urgent requests', meta: 'require response', value: '4' },
    { accent: 'info', href: '/staff/calendar', icon: 'calendar', label: 'Interviews', meta: 'on the calendar', value: '6' },
  ],
  primaryQueueHeading: "Today's priorities",
  primaryQueueLink: 'View all',
  queueRows: [
    { days: '9:00 a.m.', href: '/staff/intakes/workers?reference=b7dea69e-9b10-43b3-95aa-d1cd01f6c453&open=match', icon: 'worker', name: 'Urgent intake review', next: 'Missing residential address', ref: 'Ana Quispe', status: 'incomplete' },
    { days: '10:30 a.m.', href: '/staff/intakes/employers?reference=40bd8f48-88c2-42bf-a2bb-bd4ee6e962e2&open=match', icon: 'building', name: 'Employer follow-up', next: 'Confirm worksite details', ref: 'Restaurante La Esperanza', status: 'pending' },
    { days: '11:00 a.m.', href: '/staff/intakes/workers?reference=ca0a3935-e72f-4a00-be6d-af081546a73f&open=match', icon: 'worker', name: 'Complete pending interview', next: 'Review availability', ref: 'Carlos Mendoza', status: 'pending' },
    { days: '1:00 p.m.', href: '/staff/intakes/workers?queue=review', icon: 'document', name: 'Review new drafts', next: 'Three records waiting', ref: 'Staff queue', status: 'draft' },
    { days: '3:00 p.m.', href: '/staff/work-interests', icon: 'catalog', name: 'Update interest catalog', next: 'Review new skill labels', ref: 'Catalog', status: 'in_review' },
  ],
  quickActions: [
    { href: '/staff/intakes/workers', label: 'New worker intake' },
    { href: '/staff/intakes/employers', label: 'New employer intake' },
    { href: '/staff/admin/accounts', label: 'Manage staff accounts' },
    { href: '/staff/calendar', label: 'View calendar' },
    { href: '/employers', label: 'Search records' },
  ],
  quickHeading: 'Quick actions',
  recentEmployerHeading: 'Recent employer intakes',
  recentWorkerHeading: 'Recent worker intakes',
  recentRows: [
    { href: '/staff/intakes/workers?reference=499342a9-30ee-41eb-a5fe-22855025d8a9&open=match', meta: '2 days ago', name: 'Maria Lopez', status: 'complete' },
    { href: '/staff/intakes/workers?reference=849ae3a9-acde-44f8-b49b-acb3e58a1f7d&open=match', meta: 'Today', name: 'Sofia Diaz', status: 'complete' },
    { href: '/staff/intakes/workers?reference=b7dea69e-9b10-43b3-95aa-d1cd01f6c453&open=match', meta: '2 days ago', name: 'Ana Quispe', status: 'incomplete' },
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
  emptyQueue: 'No hay solicitudes, turnos ni registros pendientes en la proyeccion.',
  emptySchedule: 'No hay turnos proyectados para esta vista.',
  greeting: 'Buenos días, Mariela',
  kpis: [
    { accent: 'danger', href: '/staff/intakes/workers?queue=review', icon: 'document', label: 'Registros pendientes', meta: 'requieren revision', value: '12' },
    { accent: 'success', href: '/employers', icon: 'workers', label: 'Seguimientos hoy', meta: 'contactos programados', value: '8' },
    { accent: 'warning', href: '/staff/queues', icon: 'warning', label: 'Solicitudes urgentes', meta: 'requieren respuesta', value: '4' },
    { accent: 'info', href: '/staff/calendar', icon: 'calendar', label: 'Entrevistas programadas', meta: 'hoy en tu calendario', value: '6' },
  ],
  primaryQueueHeading: 'Prioridades de hoy',
  primaryQueueLink: 'Ver todas',
  queueRows: [
    { days: '9:00 a. m.', href: '/staff/intakes/workers?reference=b7dea69e-9b10-43b3-95aa-d1cd01f6c453&open=match', icon: 'worker', name: 'Revisar solicitud urgente', next: 'Falta domicilio residencial', ref: 'Ana Quispe', status: 'incomplete' },
    { days: '10:30 a. m.', href: '/staff/intakes/employers?reference=40bd8f48-88c2-42bf-a2bb-bd4ee6e962e2&open=match', icon: 'building', name: 'Hacer seguimiento con empleador', next: 'Confirmar lugar de trabajo', ref: 'Restaurante La Esperanza', status: 'pending' },
    { days: '11:00 a. m.', href: '/staff/intakes/workers?reference=ca0a3935-e72f-4a00-be6d-af081546a73f&open=match', icon: 'worker', name: 'Completar entrevista pendiente', next: 'Revisar disponibilidad', ref: 'Carlos Mendoza', status: 'pending' },
    { days: '1:00 p. m.', href: '/staff/intakes/workers?queue=review', icon: 'document', name: 'Revisar nuevos borradores', next: 'Tres registros sin revisar', ref: 'Cola del personal', status: 'draft' },
    { days: '3:00 p. m.', href: '/staff/work-interests', icon: 'catalog', name: 'Actualizar catalogo de intereses', next: 'Revisar nuevas habilidades', ref: 'Catalogo', status: 'in_review' },
  ],
  quickActions: [
    { href: '/staff/intakes/workers', label: 'Nuevo registro de trabajador' },
    { href: '/staff/intakes/employers', label: 'Nuevo registro de empleador' },
    { href: '/staff/admin/accounts', label: 'Administrar cuentas' },
    { href: '/staff/calendar', label: 'Ver calendario' },
    { href: '/employers', label: 'Buscar registros' },
  ],
  quickHeading: 'Acciones rapidas',
  recentEmployerHeading: 'Registros recientes de empleadores',
  recentWorkerHeading: 'Registros recientes de trabajadores',
  recentRows: [
    { href: '/staff/intakes/workers?reference=499342a9-30ee-41eb-a5fe-22855025d8a9&open=match', meta: 'hace 2 dias', name: 'Maria Lopez', status: 'complete' },
    { href: '/staff/intakes/workers?reference=849ae3a9-acde-44f8-b49b-acb3e58a1f7d&open=match', meta: 'hoy', name: 'Sofia Diaz', status: 'complete' },
    { href: '/staff/intakes/workers?reference=b7dea69e-9b10-43b3-95aa-d1cd01f6c453&open=match', meta: 'hace 2 dias', name: 'Ana Quispe', status: 'incomplete' },
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

function intakeHref(kind: IntakeKind, item: IntakeSummary) {
  return `/staff/intakes/${kind === 'worker' ? 'workers' : 'employers'}?reference=${item.intake_id}&open=match`;
}

function displayName(item: IntakeSummary, language: 'en' | 'es') {
  return item.display_name?.trim() || (language === 'es' ? 'Registro sin nombre' : 'Unnamed intake');
}

function summaryStatus(item: IntakeSummary): DashboardStatus {
  if (item.complete === false) return 'incomplete';
  if (item.follow_up || item.review_status === 'needs_follow_up') return 'pending';
  if (item.review_status === 'stale') return 'in_review';
  if (item.review_status === 'current' && item.complete) return 'complete';
  return item.complete ? 'complete' : 'draft';
}

function queueStatus(item: IntakeSummary): Exclude<DashboardStatus, 'complete'> {
  const status = summaryStatus(item);
  return status === 'complete' ? 'draft' : status;
}

function missingLabel(field: string, language: 'en' | 'es') {
  const labels: Record<string, { en: string; es: string }> = {
    availability: { en: 'availability', es: 'disponibilidad' },
    duties_summary: { en: 'duties', es: 'responsabilidades' },
    offer: { en: 'offer', es: 'oferta' },
    party_address: { en: 'contact address', es: 'direccion de contacto' },
    phone: { en: 'phone', es: 'telefono' },
    representative_name: { en: 'representative name', es: 'nombre del representante' },
    role_title: { en: 'role title', es: 'cargo' },
    schedule: { en: 'requested schedule', es: 'horario solicitado' },
    worker_count: { en: 'number of workers', es: 'numero de trabajadores' },
    worker_residence: { en: 'residential address', es: 'domicilio residencial' },
    worksite_address: { en: 'worksite address', es: 'direccion del lugar de trabajo' },
  };
  return labels[field]?.[language] ?? field.replace(/_/g, ' ');
}

function nextStep(item: IntakeSummary, language: 'en' | 'es') {
  const firstMissingField = item.missing_fields[0];
  if (firstMissingField) {
    const firstMissing = missingLabel(firstMissingField, language);
    return language === 'es' ? `Falta ${firstMissing}` : `Missing ${firstMissing}`;
  }
  if (item.review_status !== 'current') {
    return language === 'es' ? 'Revisar borrador' : 'Review draft';
  }
  return language === 'es' ? 'Abrir registro' : 'Open intake';
}

function relativeDate(value: string, language: 'en' | 'es') {
  const updated = new Date(value);
  if (Number.isNaN(updated.getTime())) return language === 'es' ? 'Actualizado recientemente' : 'Updated recently';
  const now = new Date();
  const elapsedDays = Math.max(0, Math.floor((now.getTime() - updated.getTime()) / 86_400_000));
  if (elapsedDays === 0) return language === 'es' ? 'hoy' : 'Today';
  if (elapsedDays === 1) return language === 'es' ? 'hace 1 dia' : '1 day ago';
  return language === 'es' ? `hace ${String(elapsedDays)} dias` : `${String(elapsedDays)} days ago`;
}

function isProjectionFailure(status: ProjectionStatus) {
  return status !== 'loading' && status !== 'ready';
}

function projectionNotice(status: ProjectionStatus, language: 'en' | 'es') {
  if (!isProjectionFailure(status)) return null;
  const reason = {
    forbidden: {
      en: 'this account is not authorized to read the projection',
      es: 'esta cuenta no tiene autorizacion para leer la proyeccion',
    },
    validation: {
      en: 'the projection response could not be validated',
      es: 'no se pudo validar la respuesta de la proyeccion',
    },
    unavailable: {
      en: 'the projection service is unavailable',
      es: 'el servicio de proyeccion no esta disponible',
    },
    unexpected: {
      en: 'the projection response was unexpected',
      es: 'la respuesta de la proyeccion fue inesperada',
    },
  }[status][language];
  return language === 'es'
    ? `No se pudieron leer las solicitudes y turnos porque ${reason}. Se muestran registros guardados y datos de respaldo cuando no hay una lectura autoritativa.`
    : `Requests and shifts could not be read because ${reason}. Saved intakes and fallback data are shown where an authoritative read is unavailable.`;
}

function recentRows(
  kind: IntakeKind,
  items: IntakeSummary[],
  language: 'en' | 'es',
  fallback: DashboardCopy['recentRows'],
): DashboardCopy['recentRows'] {
  if (items.length === 0) return fallback;
  return [...items]
    .sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at))
    .slice(0, 3)
    .map((item) => ({
      href: intakeHref(kind, item),
      meta: relativeDate(item.updated_at, language),
      name: displayName(item, language),
      status: summaryStatus(item),
    }));
}

function dynamicKpis(copy: DashboardCopy, data: DashboardIntakes, language: 'en' | 'es'): DashboardCopy['kpis'] {
  if (!data.loaded) return copy.kpis;
  const workerReviewCount = data.workers.filter((item) => item.review_status !== 'current').length;
  const employerReviewCount = data.employers.filter((item) => item.review_status !== 'current').length;
  const incompleteCount = [...data.workers, ...data.employers].filter((item) => item.complete === false).length;
  const operationsUnavailable = isProjectionFailure(data.operationsStatus);
  const pendingShiftCount = operationsUnavailable
    ? null
    : data.operations?.shiftItems.filter((item) => item.shiftStatus === 'pending_review').length ?? 0;
  const timedShiftCount = operationsUnavailable ? null : data.operations?.shiftItems.length ?? 0;
  const workerKpi = copy.kpis[0];
  const urgentKpi = copy.kpis[2];
  const calendarKpi = copy.kpis[3];
  if (!workerKpi || !urgentKpi || !calendarKpi) return copy.kpis;
  return [
    { ...workerKpi, value: String(workerReviewCount) },
    {
      accent: 'success',
      href: '/staff/intakes/employers?queue=review',
      icon: 'building',
      label: language === 'es' ? 'Registros de empleadores' : 'Employer intakes',
      meta: language === 'es' ? 'requieren revision' : 'need review',
      value: String(employerReviewCount),
    },
    {
      ...urgentKpi,
      href: pendingShiftCount ? '/staff/queues' : urgentKpi.href,
      label: pendingShiftCount ? language === 'es' ? 'Turnos en revision' : 'Shifts in review' : language === 'es' ? 'Registros incompletos' : 'Incomplete intakes',
      value: String(pendingShiftCount || incompleteCount),
    },
    {
      ...calendarKpi,
      label: language === 'es' ? 'Turnos registrados' : 'Recorded shifts',
      meta: timedShiftCount === null
        ? language === 'es' ? 'proyeccion no disponible' : 'projection unavailable'
        : language === 'es' ? 'desde solicitudes' : 'from requests',
      value: timedShiftCount === null ? 'N/A' : String(timedShiftCount),
    },
  ];
}

function requestHref(item: OperationsRequestItem | OperationsShiftItem) {
  return item.sourceIntakeId
    ? `/staff/intakes/${item.sourceIntakeId}/outputs/request`
    : `/staff/intakes/employers?reference=${item.employerId}&open=match`;
}

function rowFromRequest(item: OperationsRequestItem, template: DashboardCopy['queueRows'][number], language: 'en' | 'es'): DashboardCopy['queueRows'][number] {
  return {
    ...template,
    days: item.requestStatus === 'pending_review'
      ? language === 'es' ? 'Revision' : 'Review'
      : language === 'es' ? 'Borrador' : 'Draft',
    href: requestHref(item),
    icon: 'building',
    name: item.requestStatus === 'pending_review'
      ? language === 'es' ? 'Solicitud en revision' : 'Request in review'
      : language === 'es' ? 'Preparar solicitud' : 'Prepare request',
    next: language === 'es'
      ? `${item.roleTitle}, ${String(item.workerCount)} trabajador(es)`
      : `${item.roleTitle}, ${String(item.workerCount)} worker(s)`,
    ref: item.employerName,
    status: item.requestStatus === 'pending_review' ? 'in_review' : 'draft',
  };
}

function rowFromShift(item: OperationsShiftItem, template: DashboardCopy['queueRows'][number], language: 'en' | 'es'): DashboardCopy['queueRows'][number] {
  const starts = new Date(item.startsAt);
  return {
    ...template,
    days: Number.isNaN(starts.getTime())
      ? language === 'es' ? 'Turno' : 'Shift'
      : starts.toLocaleString(language === 'es' ? 'es-US' : 'en-US', { hour: 'numeric', minute: '2-digit', month: 'short', day: 'numeric' }),
    href: requestHref(item),
    icon: 'schedule',
    name: item.shiftStatus === 'pending_review'
      ? language === 'es' ? 'Turno en revision' : 'Shift in review'
      : language === 'es' ? 'Turno en borrador' : 'Draft shift',
    next: language === 'es'
      ? `${item.roleTitle}, ${String(item.workerCount)} trabajador(es)`
      : `${item.roleTitle}, ${String(item.workerCount)} worker(s)`,
    ref: item.employerName,
    status: item.shiftStatus === 'pending_review' ? 'in_review' : 'draft',
  };
}

function rowFromIntake(
  kind: IntakeKind,
  item: IntakeSummary,
  template: DashboardCopy['queueRows'][number],
  language: 'en' | 'es',
): DashboardCopy['queueRows'][number] {
  return {
    ...template,
    href: intakeHref(kind, item),
    next: nextStep(item, language),
    ref: displayName(item, language),
    status: queueStatus(item),
  };
}

function dynamicQueueRows(copy: DashboardCopy, data: DashboardIntakes, language: 'en' | 'es'): DashboardCopy['queueRows'] {
  if (!data.loaded) return copy.queueRows;
  if (
    data.workers.length === 0 &&
    data.employers.length === 0 &&
    (!data.operations || (data.operations.requestItems.length === 0 && data.operations.shiftItems.length === 0))
  ) return isProjectionFailure(data.operationsStatus) ? copy.queueRows : [];
  const rows = [...copy.queueRows];
  const operationRows = [
    ...(data.operations?.shiftItems.map((item, index) => {
      const template = rows[index] ?? rows[0];
      return template ? rowFromShift(item, template, language) : null;
    }) ?? []),
    ...(data.operations?.requestItems.map((item, index) => {
      const template = rows[(data.operations?.shiftItems.length ?? 0) + index] ?? rows[0];
      return template ? rowFromRequest(item, template, language) : null;
    }) ?? []),
  ].filter((row): row is DashboardCopy['queueRows'][number] => row !== null);
  if (operationRows.length) return [...operationRows, ...rows].slice(0, rows.length);
  const workerReviewCount = data.workers.filter((item) => item.review_status !== 'current').length;
  const primaryWorker = data.workers.find((item) => item.complete === false) ?? data.workers[0];
  const primaryEmployer = data.employers.find((item) => item.complete === false) ?? data.employers[0];
  const availabilityWorker = data.workers.find((item) => item.missing_fields.includes('availability')) ?? data.workers[1] ?? data.workers[0];

  const primaryWorkerTemplate = rows[0];
  const primaryEmployerTemplate = rows[1];
  const availabilityWorkerTemplate = rows[2];
  const reviewQueueTemplate = rows[3];
  if (primaryWorker && primaryWorkerTemplate) rows[0] = rowFromIntake('worker', primaryWorker, primaryWorkerTemplate, language);
  if (primaryEmployer && primaryEmployerTemplate) rows[1] = rowFromIntake('employer', primaryEmployer, primaryEmployerTemplate, language);
  if (availabilityWorker && availabilityWorkerTemplate) rows[2] = rowFromIntake('worker', availabilityWorker, availabilityWorkerTemplate, language);
  if (!reviewQueueTemplate) return rows;
  rows[3] = {
    ...reviewQueueTemplate,
    next: language === 'es'
      ? `${String(workerReviewCount)} registros sin revisar`
      : `${String(workerReviewCount)} records waiting`,
  };
  return rows;
}

function dynamicScheduleRows(copy: DashboardCopy, data: DashboardIntakes, language: 'en' | 'es'): DashboardCopy['scheduleRows'] {
  const shifts = data.operations?.shiftItems ?? [];
  if (!data.loaded || isProjectionFailure(data.operationsStatus)) return copy.scheduleRows;
  if (!shifts.length) return [];
  return shifts.slice(0, 5).map((item) => {
    const starts = new Date(item.startsAt);
    const ends = new Date(item.endsAt);
    return {
      dot: item.shiftStatus === 'pending_review' ? 'warning' : 'info',
      meta: Number.isNaN(ends.getTime())
        ? item.employerName
        : `${item.employerName} - ${ends.toLocaleTimeString(language === 'es' ? 'es-US' : 'en-US', { hour: 'numeric', minute: '2-digit' })}`,
      time: Number.isNaN(starts.getTime())
        ? language === 'es' ? 'Turno' : 'Shift'
        : starts.toLocaleTimeString(language === 'es' ? 'es-US' : 'en-US', { hour: 'numeric', minute: '2-digit' }),
      title: `${item.roleTitle} (${String(item.workerCount)})`,
    };
  });
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
  const [intakes, setIntakes] = useState<DashboardIntakes>({
    employers: [],
    loaded: false,
    operations: null,
    operationsStatus: 'loading',
    workers: [],
  });

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      queryIntakes('worker', { page_size: 50 }).catch(() => ({ ok: false as const, failure: 'failed' as const })),
      queryIntakes('employer', { page_size: 50 }).catch(() => ({ ok: false as const, failure: 'failed' as const })),
      getOperationsProjection().catch(() => ({ ok: false as const, failure: { kind: 'unavailable' as const } })),
    ])
      .then(([workerResult, employerResult, operationsResult]) => {
        if (cancelled) return;
        setIntakes({
          workers: workerResult.ok ? workerResult.value.items : [],
          employers: employerResult.ok ? employerResult.value.items : [],
          loaded: true,
          operations: operationsResult.ok ? operationsResult.value : null,
          operationsStatus: operationsResult.ok ? 'ready' : operationsResult.failure.kind,
        });
      })
      .catch(() => {
        if (!cancelled) setIntakes({ employers: [], loaded: true, operations: null, operationsStatus: 'unavailable', workers: [] });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const kpis = useMemo(() => dynamicKpis(copy, intakes, language), [copy, intakes, language]);
  const queueRows = useMemo(() => dynamicQueueRows(copy, intakes, language), [copy, intakes, language]);
  const scheduleRows = useMemo(() => dynamicScheduleRows(copy, intakes, language), [copy, intakes, language]);
  const operationsNotice = useMemo(() => projectionNotice(intakes.operationsStatus, language), [intakes.operationsStatus, language]);
  const workerRows = useMemo(
    () => recentRows('worker', intakes.workers, language, copy.recentRows),
    [copy.recentRows, intakes.workers, language],
  );
  const employerRows = useMemo(
    () => recentRows(
      'employer',
      intakes.employers,
      language,
      [
        { href: '/staff/intakes/employers', meta: language === 'es' ? 'hoy' : 'Today', name: 'Sunshine Home Care', status: 'pending' },
        { href: '/staff/intakes/employers', meta: language === 'es' ? 'hace 1 dia' : '1 day ago', name: 'Family First LLC', status: 'incomplete' },
        { href: '/staff/intakes/employers', meta: language === 'es' ? 'hace 2 dias' : '2 days ago', name: 'Caring Hands', status: 'complete' },
      ],
    ),
    [intakes.employers, language],
  );

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
        {kpis.map((kpi) => (
          <Link className="dashboard-card dashboard-kpi focus-ring" data-accent={kpi.accent} key={kpi.label} to={kpi.href}>
            <IconMark name={kpi.icon} />
            <span className="dashboard-kpi__number">{kpi.value}</span>
            <span className="dashboard-kpi__label">{kpi.label}</span>
            <span className="dashboard-kpi__meta">{kpi.meta}</span>
            <span aria-hidden="true" className="dashboard-card__arrow">&gt;</span>
          </Link>
        ))}
      </div>

      {operationsNotice ? (
        <p className="projection-status-notice" role="status">{operationsNotice}</p>
      ) : null}

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
            {queueRows.map((row) => (
              <Link className="dashboard-queue__row focus-ring" key={`${row.name}-${row.days}`} to={row.href}>
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
            {queueRows.length === 0 ? <p className="dashboard-empty-state">{copy.emptyQueue}</p> : null}
          </div>
        </section>

        <section className="dashboard-card dashboard-card--schedule" aria-labelledby="schedule-heading">
          <div className="dashboard-section-header">
            <h3 id="schedule-heading"><IconMark name="calendar" /> {copy.scheduleHeading}</h3>
            <Link className="dashboard-text-link focus-ring" to="/staff/calendar">{copy.scheduleLink}</Link>
          </div>
          <ol className="schedule-list">
            {scheduleRows.map((row) => (
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
          {scheduleRows.length === 0 ? <p className="dashboard-empty-state">{copy.emptySchedule}</p> : null}
        </section>
      </div>

      <div className="dashboard-bottom-grid">
        <section className="dashboard-card" aria-labelledby="recent-workers-heading">
          <div className="dashboard-section-header">
            <h3 id="recent-workers-heading"><IconMark name="worker" /> {copy.recentWorkerHeading}</h3>
            <Link className="dashboard-text-link focus-ring" to="/staff/intakes/workers">{copy.primaryQueueLink}</Link>
          </div>
          <RecentRows rows={workerRows} language={language} />
        </section>

        <section className="dashboard-card" aria-labelledby="recent-employers-heading">
          <div className="dashboard-section-header">
            <h3 id="recent-employers-heading"><IconMark name="building" /> {copy.recentEmployerHeading}</h3>
            <Link className="dashboard-text-link focus-ring" to="/staff/intakes/employers">{copy.primaryQueueLink}</Link>
          </div>
          <RecentRows language={language} rows={employerRows} />
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
