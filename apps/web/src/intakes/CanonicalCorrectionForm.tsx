import { useEffect, useRef, useState } from 'react';
import type { DraftObject, DraftValue } from '../api/intakeContracts';
import { correctCanonical } from '../api/canonicalCorrectionClient';
import { useLanguage } from '../i18n/LanguageProvider';
import { AddressFields, Field, IntakeFields } from './IntakeFields';

const correctionMessages = {
  en: { correct: 'Correct this section', title: 'Correct current facts', reason: 'Reason for correction', save: 'Save correction', retry: 'Retry original correction', cancel: 'Cancel correction', unsaved: 'Unsaved correction', saving: 'Saving correction…', unknown: 'Outcome unknown. Retry the original correction before saving another section.', saved: 'Correction saved. Current facts need re-review.', failed: 'Correction was not saved. Check the values and reason.', conflict: 'The record changed. Compare current facts before correcting again.', forbidden: 'Access is unavailable. Concealed values have been cleared.', unavailable: 'Correction saved; current detail is unavailable. Refresh before another correction.' },
  es: { correct: 'Corregir esta sección', title: 'Corregir datos actuales', reason: 'Motivo de la corrección', save: 'Guardar corrección', retry: 'Reintentar corrección original', cancel: 'Cancelar corrección', unsaved: 'Corrección sin guardar', saving: 'Guardando corrección…', unknown: 'Resultado desconocido. Reintente la corrección original antes de guardar otra sección.', saved: 'Corrección guardada. Los datos actuales requieren una nueva revisión.', failed: 'La corrección no se guardó. Revise los datos y el motivo.', conflict: 'El registro cambió. Compare los datos actuales antes de corregir de nuevo.', forbidden: 'Acceso no disponible. Se borraron los datos restringidos.', unavailable: 'Corrección guardada; datos actuales no disponibles. Actualice antes de otra corrección.' },
};
type Pending = { key: string; body: DraftObject; generation: number };
export function CanonicalCorrectionForm({ path, targetId, output, initial, version, committedVersion, blocked, onLock, onDirty, onSaved, onDenied }: {
  path: string; targetId: string; output: string; initial: DraftObject; version: number; committedVersion?: number; blocked: boolean;
  onLock: (locked: boolean) => void; onDirty: (dirty: boolean) => void; onSaved: (version: number | null) => Promise<boolean>; onDenied: () => void;
}) {
  const { language } = useLanguage(), m = correctionMessages[language];
  const [open, setOpen] = useState(false), [value, setValue] = useState(initial), [reason, setReason] = useState('');
  const [status, setStatus] = useState<keyof typeof m>('unsaved');
  const [savedVersion, setSavedVersion] = useState(version);
  const command = useRef<Pending | null>(null), generation = useRef(0), pending = useRef(false), epoch = useRef(0);
  useEffect(() => { const token = ++epoch.current; return () => { epoch.current = token + 1000000; }; }, []);
  useEffect(() => {
    if (!open) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    window.addEventListener('beforeunload', warn);
    return () => { window.removeEventListener('beforeunload', warn); };
  }, [open]);
  function edit(next: DraftObject) { ++generation.current; setValue(next); if (!command.current && status !== 'conflict' && status !== 'unavailable') setStatus('unsaved'); }
  function field(key: string, labels: readonly [string, string], type = 'text', max = 200) {
    return <Field label={labels} value={value[key]} type={type} max={max} change={(next: DraftValue | undefined) => { edit(next === undefined ? Object.fromEntries(Object.entries(value).filter(([name]) => name !== key)) : { ...value, [key]: next }); }} />;
  }
  async function save() {
    if (pending.current || blocked || status === 'conflict' || status === 'unavailable') return;
    const token = epoch.current;
    if (!command.current) command.current = { key: crypto.randomUUID(), body: structuredClone({ expected_version: Math.max(savedVersion, committedVersion ?? savedVersion), reason_text: reason, ...value }), generation: generation.current };
    const sent = command.current;
    pending.current = true; setStatus('saving'); onLock(true);
    const result = await correctCanonical(path, sent.key, sent.body, targetId);
    if (epoch.current !== token) return;
    pending.current = false;
    if (!result.ok) {
      setStatus(result.failure);
      if (result.failure !== 'unknown') { command.current = null; onLock(false); }
      if (result.failure === 'forbidden') { setValue({}); setReason(''); setOpen(false); onDirty(false); onDenied(); }
      return;
    }
    command.current = null; setSavedVersion(result.value.result_record_version);
    const later = generation.current !== sent.generation;
    const superseded = result.value.target.current_version > result.value.result_record_version;
    setStatus(superseded ? 'conflict' : later ? 'unsaved' : 'saved');
    if (!later && !superseded) { setOpen(false); setReason(''); onDirty(false); }
    const available = await onSaved(superseded ? null : result.value.result_record_version);
    if (epoch.current === token) { onLock(false); if (!available) setStatus('unavailable'); }
  }
  return <section>
    {!open ? <button type="button" disabled={blocked || status === 'saving' || status === 'unavailable'} onClick={() => { setValue(initial); setSavedVersion(version); setStatus('unsaved'); setOpen(true); onDirty(true); }}>{m.correct}</button> : <form onSubmit={(event) => { event.preventDefault(); void save(); }}>
      <h4>{m.title}</h4>
      {Object.hasOwn(value, 'address') ? <AddressFields value={value.address as DraftObject} change={(address) => { edit({ address }); }} /> : output === 'preferences' || output === 'request' ? <IntakeFields sectionOnly kind={output === 'preferences' ? 'worker' : 'employer'} value={value} change={edit} /> : <>
        {output === 'worker' ? field('full_name', ['Full name', 'Nombre completo']) : null}
        {output === 'contact_details' ? field('representative_name', ['Current representative name', 'Nombre actual del representante']) : null}
        {output === 'contact' || output === 'contact_details' ? field('phone', ['Phone', 'Teléfono'], 'tel', 40) : null}
      </>}
      <Field label={['Reason for correction', 'Motivo de la corrección']} type="textarea" max={512} value={reason} change={(next) => { ++generation.current; setReason(typeof next === 'string' ? next : ''); }} />
      <button type="submit" disabled={blocked || status === 'saving' || (status !== 'unknown' && !reason.trim()) || status === 'conflict' || status === 'unavailable'}>{status === 'unknown' ? m.retry : m.save}</button>
      <button type="button" disabled={(status === 'saving' || status === 'unknown')} onClick={() => { setOpen(false); setValue(initial); setReason(''); onLock(false); onDirty(false); }}>{m.cancel}</button>
    </form>}
    {open || status === 'saved' || status === 'forbidden' ? <p role={['failed', 'conflict', 'forbidden'].includes(status) ? 'alert' : 'status'}>{m[status]}</p> : null}
  </section>;
}
