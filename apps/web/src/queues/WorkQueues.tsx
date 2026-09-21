import { Link } from 'react-router';
import { useMemo, useState } from 'react';

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
    { age: 'Due 9:00 AM', assignee: 'Mariela Torres', category: 'urgent', href: '/staff/intakes/workers?reference=b7dea69e-9b10-43b3-95aa-d1cd01f6c453&open=match', icon: 'worker', id: 'WRK-2025-00123', nextStep: 'Add residential address', owner: 'Preview Catalog Worker', priority: 'high', reason: 'Missing restricted address blocks review', reference: 'Worker intake', status: 'incomplete', title: 'Urgent intake review' },
    { age: 'Due 10:30 AM', assignee: 'Carlos Ramirez', category: 'employer', href: '/staff/intakes/employers?reference=40bd8f48-88c2-42bf-a2bb-bd4ee6e962e2&open=match', icon: 'building', id: 'EMP-2025-00456', nextStep: 'Confirm worksite details', owner: 'Heather Micca', priority: 'medium', reason: 'Follow-up deadline is next on today\'s agenda', reference: 'Employer follow-up', status: 'pending', title: 'Employer follow-up' },
    { age: 'Due 11:00 AM', assignee: 'Ana Torres', category: 'worker', href: '/staff/intakes/workers?reference=ca0a3935-e72f-4a00-be6d-af081546a73f&open=match', icon: 'worker', id: 'WRK-2025-00124', nextStep: 'Review availability', owner: 'Jason Meme', priority: 'medium', reason: 'Interview cannot close until availability is reviewed', reference: 'Worker interview', status: 'pending', title: 'Complete pending interview' },
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
    { age: 'Vence 9:00 a. m.', assignee: 'Mariela Torres', category: 'urgent', href: '/staff/intakes/workers?reference=b7dea69e-9b10-43b3-95aa-d1cd01f6c453&open=match', icon: 'worker', id: 'WRK-2025-00123', nextStep: 'Agregar domicilio residencial', owner: 'Preview Catalog Worker', priority: 'high', reason: 'Falta domicilio restringido para completar la revision', reference: 'Registro de trabajador', status: 'incomplete', title: 'Revisar solicitud urgente' },
    { age: 'Vence 10:30 a. m.', assignee: 'Carlos Ramirez', category: 'employer', href: '/staff/intakes/employers?reference=40bd8f48-88c2-42bf-a2bb-bd4ee6e962e2&open=match', icon: 'building', id: 'EMP-2025-00456', nextStep: 'Confirmar lugar de trabajo', owner: 'Heather Micca', priority: 'medium', reason: 'El seguimiento vence en la agenda de hoy', reference: 'Seguimiento de empleador', status: 'pending', title: 'Hacer seguimiento con empleador' },
    { age: 'Vence 11:00 a. m.', assignee: 'Ana Torres', category: 'worker', href: '/staff/intakes/workers?reference=ca0a3935-e72f-4a00-be6d-af081546a73f&open=match', icon: 'worker', id: 'WRK-2025-00124', nextStep: 'Revisar disponibilidad', owner: 'Jason Meme', priority: 'medium', reason: 'La entrevista necesita disponibilidad revisada', reference: 'Entrevista de trabajador', status: 'pending', title: 'Completar entrevista pendiente' },
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

export function WorkQueues() {
  const { language } = useLanguage();
  const copy = language === 'es' ? spanishQueues : englishQueues;
  const [filter, setFilter] = useState<QueueFilter>('all');
  const visibleItems = useMemo(
    () => copy.items.filter((item) => filter === 'all' || item.category === filter),
    [copy.items, filter],
  );

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
        {copy.summaryItems.map((item) => (
          <div className="queue-summary-card" key={item.label}>
            <span aria-hidden="true" className="dashboard-icon">
              <IconSymbol name={item.icon} />
            </span>
            <strong>{item.value}</strong>
            <span>{item.label}</span>
          </div>
        ))}
      </div>

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
