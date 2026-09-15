import { useRef, useState } from 'react';
import type { FinalizationOutputs } from '../api/intakeCanonicalContracts';
import type { DraftObject } from '../api/intakeContracts';
import { currentReview, reviewCanonical } from '../api/canonicalCorrectionClient';
import type { CurrentReview } from '../api/canonicalCorrectionClient';
import { useLanguage } from '../i18n/LanguageProvider';
import { Field } from './IntakeFields';

const messages = {
  en: { title: 'Current facts review', read: 'Check current review', review: 'Review current facts', retry: 'Retry original review', note: 'Review note (optional)', unreviewed: 'Current facts have not been reviewed.', current: 'Current facts review is current.', stale: 'Current facts changed. Review them again.', pending: 'Checking current facts…', failed: 'Review unavailable. Refresh and compare current facts.', unknown: 'Review outcome unknown. Retry the original request.', meaning: 'This review preserves the original finalized intake and review. It does not verify preferences or open demand.' },
  es: { title: 'Revisión de datos actuales', read: 'Consultar revisión actual', review: 'Revisar datos actuales', retry: 'Reintentar revisión original', note: 'Nota de revisión (opcional)', unreviewed: 'Los datos actuales no se han revisado.', current: 'La revisión de datos actuales está vigente.', stale: 'Los datos actuales cambiaron. Revíselos de nuevo.', pending: 'Consultando datos actuales…', failed: 'Revisión no disponible. Actualice y compare los datos actuales.', unknown: 'Resultado de revisión desconocido. Reintente la solicitud original.', meaning: 'Esta revisión conserva la admisión y revisión originales. No verifica preferencias ni abre demanda.' },
};
export function CanonicalCurrentReview({ intakeId, outputs, blocked, onLock, onDenied }: { intakeId: string; outputs: FinalizationOutputs; blocked: boolean; onLock: (locked: boolean) => void; onDenied: () => void }) {
  const { language } = useLanguage(), m = messages[language];
  const [state, setState] = useState<CurrentReview | null>(null), [note, setNote] = useState('');
  const [status, setStatus] = useState<'pending' | 'failed' | 'unknown' | null>(null);
  const pending = useRef(false), command = useRef<{ key: string; body: DraftObject } | null>(null);
  async function run(write: boolean) {
    if (pending.current || blocked) return;
    pending.current = true; setStatus('pending'); onLock(true);
    if (write && !command.current && state) command.current = { key: crypto.randomUUID(), body: { expected_review_version: state.review_version, expected_versions: state.dependencies, ...(note.trim() ? { note } : {}) } };
    const result = write && command.current ? await reviewCanonical(intakeId, outputs, command.current.key, command.current.body) : await currentReview(intakeId, outputs);
    pending.current = false;
    if (!result.ok) { if (result.failure === 'forbidden') onDenied(); setStatus(result.failure === 'unknown' ? 'unknown' : 'failed'); if (result.failure !== 'unknown') { command.current = null; setState(null); onLock(false); } return; }
    command.current = null; onLock(false); setState(result.value); setStatus(null);
  }
  return <section><h3>{m.title}</h3><p>{m.meaning}</p>
    <button type="button" disabled={blocked || status === 'pending' || status === 'unknown'} onClick={() => void run(false)}>{m.read}</button>
    {state ? <><p role="status">{m[state.status]}</p><Field label={['Review note (optional)', 'Nota de revisión (opcional)']} max={512} value={note} change={(next) => { setNote(typeof next === 'string' ? next : ''); }} />
      <button type="button" disabled={blocked || status === 'pending'} onClick={() => void run(true)}>{status === 'unknown' ? m.retry : m.review}</button></> : null}
    {status ? <p role={status === 'failed' ? 'alert' : 'status'}>{m[status]}</p> : null}
  </section>;
}
