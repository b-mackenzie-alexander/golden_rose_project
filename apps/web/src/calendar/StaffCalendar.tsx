import { type SyntheticEvent, useMemo, useState } from 'react';

import { IconSymbol } from '../dashboard/artwork';
import type { IconName } from '../dashboard/artwork';
import { useLanguage } from '../i18n/LanguageProvider';

type CalendarEventKind = 'employer' | 'focus' | 'interview' | 'review' | 'staff';
type CalendarEventScope = 'company' | 'personal' | 'system';

type CalendarEvent = {
  accent: 'danger' | 'info' | 'success' | 'warning';
  assignee: string;
  dayId: string;
  duration: string;
  id: string;
  kind: CalendarEventKind;
  meta: string;
  scope: CalendarEventScope;
  sortMinutes: number;
  time: string;
  title: string;
};

type CalendarDay = {
  date: string;
  id: string;
  label: string;
  shortLabel: string;
};

type CalendarCopy = {
  addEvent: string;
  agendaHeading: string;
  assigneeLabel: string;
  calendarHeading: string;
  cancelEdit: string;
  companyCalendar: string;
  dayView: string;
  detailsLabel: string;
  durationLabel: string;
  editEvent: string;
  eventAdded: string;
  eventRemoved: string;
  eventUpdated: string;
  events: CalendarEvent[];
  openSlots: string;
  personalCalendar: string;
  removeEvent: string;
  removeRequiresPermission: string;
  saveEvent: string;
  selectedDay: string;
  scopeLabel: string;
  subtitle: string;
  summaryItems: Array<{ icon: IconName; label: string; value: string }>;
  thisWeek: string;
  timeLabel: string;
  titleLabel: string;
  updateEvent: string;
  weekDays: CalendarDay[];
  weekRange: string;
  weekView: string;
};

const englishCalendar: CalendarCopy = {
  addEvent: 'Add event',
  agendaHeading: "Today's agenda",
  assigneeLabel: 'Assigned to',
  calendarHeading: 'Calendar',
  cancelEdit: 'Cancel edit',
  companyCalendar: 'Company calendar',
  dayView: 'Day',
  detailsLabel: 'Details',
  durationLabel: 'Duration',
  editEvent: 'Edit event',
  eventAdded: 'Event added',
  eventRemoved: 'Event removed',
  eventUpdated: 'Event updated',
  events: [
    { accent: 'danger', assignee: 'Mariela Torres', dayId: 'mon', duration: '30 min', id: 'seed-mon-team', kind: 'staff', meta: 'Staff meeting', scope: 'company', sortMinutes: 540, time: '9:00 AM', title: 'Team check-in' },
    { accent: 'warning', assignee: 'Carlos Ramirez', dayId: 'mon', duration: '30 min', id: 'seed-mon-restaurant', kind: 'employer', meta: 'Employer follow-up', scope: 'company', sortMinutes: 630, time: '10:30 AM', title: 'Call Restaurante La Esperanza' },
    { accent: 'success', assignee: 'Ana Torres', dayId: 'mon', duration: '45 min', id: 'seed-mon-ana', kind: 'interview', meta: 'Worker registration', scope: 'company', sortMinutes: 720, time: '12:00 PM', title: 'Interview with Ana Quispe' },
    { accent: 'info', assignee: 'Operations', dayId: 'mon', duration: '45 min', id: 'seed-mon-review', kind: 'review', meta: 'Queue review', scope: 'company', sortMinutes: 840, time: '2:00 PM', title: 'Review pending intakes' },
    { accent: 'success', assignee: 'Sofia Diaz', dayId: 'mon', duration: '30 min', id: 'seed-mon-maria', kind: 'employer', meta: 'Document check', scope: 'company', sortMinutes: 960, time: '4:00 PM', title: 'Follow-up with Maria Lopez' },
    { accent: 'warning', assignee: 'Carlos Ramirez', dayId: 'tue', duration: '30 min', id: 'seed-tue-bright', kind: 'employer', meta: 'Employer intake', scope: 'company', sortMinutes: 600, time: '10:00 AM', title: 'Bright Horizons staffing call' },
    { accent: 'success', assignee: 'Mariela Torres', dayId: 'tue', duration: '45 min', id: 'seed-tue-carlos', kind: 'interview', meta: 'Worker interview', scope: 'company', sortMinutes: 810, time: '1:30 PM', title: 'Meet Carlos Mendoza' },
    { accent: 'info', assignee: 'Operations', dayId: 'wed', duration: '60 min', id: 'seed-wed-focus', kind: 'focus', meta: 'Focus block', scope: 'personal', sortMinutes: 570, time: '9:30 AM', title: 'Worker intake review block' },
    { accent: 'warning', assignee: 'Sofia Diaz', dayId: 'thu', duration: '30 min', id: 'seed-thu-clean', kind: 'employer', meta: 'Follow-up', scope: 'company', sortMinutes: 660, time: '11:00 AM', title: 'Clean Homes LLC confirmation' },
    { accent: 'success', assignee: 'Ana Torres', dayId: 'fri', duration: '45 min', id: 'seed-fri-jason', kind: 'interview', meta: 'Interview', scope: 'company', sortMinutes: 840, time: '2:00 PM', title: 'Interview with Jason Meme' },
  ],
  openSlots: 'Open slots',
  personalCalendar: 'My calendar',
  removeEvent: 'Remove event',
  removeRequiresPermission: 'Company calendar permission required',
  saveEvent: 'Save event',
  selectedDay: 'Selected day',
  scopeLabel: 'Calendar',
  subtitle: 'Today, interviews, follow-ups, and protected focus time.',
  summaryItems: [
    { icon: 'calendar', label: 'Scheduled events', value: '10' },
    { icon: 'worker', label: 'Interviews', value: '3' },
    { icon: 'building', label: 'Employer follow-ups', value: '3' },
  ],
  thisWeek: 'This week',
  timeLabel: 'Time',
  titleLabel: 'Title',
  updateEvent: 'Update event',
  weekDays: [
    { date: 'Jan 27', id: 'mon', label: 'Monday', shortLabel: 'Mon' },
    { date: 'Jan 28', id: 'tue', label: 'Tuesday', shortLabel: 'Tue' },
    { date: 'Jan 29', id: 'wed', label: 'Wednesday', shortLabel: 'Wed' },
    { date: 'Jan 30', id: 'thu', label: 'Thursday', shortLabel: 'Thu' },
    { date: 'Jan 31', id: 'fri', label: 'Friday', shortLabel: 'Fri' },
    { date: 'Feb 1', id: 'sat', label: 'Saturday', shortLabel: 'Sat' },
    { date: 'Feb 2', id: 'sun', label: 'Sunday', shortLabel: 'Sun' },
  ],
  weekRange: 'January 27 - February 2, 2025',
  weekView: 'Week',
};

const spanishCalendar: CalendarCopy = {
  addEvent: 'Agregar evento',
  agendaHeading: 'Agenda de hoy',
  assigneeLabel: 'Asignado a',
  calendarHeading: 'Calendario',
  cancelEdit: 'Cancelar edicion',
  companyCalendar: 'Calendario de la compania',
  dayView: 'Dia',
  detailsLabel: 'Detalles',
  durationLabel: 'Duracion',
  editEvent: 'Editar evento',
  eventAdded: 'Evento agregado',
  eventRemoved: 'Evento eliminado',
  eventUpdated: 'Evento actualizado',
  events: [
    { accent: 'danger', assignee: 'Mariela Torres', dayId: 'mon', duration: '30 min', id: 'seed-mon-team', kind: 'staff', meta: 'Reunion del equipo', scope: 'company', sortMinutes: 540, time: '9:00 a. m.', title: 'Revision diaria' },
    { accent: 'warning', assignee: 'Carlos Ramirez', dayId: 'mon', duration: '30 min', id: 'seed-mon-restaurant', kind: 'employer', meta: 'Seguimiento de empleador', scope: 'company', sortMinutes: 630, time: '10:30 a. m.', title: 'Llamada con Restaurante La Esperanza' },
    { accent: 'success', assignee: 'Ana Torres', dayId: 'mon', duration: '45 min', id: 'seed-mon-ana', kind: 'interview', meta: 'Registro de trabajador', scope: 'company', sortMinutes: 720, time: '12:00 p. m.', title: 'Entrevista con Ana Quispe' },
    { accent: 'info', assignee: 'Operaciones', dayId: 'mon', duration: '45 min', id: 'seed-mon-review', kind: 'review', meta: 'Revision de cola', scope: 'company', sortMinutes: 840, time: '2:00 p. m.', title: 'Revisar registros pendientes' },
    { accent: 'success', assignee: 'Sofia Diaz', dayId: 'mon', duration: '30 min', id: 'seed-mon-maria', kind: 'employer', meta: 'Verificar documentos', scope: 'company', sortMinutes: 960, time: '4:00 p. m.', title: 'Seguimiento con Maria Lopez' },
    { accent: 'warning', assignee: 'Carlos Ramirez', dayId: 'tue', duration: '30 min', id: 'seed-tue-bright', kind: 'employer', meta: 'Registro de empleador', scope: 'company', sortMinutes: 600, time: '10:00 a. m.', title: 'Llamada con Bright Horizons' },
    { accent: 'success', assignee: 'Mariela Torres', dayId: 'tue', duration: '45 min', id: 'seed-tue-carlos', kind: 'interview', meta: 'Entrevista de trabajador', scope: 'company', sortMinutes: 810, time: '1:30 p. m.', title: 'Entrevista con Carlos Mendoza' },
    { accent: 'info', assignee: 'Operaciones', dayId: 'wed', duration: '60 min', id: 'seed-wed-focus', kind: 'focus', meta: 'Bloque de enfoque', scope: 'personal', sortMinutes: 570, time: '9:30 a. m.', title: 'Revision de registros de trabajadores' },
    { accent: 'warning', assignee: 'Sofia Diaz', dayId: 'thu', duration: '30 min', id: 'seed-thu-clean', kind: 'employer', meta: 'Seguimiento', scope: 'company', sortMinutes: 660, time: '11:00 a. m.', title: 'Confirmacion de Clean Homes LLC' },
    { accent: 'success', assignee: 'Ana Torres', dayId: 'fri', duration: '45 min', id: 'seed-fri-jason', kind: 'interview', meta: 'Entrevista', scope: 'company', sortMinutes: 840, time: '2:00 p. m.', title: 'Entrevista con Jason Meme' },
  ],
  openSlots: 'Espacios abiertos',
  personalCalendar: 'Mi calendario',
  removeEvent: 'Eliminar evento',
  removeRequiresPermission: 'Requiere permiso del calendario de la compania',
  saveEvent: 'Guardar evento',
  selectedDay: 'Dia seleccionado',
  scopeLabel: 'Calendario',
  subtitle: 'Hoy, entrevistas, seguimientos y tiempo protegido de enfoque.',
  summaryItems: [
    { icon: 'calendar', label: 'Eventos programados', value: '10' },
    { icon: 'worker', label: 'Entrevistas', value: '3' },
    { icon: 'building', label: 'Seguimientos', value: '3' },
  ],
  thisWeek: 'Esta semana',
  timeLabel: 'Hora',
  titleLabel: 'Titulo',
  updateEvent: 'Actualizar evento',
  weekDays: [
    { date: '27 ene.', id: 'mon', label: 'Lunes', shortLabel: 'Lun' },
    { date: '28 ene.', id: 'tue', label: 'Martes', shortLabel: 'Mar' },
    { date: '29 ene.', id: 'wed', label: 'Miercoles', shortLabel: 'Mie' },
    { date: '30 ene.', id: 'thu', label: 'Jueves', shortLabel: 'Jue' },
    { date: '31 ene.', id: 'fri', label: 'Viernes', shortLabel: 'Vie' },
    { date: '1 feb.', id: 'sat', label: 'Sabado', shortLabel: 'Sab' },
    { date: '2 feb.', id: 'sun', label: 'Domingo', shortLabel: 'Dom' },
  ],
  weekRange: '27 de enero - 2 de febrero de 2025',
  weekView: 'Semana',
};

const eventIcons: Record<CalendarEventKind, IconName> = {
  employer: 'building',
  focus: 'queue',
  interview: 'worker',
  review: 'document',
  staff: 'schedule',
};

type StoredCalendarEvent = {
  assignee: string;
  dayId: string;
  duration: string;
  id: string;
  meta: string;
  scope: Exclude<CalendarEventScope, 'system'>;
  time24: string;
  title: string;
};

type CalendarFormState = {
  assignee: string;
  duration: string;
  meta: string;
  scope: Exclude<CalendarEventScope, 'system'>;
  time24: string;
  title: string;
};

const manualEventsStorageKey = 'golden-rose.staff-calendar.manual-events.v1';
const canManageCompanyCalendarEvents = false;

const defaultForm: CalendarFormState = {
  assignee: '',
  duration: '30 min',
  meta: '',
  scope: 'personal',
  time24: '09:00',
  title: '',
};

function formatTime(value: string, language: 'en' | 'es') {
  const [hour = '0', minute = '0'] = value.split(':');
  const date = new Date(2025, 0, 27, Number(hour), Number(minute));
  return new Intl.DateTimeFormat(language === 'es' ? 'es-US' : 'en-US', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(date);
}

function minutesFromTime(value: string) {
  const [hour = '0', minute = '0'] = value.split(':');
  return Number(hour) * 60 + Number(minute);
}

function readStoredEvents(): StoredCalendarEvent[] {
  if (typeof window === 'undefined') return [];
  try {
    const parsed = JSON.parse(window.localStorage.getItem(manualEventsStorageKey) ?? '[]') as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((event): event is StoredCalendarEvent => (
      typeof event === 'object' &&
      event !== null &&
      typeof (event as StoredCalendarEvent).id === 'string' &&
      typeof (event as StoredCalendarEvent).dayId === 'string' &&
      typeof (event as StoredCalendarEvent).time24 === 'string' &&
      typeof (event as StoredCalendarEvent).title === 'string' &&
      ((event as StoredCalendarEvent).scope === 'personal' || (event as StoredCalendarEvent).scope === 'company')
    ));
  } catch {
    return [];
  }
}

function writeStoredEvents(events: StoredCalendarEvent[]) {
  window.localStorage.setItem(manualEventsStorageKey, JSON.stringify(events));
}

function toCalendarEvent(event: StoredCalendarEvent, language: 'en' | 'es'): CalendarEvent {
  return {
    accent: event.scope === 'company' ? 'warning' : 'info',
    assignee: event.assignee || (event.scope === 'company' ? 'Operations' : 'Me'),
    dayId: event.dayId,
    duration: event.duration,
    id: event.id,
    kind: event.scope === 'company' ? 'staff' : 'focus',
    meta: event.meta || (event.scope === 'company'
      ? language === 'es' ? 'Evento de compania' : 'Company event'
      : language === 'es' ? 'Evento personal' : 'Personal event'),
    scope: event.scope,
    sortMinutes: minutesFromTime(event.time24),
    time: formatTime(event.time24, language),
    title: event.title,
  };
}

function canRemoveEvent(event: CalendarEvent) {
  return event.id.startsWith('manual-') && (event.scope === 'personal' || canManageCompanyCalendarEvents);
}

function canEditEvent(event: CalendarEvent) {
  return event.id.startsWith('manual-') && event.scope === 'personal';
}

export function StaffCalendar() {
  const { language } = useLanguage();
  const copy = language === 'es' ? spanishCalendar : englishCalendar;
  const [selectedDayId, setSelectedDayId] = useState('mon');
  const [manualEvents, setManualEvents] = useState<StoredCalendarEvent[]>(() => readStoredEvents());
  const [form, setForm] = useState<CalendarFormState>(defaultForm);
  const [editingEventId, setEditingEventId] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState('');
  const fallbackDay = copy.weekDays[0];
  if (fallbackDay === undefined) {
    throw new Error('Staff calendar requires at least one day.');
  }
  const selectedDay = copy.weekDays.find((day) => day.id === selectedDayId) ?? fallbackDay;
  const events = useMemo(
    () => [
      ...copy.events,
      ...manualEvents.map((event) => toCalendarEvent(event, language)),
    ].sort((left, right) => left.sortMinutes - right.sortMinutes || left.title.localeCompare(right.title)),
    [copy.events, language, manualEvents],
  );
  const selectedEvents = useMemo(
    () => events.filter((event) => event.dayId === selectedDay.id),
    [events, selectedDay.id],
  );
  const eventsByDay = useMemo(() => new Map(copy.weekDays.map((day) => [
    day.id,
    events.filter((event) => event.dayId === day.id),
  ])), [copy.weekDays, events]);
  const summaryItems = useMemo(() => {
    const interviews = events.filter((event) => event.kind === 'interview').length;
    const followUps = events.filter((event) => event.kind === 'employer').length;
    return copy.summaryItems.map((item, index) => ({
      ...item,
      value: index === 0 ? String(events.length) : index === 1 ? String(interviews) : index === 2 ? String(followUps) : item.value,
    }));
  }, [copy.summaryItems, events]);
  function saveManualEvent(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    const title = form.title.trim();
    if (!title) return;
    if (editingEventId !== null) {
      const nextEvents = manualEvents.map((storedEvent) => storedEvent.id === editingEventId
        ? {
            ...storedEvent,
            assignee: form.assignee.trim(),
            dayId: selectedDay.id,
            duration: form.duration,
            meta: form.meta.trim(),
            scope: form.scope,
            time24: form.time24,
            title,
          }
        : storedEvent);
      setManualEvents(nextEvents);
      writeStoredEvents(nextEvents);
      setEditingEventId(null);
      setStatusMessage(copy.eventUpdated);
      setForm({ ...defaultForm, scope: form.scope });
      return;
    }
    const nextEvent: StoredCalendarEvent = {
      assignee: form.assignee.trim(),
      dayId: selectedDay.id,
      duration: form.duration,
      id: `manual-${String(Date.now())}-${Math.random().toString(36).slice(2)}`,
      meta: form.meta.trim(),
      scope: form.scope,
      time24: form.time24,
      title,
    };
    const nextEvents = [...manualEvents, nextEvent];
    setManualEvents(nextEvents);
    writeStoredEvents(nextEvents);
    setStatusMessage(copy.eventAdded);
    setForm({ ...defaultForm, scope: form.scope });
  }
  function editManualEvent(event: CalendarEvent) {
    if (!canEditEvent(event)) return;
    const storedEvent = manualEvents.find((candidate) => candidate.id === event.id);
    if (!storedEvent) return;
    setSelectedDayId(storedEvent.dayId);
    setEditingEventId(storedEvent.id);
    setForm({
      assignee: storedEvent.assignee,
      duration: storedEvent.duration,
      meta: storedEvent.meta,
      scope: storedEvent.scope,
      time24: storedEvent.time24,
      title: storedEvent.title,
    });
  }
  function removeManualEvent(event: CalendarEvent) {
    if (!canRemoveEvent(event)) return;
    const nextEvents = manualEvents.filter((storedEvent) => storedEvent.id !== event.id);
    setManualEvents(nextEvents);
    writeStoredEvents(nextEvents);
    setStatusMessage(copy.eventRemoved);
    if (editingEventId === event.id) {
      setEditingEventId(null);
      setForm(defaultForm);
    }
  }
  function cancelEdit() {
    setEditingEventId(null);
    setForm(defaultForm);
  }

  return (
    <section aria-labelledby="calendar-heading" className="staff-calendar-page">
      <div className="staff-calendar-hero">
        <div>
          <p className="staff-calendar-eyebrow">{copy.thisWeek}</p>
          <h2 id="calendar-heading">{copy.calendarHeading}</h2>
          <p>{copy.subtitle}</p>
        </div>
        <div className="calendar-toolbar" aria-label={language === 'es' ? 'Controles del calendario' : 'Calendar controls'}>
          <span>{copy.weekRange}</span>
        </div>
      </div>

      <div className="calendar-summary-grid" aria-label={language === 'es' ? 'Resumen del calendario' : 'Calendar summary'}>
        {summaryItems.map((item) => (
          <div className="calendar-summary-card" key={item.label}>
            <span aria-hidden="true" className="dashboard-icon">
              <IconSymbol name={item.icon} />
            </span>
            <strong>{item.value}</strong>
            <span>{item.label}</span>
          </div>
        ))}
      </div>

      <div className="calendar-layout">
        <section className="calendar-panel calendar-week-panel" aria-labelledby="calendar-week-heading">
          <div className="calendar-panel-header">
            <h3 id="calendar-week-heading">{copy.weekView}</h3>
            <div className="calendar-view-toggle" aria-label={language === 'es' ? 'Vista del calendario' : 'Calendar view'}>
              <button aria-pressed="true" className="focus-ring" type="button">{copy.weekView}</button>
              <button aria-pressed="false" className="focus-ring" type="button">{copy.dayView}</button>
            </div>
          </div>

          <div className="calendar-day-strip">
            {copy.weekDays.map((day) => {
              const eventCount = eventsByDay.get(day.id)?.length ?? 0;
              const isSelected = day.id === selectedDay.id;
              return (
                <button
                  aria-pressed={isSelected}
                  className="calendar-day-button focus-ring"
                  data-selected={isSelected}
                  key={day.id}
                  type="button"
                  onClick={() => {
                    setSelectedDayId(day.id);
                  }}
                >
                  <span>{day.shortLabel}</span>
                  <strong>{day.date}</strong>
                  <small>{eventCount}</small>
                </button>
              );
            })}
          </div>

          <div className="calendar-timeline" aria-label={`${copy.selectedDay}: ${selectedDay.label}`}>
            {selectedEvents.map((event) => (
              <article className="calendar-event" data-accent={event.accent} key={event.id}>
                <time>{event.time}</time>
                <span aria-hidden="true" className="calendar-event-icon">
                  <IconSymbol name={eventIcons[event.kind]} />
                </span>
                <div>
                  <h4>{event.title}</h4>
                  <p>{event.meta}</p>
                  <dl>
                    <div>
                      <dt>{copy.scopeLabel}</dt>
                      <dd>{event.scope === 'company' ? copy.companyCalendar : event.scope === 'personal' ? copy.personalCalendar : copy.companyCalendar}</dd>
                    </div>
                    <div>
                      <dt>{copy.assigneeLabel}</dt>
                      <dd>{event.assignee}</dd>
                    </div>
                    <div>
                      <dt>{language === 'es' ? 'Duracion' : 'Duration'}</dt>
                      <dd>{event.duration}</dd>
                    </div>
                  </dl>
                  {event.id.startsWith('manual-') ? (
                    <div className="calendar-event-actions">
                      <button
                        className="focus-ring"
                        disabled={!canEditEvent(event)}
                        type="button"
                        onClick={() => {
                          editManualEvent(event);
                        }}
                      >
                        {canEditEvent(event) ? copy.editEvent : copy.removeRequiresPermission}
                      </button>
                      <button
                        className="focus-ring"
                        disabled={!canRemoveEvent(event)}
                        type="button"
                        onClick={() => {
                          removeManualEvent(event);
                        }}
                      >
                        {canRemoveEvent(event) ? copy.removeEvent : copy.removeRequiresPermission}
                      </button>
                    </div>
                  ) : null}
                </div>
              </article>
            ))}
            {selectedEvents.length === 0 ? (
              <div className="calendar-empty">
                <strong>{copy.openSlots}</strong>
              </div>
            ) : null}
          </div>
        </section>

        <aside className="calendar-panel calendar-agenda-panel" aria-labelledby="calendar-agenda-heading">
          <div className="calendar-panel-header">
            <h3 id="calendar-agenda-heading">{copy.agendaHeading}</h3>
            <span>{selectedDay.label}</span>
          </div>
          <ol className="calendar-agenda-list">
            {selectedEvents.map((event) => (
              <li data-accent={event.accent} key={event.id}>
                <time>{event.time}</time>
                <div>
                  <strong>{event.title}</strong>
                  <span>{event.meta}</span>
                </div>
              </li>
            ))}
          </ol>
          {statusMessage ? <p className="calendar-status" role="status">{statusMessage}</p> : null}
          <form className="calendar-event-form" onSubmit={saveManualEvent}>
            <div className="calendar-event-form-header">
              <h4>{editingEventId ? copy.editEvent : copy.addEvent}</h4>
              {editingEventId ? (
                <button className="focus-ring" type="button" onClick={cancelEdit}>
                  {copy.cancelEdit}
                </button>
              ) : null}
            </div>
            <label>
              <span>{copy.titleLabel}</span>
              <input
                required
                type="text"
                value={form.title}
                onChange={(event) => {
                  setForm((current) => ({ ...current, title: event.target.value }));
                }}
              />
            </label>
            <div className="calendar-form-row">
              <label>
                <span>{copy.timeLabel}</span>
                <input
                  type="time"
                  value={form.time24}
                  onChange={(event) => {
                    setForm((current) => ({ ...current, time24: event.target.value }));
                  }}
                />
              </label>
              <label>
                <span>{copy.durationLabel}</span>
                <select
                  value={form.duration}
                  onChange={(event) => {
                    setForm((current) => ({ ...current, duration: event.target.value }));
                  }}
                >
                  <option value="15 min">15 min</option>
                  <option value="30 min">30 min</option>
                  <option value="45 min">45 min</option>
                  <option value="60 min">60 min</option>
                  <option value="90 min">90 min</option>
                </select>
              </label>
            </div>
            <label>
              <span>{copy.scopeLabel}</span>
              <select
                value={form.scope}
                onChange={(event) => {
                  setForm((current) => ({ ...current, scope: event.target.value as CalendarFormState['scope'] }));
                }}
              >
                <option value="personal">{copy.personalCalendar}</option>
                <option value="company">{copy.companyCalendar}</option>
              </select>
            </label>
            <label>
              <span>{copy.assigneeLabel}</span>
              <input
                type="text"
                value={form.assignee}
                onChange={(event) => {
                  setForm((current) => ({ ...current, assignee: event.target.value }));
                }}
              />
            </label>
            <label>
              <span>{copy.detailsLabel}</span>
              <textarea
                rows={3}
                value={form.meta}
                onChange={(event) => {
                  setForm((current) => ({ ...current, meta: event.target.value }));
                }}
              />
            </label>
            <button className="focus-ring" type="submit">{editingEventId ? copy.updateEvent : copy.saveEvent}</button>
          </form>
        </aside>
      </div>
    </section>
  );
}
