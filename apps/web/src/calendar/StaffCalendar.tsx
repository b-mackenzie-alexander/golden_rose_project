import { type SyntheticEvent, useEffect, useMemo, useState } from 'react';

import { disposeExternalCalendarCandidate, getCalendarImportSummary, type CalendarImportDisposition, type CalendarImportFailureKind, type CalendarImportSummary, type ExternalCalendarImport } from '../api/calendarImportClient';
import { getOperationsProjection, type OperationsCalendarSummary, type OperationsProjectionFailureKind, type OperationsShiftItem } from '../api/operationsProjectionClient';
import { getStaticOperationalFallbackPolicy, staticOperationalFallbackNotice, staticOperationalFallbacksAllowed, type StaticOperationalFallbackPolicy } from '../api/runtimeEnvironmentClient';
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

type ProjectionStatus = 'loading' | 'ready' | OperationsProjectionFailureKind;
type CalendarImportStatus = 'loading' | 'ready' | CalendarImportFailureKind;

type CalendarDay = {
  date: string;
  dateValue: Date;
  dayOfMonth: string;
  id: string;
  isToday: boolean;
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
  googleCandidateLabel: string;
  googleConfigRequired: string;
  googleConnect: string;
  googleHeading: string;
  googleIgnore: string;
  googleIgnored: string;
  googleMarkExisting: string;
  googleMarkedExisting: string;
  googleNoCandidates: string;
  googleStale: string;
  googleSubtitle: string;
  googleUnavailable: string;
  googleUnverified: string;
  monthView: string;
  nextMonth: string;
  openSlots: string;
  personalCalendar: string;
  previousMonth: string;
  projectedShifts: string;
  projectedWorkerSlots: string;
  projectionSeparate: string;
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
  today: string;
  updateEvent: string;
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
    { accent: 'success', assignee: 'Ana Torres', dayId: 'fri', duration: '45 min', id: 'seed-fri-carlos', kind: 'interview', meta: 'Interview', scope: 'company', sortMinutes: 840, time: '2:00 PM', title: 'Interview with Carlos Mendoza' },
  ],
  googleCandidateLabel: 'Google candidate',
  googleConfigRequired: 'Google Calendar connection requires approved OAuth configuration before staff can import live events.',
  googleConnect: 'Connect Google Calendar',
  googleHeading: 'Google Calendar migration',
  googleIgnore: 'Ignore',
  googleIgnored: 'Candidate ignored',
  googleMarkExisting: 'Already in Golden Rose',
  googleMarkedExisting: 'Marked as existing',
  googleNoCandidates: 'No Google Calendar candidates waiting for review.',
  googleStale: 'This candidate changed. Refresh the calendar before deciding.',
  googleSubtitle: 'Imported events stay outside the dashboard calendar until staff reviews them.',
  googleUnavailable: 'Google Calendar import candidates are unavailable right now.',
  googleUnverified: 'External, unverified',
  monthView: 'Month',
  nextMonth: 'Next month',
  openSlots: 'Open slots',
  personalCalendar: 'My calendar',
  previousMonth: 'Previous month',
  projectedShifts: 'Projected shifts',
  projectedWorkerSlots: 'Projected worker slots',
  projectionSeparate: 'Request-derived shifts only; personal events stay separate.',
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
  today: 'Today',
  updateEvent: 'Update event',
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
    { accent: 'success', assignee: 'Ana Torres', dayId: 'fri', duration: '45 min', id: 'seed-fri-carlos', kind: 'interview', meta: 'Entrevista', scope: 'company', sortMinutes: 840, time: '2:00 p. m.', title: 'Entrevista con Carlos Mendoza' },
  ],
  googleCandidateLabel: 'Candidato de Google',
  googleConfigRequired: 'La conexion con Google Calendar requiere configuracion OAuth aprobada antes de importar eventos reales.',
  googleConnect: 'Conectar Google Calendar',
  googleHeading: 'Migracion de Google Calendar',
  googleIgnore: 'Ignorar',
  googleIgnored: 'Candidato ignorado',
  googleMarkExisting: 'Ya esta en Golden Rose',
  googleMarkedExisting: 'Marcado como existente',
  googleNoCandidates: 'No hay candidatos de Google Calendar esperando revision.',
  googleStale: 'Este candidato cambio. Actualiza el calendario antes de decidir.',
  googleSubtitle: 'Los eventos importados quedan fuera del calendario hasta que el personal los revise.',
  googleUnavailable: 'Los candidatos de Google Calendar no estan disponibles ahora.',
  googleUnverified: 'Externo, no verificado',
  monthView: 'Mes',
  nextMonth: 'Mes siguiente',
  openSlots: 'Espacios abiertos',
  personalCalendar: 'Mi calendario',
  previousMonth: 'Mes anterior',
  projectedShifts: 'Turnos proyectados',
  projectedWorkerSlots: 'Cupos proyectados',
  projectionSeparate: 'Solo turnos derivados de solicitudes; los eventos personales siguen separados.',
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
  today: 'Hoy',
  updateEvent: 'Actualizar evento',
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

const legacyWeekdayIds = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'] as const;

function startOfLocalDay(value: Date) {
  return new Date(value.getFullYear(), value.getMonth(), value.getDate());
}

function addDays(value: Date, days: number) {
  const next = startOfLocalDay(value);
  next.setDate(next.getDate() + days);
  return next;
}

function dateId(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${String(year)}-${month}-${day}`;
}

function formatDateRange(start: Date, end: Date, language: 'en' | 'es') {
  const locale = language === 'es' ? 'es-US' : 'en-US';
  const sameYear = start.getFullYear() === end.getFullYear();
  const sameMonth = sameYear && start.getMonth() === end.getMonth();
  if (sameMonth) {
    const month = new Intl.DateTimeFormat(locale, { month: 'long' }).format(start);
    return language === 'es'
      ? `${String(start.getDate())} - ${String(end.getDate())} de ${month} de ${String(start.getFullYear())}`
      : `${month} ${String(start.getDate())} - ${String(end.getDate())}, ${String(start.getFullYear())}`;
  }
  return `${new Intl.DateTimeFormat(locale, { month: 'long', day: 'numeric', year: sameYear ? undefined : 'numeric' }).format(start)} - ${new Intl.DateTimeFormat(locale, { month: 'long', day: 'numeric', year: 'numeric' }).format(end)}`;
}

function buildCalendarDay(value: Date, today: Date, language: 'en' | 'es'): CalendarDay {
  const locale = language === 'es' ? 'es-US' : 'en-US';
  return {
    date: new Intl.DateTimeFormat(locale, { month: 'short', day: 'numeric' }).format(value),
    dateValue: value,
    dayOfMonth: String(value.getDate()),
    id: dateId(value),
    isToday: dateId(value) === dateId(today),
    label: new Intl.DateTimeFormat(locale, { weekday: 'long', month: 'long', day: 'numeric' }).format(value),
    shortLabel: new Intl.DateTimeFormat(locale, { weekday: 'short' }).format(value),
  };
}

function buildWeekDays(today: Date, language: 'en' | 'es') {
  return Array.from({ length: 7 }, (_, index) => buildCalendarDay(addDays(today, index), today, language));
}

function buildMonthDays(monthDate: Date, today: Date, language: 'en' | 'es') {
  const first = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
  const daysInMonth = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0).getDate();
  return Array.from({ length: daysInMonth }, (_, index) => buildCalendarDay(addDays(first, index), today, language));
}

function buildWeekdayHeadings(language: 'en' | 'es') {
  const sunday = new Date(2026, 0, 4);
  return Array.from({ length: 7 }, (_, index) => new Intl.DateTimeFormat(language === 'es' ? 'es-US' : 'en-US', {
    weekday: 'short',
  }).format(addDays(sunday, index)));
}

function formatMonthHeading(value: Date, language: 'en' | 'es') {
  return new Intl.DateTimeFormat(language === 'es' ? 'es-US' : 'en-US', {
    month: 'long',
    year: 'numeric',
  }).format(value);
}

function normalizeCalendarDayId(dayId: string, weekDays: CalendarDay[]) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(dayId)) return dayId;
  const legacyIndex = legacyWeekdayIds.findIndex((weekday) => weekday === dayId);
  return weekDays.find((day) => day.dateValue.getDay() === legacyIndex)?.id ?? dayId;
}

function formatTime(value: string, language: 'en' | 'es') {
  const [hour = '0', minute = '0'] = value.split(':');
  const date = new Date(2026, 0, 1, Number(hour), Number(minute));
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

function toCalendarEvent(event: StoredCalendarEvent, language: 'en' | 'es', weekDays: CalendarDay[]): CalendarEvent {
  return {
    accent: event.scope === 'company' ? 'warning' : 'info',
    assignee: event.assignee || (event.scope === 'company' ? 'Operations' : 'Me'),
    dayId: normalizeCalendarDayId(event.dayId, weekDays),
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

function dayIdFromInstant(value: string): string | null {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return dateId(date);
}

function durationLabel(startValue: string, endValue: string, language: 'en' | 'es') {
  const start = new Date(startValue);
  const end = new Date(endValue);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end <= start) {
    return language === 'es' ? 'Horario registrado' : 'Recorded time';
  }
  const minutes = Math.round((end.getTime() - start.getTime()) / 60_000);
  return minutes >= 60 && minutes % 60 === 0
    ? `${String(minutes / 60)} ${language === 'es' ? 'h' : 'hr'}`
    : `${String(minutes)} min`;
}

function toShiftEvent(item: OperationsShiftItem, language: 'en' | 'es'): CalendarEvent | null {
  const dayId = dayIdFromInstant(item.startsAt);
  const starts = new Date(item.startsAt);
  if (!dayId || Number.isNaN(starts.getTime())) return null;
  return {
    accent: item.shiftStatus === 'pending_review' ? 'warning' : 'info',
    assignee: language === 'es' ? 'Operaciones' : 'Operations',
    dayId,
    duration: durationLabel(item.startsAt, item.endsAt, language),
    id: `shift-${item.shiftNeedId}`,
    kind: 'employer',
    meta: item.employerName,
    scope: 'system',
    sortMinutes: starts.getHours() * 60 + starts.getMinutes(),
    time: starts.toLocaleTimeString(language === 'es' ? 'es-US' : 'en-US', {
      hour: 'numeric',
      minute: '2-digit',
    }),
    title: `${item.roleTitle} (${String(item.workerCount)})`,
  };
}

function formatCalendarImportWindow(candidate: ExternalCalendarImport, language: 'en' | 'es') {
  const startsAt = new Date(candidate.startsAt);
  const endsAt = new Date(candidate.endsAt);
  if (Number.isNaN(startsAt.getTime()) || Number.isNaN(endsAt.getTime())) {
    return language === 'es' ? 'Horario importado' : 'Imported time';
  }
  const locale = language === 'es' ? 'es-US' : 'en-US';
  const day = new Intl.DateTimeFormat(locale, {
    month: 'short',
    day: 'numeric',
  }).format(startsAt);
  const start = startsAt.toLocaleTimeString(locale, { hour: 'numeric', minute: '2-digit' });
  const end = endsAt.toLocaleTimeString(locale, { hour: 'numeric', minute: '2-digit' });
  return `${day}, ${start} - ${end}`;
}

function makeCalendarImportCommandId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `00000000-0000-4000-8000-${Math.random().toString(16).slice(2, 14).padEnd(12, '0')}`;
}

function canRemoveEvent(event: CalendarEvent) {
  return event.id.startsWith('manual-') && (event.scope === 'personal' || canManageCompanyCalendarEvents);
}

function canEditEvent(event: CalendarEvent) {
  return event.id.startsWith('manual-') && event.scope === 'personal';
}

function isProjectionFailure(status: ProjectionStatus) {
  return status !== 'loading' && status !== 'ready';
}

function projectionNotice(status: ProjectionStatus, language: 'en' | 'es', fallbackPolicy: StaticOperationalFallbackPolicy) {
  if (!isProjectionFailure(status)) return null;
  const fallbackNotice = staticOperationalFallbackNotice(fallbackPolicy, language);
  const reason = {
    forbidden: {
      en: 'this account is not authorized to read projected shifts',
      es: 'esta cuenta no tiene autorizacion para leer turnos proyectados',
    },
    validation: {
      en: 'the shift projection response could not be validated',
      es: 'no se pudo validar la respuesta de turnos proyectados',
    },
    unavailable: {
      en: 'the shift projection service is unavailable',
      es: 'el servicio de turnos proyectados no esta disponible',
    },
    unexpected: {
      en: 'the shift projection response was unexpected',
      es: 'la respuesta de turnos proyectados fue inesperada',
    },
  }[status][language];
  const suffix = fallbackNotice === null
    ? language === 'es'
      ? 'Los eventos personales siguen separados; se muestran eventos de respaldo cuando la proyeccion no esta disponible.'
      : 'Personal events remain separate; fallback events are shown while the projection is unavailable.'
    : language === 'es'
      ? `Los eventos personales siguen separados. ${fallbackNotice}`
      : `Personal events remain separate. ${fallbackNotice}`;
  return language === 'es'
    ? `El calendario no pudo leer turnos de solicitudes porque ${reason}. ${suffix}`
    : `The calendar could not read request-derived shifts because ${reason}. ${suffix}`;
}

export function StaffCalendar() {
  const { language } = useLanguage();
  const copy = language === 'es' ? spanishCalendar : englishCalendar;
  const today = useMemo(() => startOfLocalDay(new Date()), []);
  const currentYear = today.getFullYear();
  const [selectedDayId, setSelectedDayId] = useState(() => dateId(today));
  const [visibleMonth, setVisibleMonth] = useState(() => new Date(today.getFullYear(), today.getMonth(), 1));
  const [viewMode, setViewMode] = useState<'week' | 'month'>('week');
  const [manualEvents, setManualEvents] = useState<StoredCalendarEvent[]>(() => readStoredEvents());
  const [shiftEvents, setShiftEvents] = useState<OperationsShiftItem[]>([]);
  const [calendarSummary, setCalendarSummary] = useState<OperationsCalendarSummary | null>(null);
  const [projectionStatus, setProjectionStatus] = useState<ProjectionStatus>('loading');
  const [staticFallbackPolicy, setStaticFallbackPolicy] = useState<StaticOperationalFallbackPolicy>('loading');
  const [calendarImportSummary, setCalendarImportSummary] = useState<CalendarImportSummary | null>(null);
  const [calendarImportStatus, setCalendarImportStatus] = useState<CalendarImportStatus>('loading');
  const [calendarImportMessage, setCalendarImportMessage] = useState('');
  const [busyCalendarImportId, setBusyCalendarImportId] = useState<string | null>(null);
  const [form, setForm] = useState<CalendarFormState>(defaultForm);
  const [editingEventId, setEditingEventId] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState('');
  const weekDays = useMemo(() => buildWeekDays(today, language), [language, today]);
  const monthDays = useMemo(() => buildMonthDays(visibleMonth, today, language), [language, today, visibleMonth]);
  const weekdayHeadings = useMemo(() => buildWeekdayHeadings(language), [language]);
  const monthCells = useMemo(() => {
    const firstDay = monthDays[0];
    const leadingEmptyDays = firstDay?.dateValue.getDay() ?? 0;
    return [
      ...Array.from<null>({ length: leadingEmptyDays }).fill(null),
      ...monthDays,
    ];
  }, [monthDays]);
  const fallbackDay = weekDays[0];
  if (fallbackDay === undefined) {
    throw new Error('Staff calendar requires at least one day.');
  }
  const weekRange = formatDateRange(weekDays[0]?.dateValue ?? today, weekDays[weekDays.length - 1]?.dateValue ?? today, language);
  const monthHeading = formatMonthHeading(visibleMonth, language);
  const canGoPreviousMonth = visibleMonth.getFullYear() > currentYear || visibleMonth.getMonth() > 0;
  const canGoNextMonth = visibleMonth.getFullYear() < currentYear || visibleMonth.getMonth() < 11;
  useEffect(() => {
    let cancelled = false;
    void Promise.all([
      getOperationsProjection().catch(() => ({ ok: false as const, failure: { kind: 'unavailable' as const } })),
      getStaticOperationalFallbackPolicy().catch(() => 'deny' as const),
      getCalendarImportSummary().catch(() => ({ ok: false as const, failure: { kind: 'unavailable' as const } })),
    ])
      .then(([result, fallbackPolicy, importResult]) => {
        if (cancelled) return;
        setShiftEvents(result.ok ? result.value.shiftItems : []);
        setCalendarSummary(result.ok ? result.value.calendarSummary : null);
        setProjectionStatus(result.ok ? 'ready' : result.failure.kind);
        setStaticFallbackPolicy(fallbackPolicy);
        setCalendarImportSummary(importResult.ok ? importResult.value : null);
        setCalendarImportStatus(importResult.ok ? 'ready' : importResult.failure.kind);
      })
      .catch(() => {
        if (cancelled) return;
        setShiftEvents([]);
        setCalendarSummary(null);
        setProjectionStatus('unavailable');
        setStaticFallbackPolicy('deny');
        setCalendarImportSummary(null);
        setCalendarImportStatus('unavailable');
      });
    return () => {
      cancelled = true;
    };
  }, []);
  const allVisibleDays = useMemo(() => {
    const days = new Map<string, CalendarDay>();
    for (const day of weekDays) days.set(day.id, day);
    for (const day of monthDays) days.set(day.id, day);
    return Array.from(days.values()).sort((left, right) => left.dateValue.getTime() - right.dateValue.getTime());
  }, [monthDays, weekDays]);
  const selectedDay = allVisibleDays.find((day) => day.id === selectedDayId) ?? fallbackDay;
  const events = useMemo(
    () => [
      ...(shiftEvents.length
        ? shiftEvents
            .map((event) => toShiftEvent(event, language))
            .filter((event): event is CalendarEvent => event !== null)
        : projectionStatus === 'ready' || !staticOperationalFallbacksAllowed(staticFallbackPolicy)
          ? []
          : copy.events.map((event) => ({ ...event, dayId: normalizeCalendarDayId(event.dayId, weekDays) }))),
      ...manualEvents.map((event) => toCalendarEvent(event, language, weekDays)),
    ].sort((left, right) => left.sortMinutes - right.sortMinutes || left.title.localeCompare(right.title)),
    [copy.events, language, manualEvents, projectionStatus, shiftEvents, staticFallbackPolicy, weekDays],
  );
  const operationsNotice = useMemo(
    () => projectionNotice(projectionStatus, language, staticFallbackPolicy),
    [language, projectionStatus, staticFallbackPolicy],
  );
  const selectedEvents = useMemo(
    () => events.filter((event) => event.dayId === selectedDay.id),
    [events, selectedDay.id],
  );
  const activeImportCandidates = useMemo(
    () => (calendarImportSummary?.candidates ?? []).filter((candidate) => candidate.importStatus === 'candidate'),
    [calendarImportSummary],
  );
  const eventsByDay = useMemo(() => new Map(allVisibleDays.map((day) => [
    day.id,
    events.filter((event) => event.dayId === day.id),
  ])), [allVisibleDays, events]);
  const summaryItems = useMemo(() => {
    if (projectionStatus === 'ready' && calendarSummary !== null) {
      return [
        { icon: 'calendar' as const, label: copy.projectedShifts, value: String(calendarSummary.projectedShiftCount) },
        { icon: 'worker' as const, label: copy.projectedWorkerSlots, value: String(calendarSummary.workerSlots) },
        { icon: 'document' as const, label: language === 'es' ? 'Pendientes de revision' : 'Pending review', value: String(calendarSummary.pendingReviewShiftCount) },
      ];
    }
    const interviews = events.filter((event) => event.kind === 'interview').length;
    const followUps = events.filter((event) => event.kind === 'employer').length;
    return copy.summaryItems.map((item, index) => ({
      ...item,
      value: index === 0 ? String(events.length) : index === 1 ? String(interviews) : index === 2 ? String(followUps) : item.value,
    }));
  }, [calendarSummary, copy.projectedShifts, copy.projectedWorkerSlots, copy.summaryItems, events, language, projectionStatus]);
  async function disposeCalendarImport(candidate: ExternalCalendarImport, disposition: CalendarImportDisposition) {
    if (busyCalendarImportId !== null) return;
    setBusyCalendarImportId(candidate.importId);
    setCalendarImportMessage('');
    const result = await disposeExternalCalendarCandidate(
      candidate.importId,
      candidate.version,
      disposition,
      disposition === 'ignored'
        ? 'Staff ignored the Google Calendar candidate during migration review.'
        : 'Staff marked the Google Calendar candidate as already represented in Golden Rose.',
      makeCalendarImportCommandId(),
    );
    setBusyCalendarImportId(null);
    if (!result.ok) {
      setCalendarImportMessage(result.failure.kind === 'stale' ? copy.googleStale : copy.googleUnavailable);
      return;
    }
    setCalendarImportSummary((current) => {
      if (current === null) return current;
      return {
        ...current,
        candidates: current.candidates.map((item) => (
          item.importId === result.value.candidate.importId ? result.value.candidate : item
        )),
      };
    });
    setCalendarImportMessage(
      disposition === 'ignored' ? copy.googleIgnored : copy.googleMarkedExisting,
    );
  }
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
    const normalizedDayId = normalizeCalendarDayId(storedEvent.dayId, weekDays);
    setSelectedDayId(normalizedDayId);
    const selectedDate = new Date(`${normalizedDayId}T00:00:00`);
    if (!Number.isNaN(selectedDate.getTime())) {
      setVisibleMonth(new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1));
    }
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
  function selectCalendarDay(day: CalendarDay) {
    setSelectedDayId(day.id);
    setVisibleMonth(new Date(day.dateValue.getFullYear(), day.dateValue.getMonth(), 1));
  }
  function showToday() {
    setSelectedDayId(dateId(today));
    setVisibleMonth(new Date(today.getFullYear(), today.getMonth(), 1));
    setViewMode('week');
  }
  function shiftVisibleMonth(delta: -1 | 1) {
    setVisibleMonth((current) => {
      const next = new Date(current.getFullYear(), current.getMonth() + delta, 1);
      if (next.getFullYear() !== currentYear) return current;
      setSelectedDayId(dateId(next));
      return next;
    });
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
          <button className="focus-ring" type="button" onClick={showToday}>{copy.today}</button>
          <span>{viewMode === 'week' ? weekRange : monthHeading}</span>
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

      {operationsNotice ? (
        <p className="projection-status-notice" role="status">{operationsNotice}</p>
      ) : projectionStatus === 'ready' ? (
        <p className="calendar-coverage-note">{copy.projectionSeparate}</p>
      ) : null}

      <div className="calendar-layout">
        <section className="calendar-panel calendar-week-panel" aria-labelledby="calendar-week-heading">
          <div className="calendar-panel-header">
            <h3 id="calendar-week-heading">{viewMode === 'week' ? copy.weekView : copy.monthView}</h3>
            <div className="calendar-view-toggle" aria-label={language === 'es' ? 'Vista del calendario' : 'Calendar view'}>
              <button
                aria-pressed={viewMode === 'week'}
                className="focus-ring"
                type="button"
                onClick={() => {
                  setViewMode('week');
                }}
              >
                {copy.weekView}
              </button>
              <button
                aria-pressed={viewMode === 'month'}
                className="focus-ring"
                type="button"
                onClick={() => {
                  setViewMode('month');
                }}
              >
                {copy.monthView}
              </button>
            </div>
          </div>

          {viewMode === 'month' ? (
            <div className="calendar-month-toolbar" aria-label={language === 'es' ? 'Controles de mes' : 'Month controls'}>
              <button
                className="focus-ring"
                disabled={!canGoPreviousMonth}
                type="button"
                onClick={() => {
                  shiftVisibleMonth(-1);
                }}
              >
                {copy.previousMonth}
              </button>
              <strong>{monthHeading}</strong>
              <button
                className="focus-ring"
                disabled={!canGoNextMonth}
                type="button"
                onClick={() => {
                  shiftVisibleMonth(1);
                }}
              >
                {copy.nextMonth}
              </button>
            </div>
          ) : null}

          {viewMode === 'month' ? (
            <div className="calendar-month-weekdays" aria-hidden="true">
              {weekdayHeadings.map((weekday) => (
                <span key={weekday}>{weekday}</span>
              ))}
            </div>
          ) : null}

          <div className={viewMode === 'week' ? 'calendar-day-strip' : 'calendar-month-grid'}>
            {(viewMode === 'week' ? weekDays : monthCells).map((day, index) => {
              if (day === null) {
                return <div aria-hidden="true" className="calendar-month-day-empty" key={`empty-${String(index)}`} />;
              }
              const eventCount = eventsByDay.get(day.id)?.length ?? 0;
              const isSelected = day.id === selectedDay.id;
              return (
                <button
                  aria-pressed={isSelected}
                  className={viewMode === 'week' ? 'calendar-day-button focus-ring' : 'calendar-day-button calendar-month-day focus-ring'}
                  data-selected={isSelected}
                  data-today={day.isToday}
                  key={day.id}
                  type="button"
                  onClick={() => {
                    selectCalendarDay(day);
                  }}
                >
                  <span>{day.shortLabel}</span>
                  <strong>{viewMode === 'week' ? day.date : day.dayOfMonth}</strong>
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
          <section className="calendar-import-review" aria-labelledby="calendar-import-heading">
            <div className="calendar-import-review-header">
              <div>
                <h4 id="calendar-import-heading">{copy.googleHeading}</h4>
                <p>{copy.googleSubtitle}</p>
              </div>
              <button className="focus-ring" disabled type="button">
                {copy.googleConnect}
              </button>
            </div>
            {calendarImportSummary?.oauthConfigurationRequired ? (
              <p className="calendar-import-notice">{copy.googleConfigRequired}</p>
            ) : null}
            {calendarImportStatus !== 'ready' && calendarImportStatus !== 'loading' ? (
              <p className="calendar-import-notice">{copy.googleUnavailable}</p>
            ) : null}
            {activeImportCandidates.length > 0 ? (
              <ul className="calendar-import-list" aria-label={copy.googleCandidateLabel}>
                {activeImportCandidates.map((candidate) => (
                  <li key={candidate.importId}>
                    <div>
                      <strong>{candidate.eventTitle}</strong>
                      <span>{formatCalendarImportWindow(candidate, language)}</span>
                      <small>{candidate.locationReview ?? copy.googleUnverified}</small>
                    </div>
                    <span>{copy.googleUnverified}</span>
                    <div className="calendar-import-actions">
                      <button
                        className="focus-ring"
                        disabled={busyCalendarImportId !== null}
                        type="button"
                        onClick={() => {
                          void disposeCalendarImport(candidate, 'ignored');
                        }}
                      >
                        {copy.googleIgnore}
                      </button>
                      <button
                        className="focus-ring"
                        disabled={busyCalendarImportId !== null}
                        type="button"
                        onClick={() => {
                          void disposeCalendarImport(candidate, 'marked_existing');
                        }}
                      >
                        {copy.googleMarkExisting}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="calendar-import-empty">{copy.googleNoCandidates}</p>
            )}
            {calendarImportMessage ? <p className="calendar-status" role="status">{calendarImportMessage}</p> : null}
          </section>
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
