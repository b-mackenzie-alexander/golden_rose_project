import { Link } from 'react-router';
import { useEffect, useMemo, useState } from 'react';

import { queryIntakes } from '../api/intakeClient';
import type { IntakeKind, IntakeSummary } from '../api/intakeContracts';
import { getOperationsProjection, type OperationsProjection, type OperationsProjectionFailureKind, type OperationsQueueSummary, type OperationsRequestItem, type OperationsShiftItem } from '../api/operationsProjectionClient';
import { IconSymbol } from '../dashboard/artwork';
import type { IconName } from '../dashboard/artwork';
import { useLanguage } from '../i18n/LanguageProvider';

type QueueFilter = 'all' | 'employer' | 'urgent' | 'worker';

type QueueStatus = 'draft' | 'in_review' | 'incomplete' | 'pending';

type QueueItem = {
  age: string;
  assignee: string;
  category: Exclude<QueueFilter, 'all'>;
  href: string;
  icon: IconName;
  id: string;
  nextStep: string;
  owner: string;
  priority: 'high' | 'low' | 'medium';
  reason: string;
  reference: string;
  status: QueueStatus;
  title: string;
};

type ProjectionStatus = 'loading' | 'ready' | OperationsProjectionFailureKind;

type WorkQueuesCopy = {
  assignee: string;
  empty: string;
  filters: Array<{ id: QueueFilter; label: string }>;
  heading: string;
  items: QueueItem[];
  nextStep: string;
  open: string;
  owner: string;
  priority: string;
  queueHeading: string;
  reason: string;
  reference: string;
  status: string;
  subtitle: string;
  summaryItems: Array<{ icon: IconName; label: string; value: string }>;
};

const statusLabels: Record<QueueStatus, { en: string; es: string }> = {
  draft: { en: 'Draft', es: 'Borrador' },
  in_review: { en: 'In review', es: 'En revision' },
  incomplete: { en: 'Incomplete', es: 'Incompleto' },
  pending: { en: 'Pending', es: 'Pendiente' },
};

const englishQueues: WorkQueuesCopy = {
  assignee: 'Assignee',
  empty: 'No queue items match this view.',
  filters: [
    { id: 'all', label: 'All work' },
    { id: 'urgent', label: 'Urgent' },
    { id: 'worker', label: 'Worker intakes' },
    { id: 'employer', label: 'Employer follow-ups' },
  ],
  heading: 'Work queues',
  items: [
    { age: 'Due 9:00 AM', assignee: 'Mariela Torres', category: 'worker', href: '/staff/intakes/workers?q=Ana%20Quispe&open=match', icon: 'worker', id: 'WRK-2025-00123', nextStep: 'Add residential address', owner: 'Ana Quispe', priority: 'high', reason: 'Missing restricted address blocks review', reference: 'Worker intake', status: 'incomplete', title: 'Urgent intake review' },
    { age: 'Due 10:30 AM', assignee: 'Carlos Ramirez', category: 'employer', href: '/staff/intakes/employers?q=Restaurante%20La%20Esperanza&open=match', icon: 'building', id: 'EMP-2025-00456', nextStep: 'Confirm worksite details', owner: 'Restaurante La Esperanza', priority: 'medium', reason: 'Follow-up deadline is next on today\'s agenda', reference: 'Employer follow-up', status: 'pending', title: 'Employer follow-up' },
    { age: 'Due 11:00 AM', assignee: 'Ana Torres', category: 'worker', href: '/staff/intakes/workers?q=Carlos%20Mendoza&open=match', icon: 'worker', id: 'WRK-2025-00124', nextStep: 'Review availability', owner: 'Carlos Mendoza', priority: 'medium', reason: 'Interview cannot close until availability is reviewed', reference: 'Worker interview', status: 'pending', title: 'Complete pending interview' },
    { age: 'Due 1:00 PM', assignee: 'Operations', category: 'worker', href: '/staff/intakes/workers?queue=review', icon: 'document', id: 'WRK-DRAFTS', nextStep: 'Three records waiting', owner: 'Draft queue', priority: 'low', reason: 'Dashboard review queue has new worker drafts', reference: 'Draft review', status: 'draft', title: 'Review new drafts' },
    { age: 'Due 3:00 PM', assignee: 'Sofia Diaz', category: 'employer', href: '/staff/work-interests', icon: 'catalog', id: 'CAT-2025-00008', nextStep: 'Review new skill labels', owner: 'Catalog', priority: 'low', reason: 'New intake text introduced uncataloged work interests', reference: 'Work-interest catalog', status: 'in_review', title: 'Update interest catalog' },
  ],
  nextStep: 'Next step',
  open: 'Open',
  owner: 'Person / item',
  priority: 'Priority',
  queueHeading: 'Prioritized work',
  reason: 'Why it is here',
  reference: 'Reference',
  status: 'Status',
  subtitle: 'Prioritized work that needs review, follow-up, or a clear next action.',
  summaryItems: [
    { icon: 'warning', label: 'Urgent', value: '1' },
    { icon: 'worker', label: 'Worker items', value: '3' },
    { icon: 'building', label: 'Employer items', value: '2' },
    { icon: 'queue', label: 'Open queue items', value: '5' },
  ],
};

const spanishQueues: WorkQueuesCopy = {
  assignee: 'Asignado a',
  empty: 'No hay elementos para esta vista.',
  filters: [
    { id: 'all', label: 'Todo el trabajo' },
    { id: 'urgent', label: 'Urgente' },
    { id: 'worker', label: 'Registros de trabajadores' },
    { id: 'employer', label: 'Seguimientos de empleadores' },
  ],
  heading: 'Colas de trabajo',
  items: [
    { age: 'Vence 9:00 a. m.', assignee: 'Mariela Torres', category: 'worker', href: '/staff/intakes/workers?q=Ana%20Quispe&open=match', icon: 'worker', id: 'WRK-2025-00123', nextStep: 'Agregar domicilio residencial', owner: 'Ana Quispe', priority: 'high', reason: 'Falta domicilio restringido para completar la revision', reference: 'Registro de trabajador', status: 'incomplete', title: 'Revisar solicitud urgente' },
    { age: 'Vence 10:30 a. m.', assignee: 'Carlos Ramirez', category: 'employer', href: '/staff/intakes/employers?q=Restaurante%20La%20Esperanza&open=match', icon: 'building', id: 'EMP-2025-00456', nextStep: 'Confirmar lugar de trabajo', owner: 'Restaurante La Esperanza', priority: 'medium', reason: 'El seguimiento vence en la agenda de hoy', reference: 'Seguimiento de empleador', status: 'pending', title: 'Hacer seguimiento con empleador' },
    { age: 'Vence 11:00 a. m.', assignee: 'Ana Torres', category: 'worker', href: '/staff/intakes/workers?q=Carlos%20Mendoza&open=match', icon: 'worker', id: 'WRK-2025-00124', nextStep: 'Revisar disponibilidad', owner: 'Carlos Mendoza', priority: 'medium', reason: 'La entrevista necesita disponibilidad revisada', reference: 'Entrevista de trabajador', status: 'pending', title: 'Completar entrevista pendiente' },
    { age: 'Vence 1:00 p. m.', assignee: 'Operaciones', category: 'worker', href: '/staff/intakes/workers?queue=review', icon: 'document', id: 'WRK-DRAFTS', nextStep: 'Tres registros sin revisar', owner: 'Cola de borradores', priority: 'low', reason: 'La cola del panel tiene nuevos borradores de trabajador', reference: 'Revision de borradores', status: 'draft', title: 'Revisar nuevos borradores' },
    { age: 'Vence 3:00 p. m.', assignee: 'Sofia Diaz', category: 'employer', href: '/staff/work-interests', icon: 'catalog', id: 'CAT-2025-00008', nextStep: 'Revisar nuevas habilidades', owner: 'Catalogo', priority: 'low', reason: 'Un registro agrego intereses laborales sin catalogar', reference: 'Catalogo de intereses', status: 'in_review', title: 'Actualizar catalogo de intereses' },
  ],
  nextStep: 'Siguiente paso',
  open: 'Abrir',
  owner: 'Persona / elemento',
  priority: 'Prioridad',
  queueHeading: 'Trabajo priorizado',
  reason: 'Por que aparece',
  reference: 'Referencia',
  status: 'Estado',
  subtitle: 'Trabajo priorizado que necesita revision, seguimiento o un siguiente paso claro.',
  summaryItems: [
    { icon: 'warning', label: 'Urgente', value: '1' },
    { icon: 'worker', label: 'Trabajadores', value: '3' },
    { icon: 'building', label: 'Empleadores', value: '2' },
    { icon: 'queue', label: 'Elementos abiertos', value: '5' },
  ],
};

function statusLabel(status: QueueStatus, language: 'en' | 'es') {
  return statusLabels[status][language];
}

type QueueData = {
  employers: IntakeSummary[];
  loaded: boolean;
  operations: OperationsProjection | null;
  operationsStatus: ProjectionStatus;
  workers: IntakeSummary[];
};

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
    ? `No se pudieron leer las solicitudes y turnos porque ${reason}. La cola conserva registros guardados y muestra ejemplos solo cuando no hay una lectura autoritativa.`
    : `Requests and shifts could not be read because ${reason}. The queue keeps saved intake rows visible and uses examples only where an authoritative read is unavailable.`;
}

function formatQueueTimestamp(value: string | null, language: 'en' | 'es') {
  if (value === null) return language === 'es' ? 'sin actualizaciones registradas' : 'no recorded updates';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return language === 'es' ? 'actualizacion registrada' : 'recorded update';
  return date.toLocaleString(language === 'es' ? 'es-US' : 'en-US', {
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    month: 'short',
  });
}

function queueSummaryNotice(summary: OperationsQueueSummary, language: 'en' | 'es') {
  const oldest = formatQueueTimestamp(summary.oldestItemUpdatedAt, language);
  if (language === 'es') {
    return `Cola de solicitudes y turnos: ${String(summary.openItemCount)} elemento(s) abiertos, ${String(summary.pendingReviewCount)} en revision y ${String(summary.highPriorityCount)} de alta prioridad; actualizacion mas antigua ${oldest}. Esto no asigna trabajadores ni confirma cobertura.`;
  }
  return `Request and shift queue: ${String(summary.openItemCount)} open item(s), ${String(summary.pendingReviewCount)} in review and ${String(summary.highPriorityCount)} high priority; oldest update ${oldest}. This does not assign workers or confirm coverage.`;
}

function intakeHref(kind: IntakeKind, item: IntakeSummary) {
  return `/staff/intakes/${kind === 'worker' ? 'workers' : 'employers'}?reference=${item.intake_id}&open=match`;
}

function displayName(item: IntakeSummary, language: 'en' | 'es') {
  return item.display_name?.trim() || (language === 'es' ? 'Registro sin nombre' : 'Unnamed intake');
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

function itemStatus(item: IntakeSummary): QueueStatus {
  if (item.complete === false) return 'incomplete';
  if (item.follow_up || item.review_status === 'needs_follow_up') return 'pending';
  if (item.review_status === 'stale') return 'in_review';
  return 'draft';
}

function itemPriority(item: IntakeSummary): QueueItem['priority'] {
  if (item.follow_up?.overdue || item.complete === false) return 'high';
  if (item.follow_up || item.review_status === 'needs_follow_up' || item.review_status === 'stale') return 'medium';
  return 'low';
}

function itemNextStep(item: IntakeSummary, language: 'en' | 'es') {
  const firstMissing = item.missing_fields[0];
  if (firstMissing) {
    return language === 'es'
      ? `Completar ${missingLabel(firstMissing, language)}`
      : `Complete ${missingLabel(firstMissing, language)}`;
  }
  if (item.follow_up || item.review_status === 'needs_follow_up') {
    return language === 'es' ? 'Completar seguimiento' : 'Complete follow-up';
  }
  if (item.review_status !== 'current') {
    return language === 'es' ? 'Revisar borrador' : 'Review draft';
  }
  return language === 'es' ? 'Abrir registro' : 'Open intake';
}

function itemReason(kind: IntakeKind, item: IntakeSummary, language: 'en' | 'es') {
  if (item.follow_up?.overdue) {
    return language === 'es' ? 'El seguimiento esta vencido' : 'Follow-up is overdue';
  }
  if (item.follow_up) {
    return language === 'es' ? 'El seguimiento es el siguiente paso registrado' : 'Follow-up is the recorded next step';
  }
  if (item.complete === false) {
    return language === 'es' ? 'El registro necesita campos obligatorios' : 'Required intake fields are still missing';
  }
  return kind === 'employer'
    ? language === 'es' ? 'Borrador de empleador pendiente de revision' : 'Employer draft is waiting for review'
    : language === 'es' ? 'Borrador de trabajador pendiente de revision' : 'Worker draft is waiting for review';
}

function itemAge(item: IntakeSummary, language: 'en' | 'es') {
  if (item.follow_up) {
    const due = new Date(item.follow_up.next_follow_up_at);
    if (!Number.isNaN(due.getTime())) {
      return due.toLocaleString(language === 'es' ? 'es-US' : 'en-US', {
        hour: 'numeric',
        minute: '2-digit',
        month: 'short',
        day: 'numeric',
      });
    }
  }
  return language === 'es' ? 'Borrador' : 'Draft';
}

function itemFromIntake(kind: IntakeKind, item: IntakeSummary, language: 'en' | 'es'): QueueItem {
  const owner = displayName(item, language);
  const priority = itemPriority(item);
  return {
    age: itemAge(item, language),
    assignee: language === 'es' ? 'Operaciones' : 'Operations',
    category: kind === 'employer' ? 'employer' : 'worker',
    href: intakeHref(kind, item),
    icon: kind === 'employer' ? 'building' : 'worker',
    id: item.intake_id,
    nextStep: itemNextStep(item, language),
    owner,
    priority,
    reason: itemReason(kind, item, language),
    reference: kind === 'employer'
      ? language === 'es' ? 'Registro de empleador' : 'Employer intake'
      : language === 'es' ? 'Registro de trabajador' : 'Worker intake',
    status: itemStatus(item),
    title: kind === 'employer'
      ? language === 'es' ? 'Seguimiento de empleador' : 'Employer follow-up'
      : priority === 'high'
        ? language === 'es' ? 'Revisar solicitud urgente' : 'Urgent intake review'
        : language === 'es' ? 'Revision de trabajador' : 'Worker intake review',
  };
}

function requestHref(item: Pick<OperationsRequestItem, 'sourceIntakeId' | 'employerId'>) {
  return item.sourceIntakeId
    ? `/staff/intakes/${item.sourceIntakeId}/outputs/request`
    : `/staff/intakes/employers?reference=${item.employerId}&open=match`;
}

function operationStatus(status: 'draft' | 'pending_review'): QueueStatus {
  return status === 'pending_review' ? 'in_review' : 'draft';
}

function formatShiftWindow(item: OperationsShiftItem, language: 'en' | 'es') {
  const starts = new Date(item.startsAt);
  if (Number.isNaN(starts.getTime())) return language === 'es' ? 'Horario registrado' : 'Shift recorded';
  return starts.toLocaleString(language === 'es' ? 'es-US' : 'en-US', {
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    month: 'short',
  });
}

function itemFromRequest(item: OperationsRequestItem, language: 'en' | 'es'): QueueItem {
  return {
    age: item.requestStatus === 'pending_review'
      ? language === 'es' ? 'Revision' : 'Review'
      : language === 'es' ? 'Borrador' : 'Draft',
    assignee: language === 'es' ? 'Operaciones' : 'Operations',
    category: 'employer',
    href: requestHref(item),
    icon: 'building',
    id: item.staffingRequestId,
    nextStep: item.requestStatus === 'pending_review'
      ? language === 'es' ? 'Revisar solicitud' : 'Review request'
      : language === 'es' ? 'Agregar turnos o enviar a revision' : 'Add shifts or submit for review',
    owner: item.employerName,
    priority: item.requestStatus === 'pending_review' ? 'medium' : 'low',
    reason: language === 'es'
      ? `Solicitud de ${item.roleTitle} con ${String(item.workerCount)} trabajador(es)`
      : `${item.roleTitle} request for ${String(item.workerCount)} worker(s)`,
    reference: language === 'es' ? 'Solicitud de personal' : 'Staffing request',
    status: operationStatus(item.requestStatus),
    title: item.requestStatus === 'pending_review'
      ? language === 'es' ? 'Solicitud en revision' : 'Request in review'
      : language === 'es' ? 'Preparar solicitud de personal' : 'Prepare staffing request',
  };
}

function itemFromShift(item: OperationsShiftItem, language: 'en' | 'es'): QueueItem {
  return {
    age: formatShiftWindow(item, language),
    assignee: language === 'es' ? 'Operaciones' : 'Operations',
    category: 'employer',
    href: requestHref(item),
    icon: 'schedule',
    id: item.shiftNeedId,
    nextStep: item.shiftStatus === 'pending_review'
      ? language === 'es' ? 'Revisar turno' : 'Review shift'
      : language === 'es' ? 'Enviar turno a revision' : 'Submit shift for review',
    owner: item.employerName,
    priority: item.shiftStatus === 'pending_review' ? 'high' : 'medium',
    reason: language === 'es'
      ? `${item.roleTitle}, ${String(item.workerCount)} trabajador(es)`
      : `${item.roleTitle}, ${String(item.workerCount)} worker(s)`,
    reference: language === 'es' ? 'Turno solicitado' : 'Requested shift',
    status: operationStatus(item.shiftStatus),
    title: item.shiftStatus === 'pending_review'
      ? language === 'es' ? 'Turno pendiente de revision' : 'Shift pending review'
      : language === 'es' ? 'Turno en borrador' : 'Draft shift need',
  };
}

function dynamicItems(copy: WorkQueuesCopy, data: QueueData | null, language: 'en' | 'es') {
  if (
    data === null ||
    !data.loaded ||
    (data.workers.length === 0 && data.employers.length === 0 &&
      (!data.operations || (data.operations.requestItems.length === 0 && data.operations.shiftItems.length === 0)))
  ) {
    return data?.loaded && !isProjectionFailure(data.operationsStatus) ? [] : copy.items;
  }
  return [
    ...(data.operations?.shiftItems.map((item) => itemFromShift(item, language)) ?? []),
    ...(data.operations?.requestItems.map((item) => itemFromRequest(item, language)) ?? []),
    ...data.workers.map((item) => itemFromIntake('worker', item, language)),
    ...data.employers.map((item) => itemFromIntake('employer', item, language)),
  ]
    .sort((left, right) => {
      const priorityOrder = { high: 0, medium: 1, low: 2 } as const;
      return priorityOrder[left.priority] - priorityOrder[right.priority];
    })
    .slice(0, 8);
}

function dynamicSummary(copy: WorkQueuesCopy, items: QueueItem[]) {
  if (items === copy.items) return copy.summaryItems;
  const urgent = items.filter((item) => item.priority === 'high').length;
  const workers = items.filter((item) => item.category === 'worker').length;
  const employers = items.filter((item) => item.category === 'employer').length;
  return copy.summaryItems.map((item) => {
    if (item.icon === 'warning') return { ...item, value: String(urgent) };
    if (item.icon === 'worker') return { ...item, value: String(workers) };
    if (item.icon === 'building') return { ...item, value: String(employers) };
    if (item.icon === 'queue') return { ...item, value: String(items.length) };
    return item;
  });
}

export function WorkQueues() {
  const { language } = useLanguage();
  const copy = language === 'es' ? spanishQueues : englishQueues;
  const [filter, setFilter] = useState<QueueFilter>('all');
  const [queueData, setQueueData] = useState<QueueData | null>({
    employers: [],
    loaded: false,
    operations: null,
    operationsStatus: 'loading',
    workers: [],
  });
  const items = useMemo(() => dynamicItems(copy, queueData, language), [copy, language, queueData]);
  const summaryItems = useMemo(() => dynamicSummary(copy, items), [copy, items]);
  const operationsNotice = useMemo(() => projectionNotice(queueData?.operationsStatus ?? 'loading', language), [language, queueData?.operationsStatus]);
  const queueNotice = useMemo(
    () => (queueData?.operationsStatus === 'ready' && queueData.operations !== null
      ? queueSummaryNotice(queueData.operations.queueSummary, language)
      : null),
    [language, queueData],
  );
  const visibleItems = useMemo(
    () => items.filter((item) => filter === 'all' || (filter === 'urgent' ? item.priority === 'high' : item.category === filter)),
    [filter, items],
  );

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      queryIntakes('worker', { page_size: 50 }).catch(() => ({ ok: false as const, failure: 'failed' as const })),
      queryIntakes('employer', { page_size: 50 }).catch(() => ({ ok: false as const, failure: 'failed' as const })),
      getOperationsProjection().catch(() => ({ ok: false as const, failure: { kind: 'unavailable' as const } })),
    ])
      .then(([workerResult, employerResult, operationsResult]) => {
        if (cancelled) return;
        setQueueData({
          workers: workerResult.ok ? workerResult.value.items : [],
          employers: employerResult.ok ? employerResult.value.items : [],
          loaded: true,
          operations: operationsResult.ok ? operationsResult.value : null,
          operationsStatus: operationsResult.ok ? 'ready' : operationsResult.failure.kind,
        });
      })
      .catch(() => {
        if (!cancelled) setQueueData({ employers: [], loaded: true, operations: null, operationsStatus: 'unavailable', workers: [] });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section aria-labelledby="work-queues-heading" className="work-queues-page">
      <div className="work-queues-hero">
        <div>
          <p className="work-queues-eyebrow">{language === 'es' ? 'Operacion diaria' : 'Daily operations'}</p>
          <h2 id="work-queues-heading">{copy.heading}</h2>
          <p>{copy.subtitle}</p>
        </div>
      </div>

      <div className="queue-summary-grid" aria-label={language === 'es' ? 'Resumen de colas' : 'Queue summary'}>
        {summaryItems.map((item) => (
          <div className="queue-summary-card" key={item.label}>
            <span aria-hidden="true" className="dashboard-icon">
              <IconSymbol name={item.icon} />
            </span>
            <strong>{item.value}</strong>
            <span>{item.label}</span>
          </div>
        ))}
      </div>

      {operationsNotice ? (
        <p className="projection-status-notice" role="status">{operationsNotice}</p>
      ) : queueNotice ? (
        <p className="queue-aging-note">{queueNotice}</p>
      ) : null}

      <section className="queue-panel" aria-labelledby="queue-list-heading">
        <div className="queue-panel-header">
          <h3 id="queue-list-heading">{copy.queueHeading}</h3>
          <div className="queue-filter-bar" aria-label={language === 'es' ? 'Filtros de cola' : 'Queue filters'}>
            {copy.filters.map((queueFilter) => (
              <button
                aria-pressed={filter === queueFilter.id}
                className="focus-ring"
                key={queueFilter.id}
                type="button"
                onClick={() => {
                  setFilter(queueFilter.id);
                }}
              >
                {queueFilter.label}
              </button>
            ))}
          </div>
        </div>

        <div className="queue-table" aria-label={copy.queueHeading}>
          <div className="queue-table-head">
            <span>{copy.owner}</span>
            <span>{copy.status}</span>
            <span>{copy.nextStep}</span>
            <span>{copy.reason}</span>
            <span>{copy.assignee}</span>
            <span>{copy.priority}</span>
            <span>{copy.open}</span>
          </div>
          <div>
            {visibleItems.map((item) => (
              <article className="queue-row" data-priority={item.priority} key={item.id}>
                <div className="queue-row-primary">
                  <span aria-hidden="true" className="queue-row-icon">
                    <IconSymbol name={item.icon} />
                  </span>
                  <span>
                    <strong>{item.title}</strong>
                    <small>{item.owner} - {item.id}</small>
                  </span>
                </div>
                <span className="status-chip" data-status={item.status}>{statusLabel(item.status, language)}</span>
                <span>{item.nextStep}</span>
                <span>{item.reason}</span>
                <span>{item.assignee}</span>
                <span><span className="queue-priority">{item.age}</span></span>
                <Link className="dashboard-text-link focus-ring" to={item.href}>{copy.open}</Link>
              </article>
            ))}
          </div>
        </div>
        {visibleItems.length === 0 ? <p className="queue-empty">{copy.empty}</p> : null}
      </section>
    </section>
  );
}
