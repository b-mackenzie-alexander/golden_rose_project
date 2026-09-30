import { useEffect, useMemo, useState } from 'react';
import { createShiftNeed, listShiftNeeds } from '../api/shiftNeedClient';
import type { ShiftNeed, ShiftNeedFailureKind } from '../api/shiftNeedClient';
import { useLanguage } from '../i18n/LanguageProvider';

type Errors = Partial<Record<'roleTitle' | 'workerCount' | 'startsAt' | 'endsAt' | 'timeZone' | 'reasonText', string>>;

const copy = {
  en: {
    heading: 'Draft shift needs',
    boundary: 'Draft shift needs keep employer demand reviewable. They do not open demand, match workers, confirm coverage, or create referrals.',
    empty: 'No shift needs have been created for this request.',
    roleTitle: 'Role title',
    workerCount: 'Workers needed',
    startsAt: 'Start',
    endsAt: 'End',
    timeZone: 'Time zone',
    reasonText: 'Reason',
    notes: 'Notes',
    create: 'Create draft shift need',
    creating: 'Creating shift need...',
    created: 'Draft shift need recorded. Request review is still required before this becomes active demand.',
    required: 'This field is required.',
    count: 'Enter a whole number between 1 and the request worker count.',
    timeOrder: 'End time must be after start time.',
    unavailable: 'Shift needs are unavailable. Try again.',
    forbidden: 'You do not have permission to manage shift needs for this request.',
    notFound: 'This request is no longer available. Return to the intake and refresh current facts.',
    stale: 'The request changed before the shift was saved. Refresh current facts and try again.',
    validation: 'Review the shift details and try again.',
    unknown: 'The outcome is unknown. Refresh shift needs before retrying.',
    refresh: 'Refresh shift needs',
    status: 'Draft',
    schedule: 'Schedule',
    rowCount: 'workers',
  },
  es: {
    heading: 'Turnos en borrador',
    boundary: 'Los turnos en borrador mantienen la demanda lista para revision. No abren demanda, no emparejan trabajadores, no confirman cobertura ni crean referidos.',
    empty: 'No se han creado turnos para esta solicitud.',
    roleTitle: 'Puesto',
    workerCount: 'Trabajadores necesarios',
    startsAt: 'Inicio',
    endsAt: 'Fin',
    timeZone: 'Zona horaria',
    reasonText: 'Motivo',
    notes: 'Notas',
    create: 'Crear turno en borrador',
    creating: 'Creando turno...',
    created: 'Turno en borrador registrado. La solicitud aun requiere revision antes de ser demanda activa.',
    required: 'Este campo es obligatorio.',
    count: 'Ingrese un numero entero entre 1 y el total de trabajadores solicitados.',
    timeOrder: 'La hora de fin debe ser posterior al inicio.',
    unavailable: 'Los turnos no estan disponibles. Intente otra vez.',
    forbidden: 'No tiene permiso para administrar turnos en esta solicitud.',
    notFound: 'Esta solicitud ya no esta disponible. Vuelva al registro y actualice los datos actuales.',
    stale: 'La solicitud cambio antes de guardar el turno. Actualice los datos actuales e intente otra vez.',
    validation: 'Revise los datos del turno e intente otra vez.',
    unknown: 'El resultado es desconocido. Actualice los turnos antes de reintentar.',
    refresh: 'Actualizar turnos',
    status: 'Borrador',
    schedule: 'Horario',
    rowCount: 'trabajadores',
  },
};

function failureMessage(kind: ShiftNeedFailureKind, language: 'en' | 'es') {
  const m = copy[language];
  return ({
    validation: m.validation,
    forbidden: m.forbidden,
    not_found: m.notFound,
    stale: m.stale,
    unavailable: m.unavailable,
    unknown_outcome: m.unknown,
    unexpected: m.unavailable,
  })[kind];
}

function localValue(value: string) {
  return value ? new Date(value).toLocaleString() : '';
}

function initialTimeZone() {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'America/New_York';
}

export function ShiftNeedsPanel({
  employerId,
  requestId,
  requestVersion,
  roleTitle,
  workerCount,
}: {
  employerId: string;
  requestId: string;
  requestVersion: number;
  roleTitle: string;
  workerCount: number;
}) {
  const { language } = useLanguage();
  const m = copy[language];
  const [items, setItems] = useState<ShiftNeed[]>([]);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [failure, setFailure] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [draft, setDraft] = useState({
    roleTitle,
    workerCount: String(workerCount),
    startsAt: '',
    endsAt: '',
    timeZone: initialTimeZone(),
    reasonText: '',
    notes: '',
  });
  const errors = useMemo<Errors>(() => {
    const next: Errors = {};
    const count = Number(draft.workerCount);
    const start = draft.startsAt ? new Date(draft.startsAt) : null;
    const end = draft.endsAt ? new Date(draft.endsAt) : null;
    if (!draft.roleTitle.trim()) next.roleTitle = m.required;
    if (!Number.isInteger(count) || count < 1 || count > workerCount) next.workerCount = m.count;
    if (!draft.startsAt || start === null || Number.isNaN(start.getTime())) next.startsAt = m.required;
    if (!draft.endsAt || end === null || Number.isNaN(end.getTime())) next.endsAt = m.required;
    if (start && end && !Number.isNaN(start.getTime()) && !Number.isNaN(end.getTime()) && start >= end) next.endsAt = m.timeOrder;
    if (!draft.timeZone.trim()) next.timeZone = m.required;
    if (!draft.reasonText.trim()) next.reasonText = m.required;
    return next;
  }, [draft, m, workerCount]);
  const hasErrors = Object.keys(errors).length > 0;

  async function refresh() {
    setLoading(true);
    setFailure(null);
    const result = await listShiftNeeds(employerId, requestId);
    setLoading(false);
    if (result.ok) {
      setItems(result.value);
    } else {
      setFailure(failureMessage(result.failure.kind, language));
    }
  }

  useEffect(() => {
    let cancelled = false;
    void listShiftNeeds(employerId, requestId).then((result) => {
      if (cancelled) return;
      setLoading(false);
      if (result.ok) setItems(result.value);
      else setFailure(failureMessage(result.failure.kind, language));
    });
    return () => { cancelled = true; };
  }, [employerId, requestId, language]);

  async function submit() {
    setNotice(null);
    setFailure(null);
    if (hasErrors || busy) return;
    setBusy(true);
    const result = await createShiftNeed({
      employerId,
      requestId,
      expectedRequestVersion: requestVersion,
      roleTitle: draft.roleTitle.trim(),
      workerCount: Number(draft.workerCount),
      startsAt: new Date(draft.startsAt).toISOString(),
      endsAt: new Date(draft.endsAt).toISOString(),
      timeZone: draft.timeZone.trim(),
      reasonText: draft.reasonText.trim(),
      notes: draft.notes.trim() || null,
      commandId: crypto.randomUUID(),
    });
    setBusy(false);
    if (!result.ok) {
      setFailure(failureMessage(result.failure.kind, language));
      return;
    }
    setItems((existing) => [result.value.current, ...existing.filter((item) => item.shiftNeedId !== result.value.current.shiftNeedId)]);
    setDraft((value) => ({ ...value, reasonText: '', notes: '' }));
    setNotice(m.created);
  }

  return (
    <section className="shift-needs-panel" aria-labelledby="shift-needs-heading">
      <div className="shift-needs-panel__header">
        <div>
          <h3 id="shift-needs-heading">{m.heading}</h3>
          <p>{m.boundary}</p>
        </div>
        <button className="focus-ring" disabled={loading || busy} type="button" onClick={() => void refresh()}>{m.refresh}</button>
      </div>
      {failure ? <p className="staff-account-error" role="alert">{failure}</p> : null}
      {notice ? <p role="status">{notice}</p> : null}
      <div className="shift-needs-grid">
        <form className="staff-account-form shift-need-form" onSubmit={(event) => { event.preventDefault(); void submit(); }}>
          <label><span>{m.roleTitle}</span><input value={draft.roleTitle} onChange={(event) => { setDraft({ ...draft, roleTitle: event.target.value }); }} /></label>
          {errors.roleTitle ? <small role="alert">{errors.roleTitle}</small> : null}
          <label><span>{m.workerCount}</span><input inputMode="numeric" value={draft.workerCount} onChange={(event) => { setDraft({ ...draft, workerCount: event.target.value }); }} /></label>
          {errors.workerCount ? <small role="alert">{errors.workerCount}</small> : null}
          <label><span>{m.startsAt}</span><input type="datetime-local" value={draft.startsAt} onChange={(event) => { setDraft({ ...draft, startsAt: event.target.value }); }} /></label>
          {errors.startsAt ? <small role="alert">{errors.startsAt}</small> : null}
          <label><span>{m.endsAt}</span><input type="datetime-local" value={draft.endsAt} onChange={(event) => { setDraft({ ...draft, endsAt: event.target.value }); }} /></label>
          {errors.endsAt ? <small role="alert">{errors.endsAt}</small> : null}
          <label><span>{m.timeZone}</span><input value={draft.timeZone} onChange={(event) => { setDraft({ ...draft, timeZone: event.target.value }); }} /></label>
          {errors.timeZone ? <small role="alert">{errors.timeZone}</small> : null}
          <label><span>{m.reasonText}</span><textarea value={draft.reasonText} onChange={(event) => { setDraft({ ...draft, reasonText: event.target.value }); }} /></label>
          {errors.reasonText ? <small role="alert">{errors.reasonText}</small> : null}
          <label><span>{m.notes}</span><textarea value={draft.notes} onChange={(event) => { setDraft({ ...draft, notes: event.target.value }); }} /></label>
          <button className="focus-ring" disabled={busy || hasErrors} type="submit">{busy ? m.creating : m.create}</button>
        </form>
        <section aria-label={language === 'en' ? 'Draft shift need list' : 'Lista de turnos en borrador'} className="shift-need-list">
          {loading ? <p role="status">{language === 'en' ? 'Loading shift needs...' : 'Cargando turnos...'}</p> : null}
          {!loading && items.length === 0 ? <p>{m.empty}</p> : null}
          {items.map((item) => (
            <article className="shift-need-row" key={item.shiftNeedId}>
              <span className="status-chip" data-status="draft">{m.status}</span>
              <strong>{item.roleTitle}</strong>
              <span>{item.workerCount} {m.rowCount}</span>
              <span>{m.schedule}: {localValue(item.startsAt)} - {localValue(item.endsAt)}</span>
              <small>{item.timeZone}</small>
              {item.notes ? <p>{item.notes}</p> : null}
            </article>
          ))}
        </section>
      </div>
    </section>
  );
}
