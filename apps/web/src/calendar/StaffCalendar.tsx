import { useMemo, useState } from 'react';

import { IconSymbol } from '../dashboard/artwork';
import type { IconName } from '../dashboard/artwork';
import { useLanguage } from '../i18n/LanguageProvider';

type CalendarEventKind = 'employer' | 'focus' | 'interview' | 'review' | 'staff';

type CalendarEvent = {
  accent: 'danger' | 'info' | 'success' | 'warning';
  assignee: string;
  dayId: string;
  duration: string;
  kind: CalendarEventKind;
  meta: string;
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
  agendaHeading: string;
  assigneeLabel: string;
  calendarHeading: string;
  dayView: string;
  events: CalendarEvent[];
  openSlots: string;
  selectedDay: string;
  subtitle: string;
  summaryItems: Array<{ icon: IconName; label: string; value: string }>;
  thisWeek: string;
  weekDays: CalendarDay[];
  weekRange: string;
  weekView: string;
};

const englishCalendar: CalendarCopy = {
  agendaHeading: "Today's agenda",
  assigneeLabel: 'Assigned to',
  calendarHeading: 'Calendar',
  dayView: 'Day',
  events: [
    { accent: 'danger', assignee: 'Mariela Torres', dayId: 'mon', duration: '30 min', kind: 'staff', meta: 'Staff meeting', time: '9:00 AM', title: 'Team check-in' },
    { accent: 'warning', assignee: 'Carlos Ramirez', dayId: 'mon', duration: '30 min', kind: 'employer', meta: 'Employer follow-up', time: '10:30 AM', title: 'Call Restaurante La Esperanza' },
    { accent: 'success', assignee: 'Ana Torres', dayId: 'mon', duration: '45 min', kind: 'interview', meta: 'Worker registration', time: '12:00 PM', title: 'Interview with Ana Quispe' },
    { accent: 'info', assignee: 'Operations', dayId: 'mon', duration: '45 min', kind: 'review', meta: 'Queue review', time: '2:00 PM', title: 'Review pending intakes' },
    { accent: 'success', assignee: 'Sofia Diaz', dayId: 'mon', duration: '30 min', kind: 'employer', meta: 'Document check', time: '4:00 PM', title: 'Follow-up with Maria Lopez' },
    { accent: 'warning', assignee: 'Carlos Ramirez', dayId: 'tue', duration: '30 min', kind: 'employer', meta: 'Employer intake', time: '10:00 AM', title: 'Bright Horizons staffing call' },
    { accent: 'success', assignee: 'Mariela Torres', dayId: 'tue', duration: '45 min', kind: 'interview', meta: 'Worker interview', time: '1:30 PM', title: 'Meet Carlos Mendoza' },
    { accent: 'info', assignee: 'Operations', dayId: 'wed', duration: '60 min', kind: 'focus', meta: 'Focus block', time: '9:30 AM', title: 'Worker intake review block' },
    { accent: 'warning', assignee: 'Sofia Diaz', dayId: 'thu', duration: '30 min', kind: 'employer', meta: 'Follow-up', time: '11:00 AM', title: 'Clean Homes LLC confirmation' },
    { accent: 'success', assignee: 'Ana Torres', dayId: 'fri', duration: '45 min', kind: 'interview', meta: 'Interview', time: '2:00 PM', title: 'Interview with Jason Meme' },
  ],
  openSlots: 'Open slots',
  selectedDay: 'Selected day',
  subtitle: 'Today, interviews, follow-ups, and protected focus time.',
  summaryItems: [
    { icon: 'calendar', label: 'Scheduled events', value: '10' },
    { icon: 'worker', label: 'Interviews', value: '3' },
    { icon: 'building', label: 'Employer follow-ups', value: '3' },
  ],
  thisWeek: 'This week',
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
  agendaHeading: 'Agenda de hoy',
  assigneeLabel: 'Asignado a',
  calendarHeading: 'Calendario',
  dayView: 'Dia',
  events: [
    { accent: 'danger', assignee: 'Mariela Torres', dayId: 'mon', duration: '30 min', kind: 'staff', meta: 'Reunion del equipo', time: '9:00 a. m.', title: 'Revision diaria' },
    { accent: 'warning', assignee: 'Carlos Ramirez', dayId: 'mon', duration: '30 min', kind: 'employer', meta: 'Seguimiento de empleador', time: '10:30 a. m.', title: 'Llamada con Restaurante La Esperanza' },
    { accent: 'success', assignee: 'Ana Torres', dayId: 'mon', duration: '45 min', kind: 'interview', meta: 'Registro de trabajador', time: '12:00 p. m.', title: 'Entrevista con Ana Quispe' },
    { accent: 'info', assignee: 'Operaciones', dayId: 'mon', duration: '45 min', kind: 'review', meta: 'Revision de cola', time: '2:00 p. m.', title: 'Revisar registros pendientes' },
    { accent: 'success', assignee: 'Sofia Diaz', dayId: 'mon', duration: '30 min', kind: 'employer', meta: 'Verificar documentos', time: '4:00 p. m.', title: 'Seguimiento con Maria Lopez' },
    { accent: 'warning', assignee: 'Carlos Ramirez', dayId: 'tue', duration: '30 min', kind: 'employer', meta: 'Registro de empleador', time: '10:00 a. m.', title: 'Llamada con Bright Horizons' },
    { accent: 'success', assignee: 'Mariela Torres', dayId: 'tue', duration: '45 min', kind: 'interview', meta: 'Entrevista de trabajador', time: '1:30 p. m.', title: 'Entrevista con Carlos Mendoza' },
    { accent: 'info', assignee: 'Operaciones', dayId: 'wed', duration: '60 min', kind: 'focus', meta: 'Bloque de enfoque', time: '9:30 a. m.', title: 'Revision de registros de trabajadores' },
    { accent: 'warning', assignee: 'Sofia Diaz', dayId: 'thu', duration: '30 min', kind: 'employer', meta: 'Seguimiento', time: '11:00 a. m.', title: 'Confirmacion de Clean Homes LLC' },
    { accent: 'success', assignee: 'Ana Torres', dayId: 'fri', duration: '45 min', kind: 'interview', meta: 'Entrevista', time: '2:00 p. m.', title: 'Entrevista con Jason Meme' },
  ],
  openSlots: 'Espacios abiertos',
  selectedDay: 'Dia seleccionado',
  subtitle: 'Hoy, entrevistas, seguimientos y tiempo protegido de enfoque.',
  summaryItems: [
    { icon: 'calendar', label: 'Eventos programados', value: '10' },
    { icon: 'worker', label: 'Entrevistas', value: '3' },
    { icon: 'building', label: 'Seguimientos', value: '3' },
  ],
  thisWeek: 'Esta semana',
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

export function StaffCalendar() {
  const { language } = useLanguage();
  const copy = language === 'es' ? spanishCalendar : englishCalendar;
  const [selectedDayId, setSelectedDayId] = useState('mon');
  const fallbackDay = copy.weekDays[0];
  if (fallbackDay === undefined) {
    throw new Error('Staff calendar requires at least one day.');
  }
  const selectedDay = copy.weekDays.find((day) => day.id === selectedDayId) ?? fallbackDay;
  const selectedEvents = useMemo(
    () => copy.events.filter((event) => event.dayId === selectedDay.id),
    [copy.events, selectedDay.id],
  );
  const eventsByDay = useMemo(() => new Map(copy.weekDays.map((day) => [
    day.id,
    copy.events.filter((event) => event.dayId === day.id),
  ])), [copy.events, copy.weekDays]);

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
        {copy.summaryItems.map((item) => (
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
              <article className="calendar-event" data-accent={event.accent} key={`${event.dayId}-${event.time}-${event.title}`}>
                <time>{event.time}</time>
                <span aria-hidden="true" className="calendar-event-icon">
                  <IconSymbol name={eventIcons[event.kind]} />
                </span>
                <div>
                  <h4>{event.title}</h4>
                  <p>{event.meta}</p>
                  <dl>
                    <div>
                      <dt>{copy.assigneeLabel}</dt>
                      <dd>{event.assignee}</dd>
                    </div>
                    <div>
                      <dt>{language === 'es' ? 'Duracion' : 'Duration'}</dt>
                      <dd>{event.duration}</dd>
                    </div>
                  </dl>
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
              <li data-accent={event.accent} key={`${event.time}-${event.title}`}>
                <time>{event.time}</time>
                <div>
                  <strong>{event.title}</strong>
                  <span>{event.meta}</span>
                </div>
              </li>
            ))}
          </ol>
        </aside>
      </div>
    </section>
  );
}
