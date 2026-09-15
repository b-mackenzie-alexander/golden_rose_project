import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router';
import { getCanonicalIntake } from '../api/intakeClient';
import { getCanonicalOutput, hasAddress, outputReference, restrictedOutput } from '../api/canonicalOutputClient';
import type { FinalizationOutputs } from '../api/intakeCanonicalContracts';
import type { DraftObject } from '../api/intakeContracts';
import { useLanguage } from '../i18n/LanguageProvider';
import { canonicalLabel, canonicalMessages } from './canonicalMessages';
import { intakeMessages } from './messages';
import { Snapshot } from './IntakeHistory';

const messages = {
  en: { current: 'Current canonical facts', original: 'Original finalized reference', back: 'Original intake and history',
    changed: 'Current facts have changed since finalization. The original intake and review remain unchanged.',
    unavailable: 'This record is unavailable or you do not have access.', reveal: 'Reveal restricted address', hide: 'Hide restricted address',
    refresh: 'Refresh current facts', separate: 'Address and detail versions differ. Refresh and reveal again to compare current facts.',
    meaning: 'These are current records, not a new review. Worker preferences remain self-reported; a draft request does not open demand or create shifts.',
    addressHint: 'Household contact addresses require separate access; business contacts may have no household address.',
  },
  es: { current: 'Datos canónicos actuales', original: 'Referencia original finalizada', back: 'Admisión original e historial',
    changed: 'Los datos actuales cambiaron desde la finalización. La admisión y revisión originales permanecen sin cambios.',
    unavailable: 'Este registro no está disponible o no tiene acceso.', reveal: 'Mostrar dirección restringida', hide: 'Ocultar dirección restringida',
    refresh: 'Actualizar datos actuales', separate: 'Las versiones de dirección y datos difieren. Actualice y vuelva a mostrar la dirección para comparar los datos actuales.',
    meaning: 'Estos son registros actuales, no una nueva revisión. Las preferencias siguen siendo autodeclaradas; una solicitud en borrador no abre demanda ni crea turnos.',
    addressHint: 'Las direcciones de contactos de hogares requieren acceso separado; los contactos comerciales pueden no tener dirección de hogar.',
  },
};
function OutputDetail({ intakeId, output }: { intakeId: string; output: string }) {
  const { language } = useLanguage(), m = messages[language], cm = canonicalMessages[language], common = intakeMessages[language];
  const [outputs, setOutputs] = useState<FinalizationOutputs | null>(null);
  const [facts, setFacts] = useState<DraftObject | null>(null), [address, setAddress] = useState<DraftObject | null>(null);
  const [busy, setBusy] = useState(true), [failed, setFailed] = useState(false), [addressFailed, setAddressFailed] = useState(false);
  const epoch = useRef(0), pending = useRef(false);
  useEffect(() => {
    const token = ++epoch.current;
    void getCanonicalIntake(intakeId).then(async (result) => {
      if (token !== epoch.current) return;
      const next = result.ok && result.value.summary.lifecycle === 'finalized' ? result.value.finalization : undefined;
      if (!next || !outputReference(next, output)) { setFailed(true); setBusy(false); return; }
      setOutputs(next);
      if (restrictedOutput(output)) { setBusy(false); return; }
      const current = await getCanonicalOutput(next, output);
      if (token !== epoch.current) return;
      setFacts(current.ok ? current.value : null); setFailed(!current.ok); setBusy(false);
    });
    const clear = () => { ++epoch.current; setOutputs(null); setFacts(null); setAddress(null); setBusy(false); };
    const restore = (event: PageTransitionEvent) => { if (event.persisted) window.location.reload(); };
    window.addEventListener('pagehide', clear); window.addEventListener('pageshow', restore);
    return () => { epoch.current = token + 1000000; window.removeEventListener('pagehide', clear); window.removeEventListener('pageshow', restore); };
  }, [intakeId, output]);
  async function read(reveal = false) {
    if (!outputs || pending.current || busy) return;
    const token = ++epoch.current;
    pending.current = true; setBusy(true);
    if (reveal) { setAddress(null); setAddressFailed(false); }
    else { setFacts(null); setAddress(null); setFailed(false); setAddressFailed(false); }
    const result = await getCanonicalOutput(outputs, output, reveal);
    if (token !== epoch.current) return;
    pending.current = false; setBusy(false);
    if (reveal) { setAddress(result.ok ? result.value : null); setAddressFailed(!result.ok); }
    else { setFacts(result.ok ? result.value : null); setFailed(!result.ok); }
  }
  function hide() {
    ++epoch.current; pending.current = false; setBusy(false); setAddress(null); setAddressFailed(false);
    if (restrictedOutput(output)) { setFacts(null); setFailed(false); }
  }
  const ref = outputs ? outputReference(outputs, output) : null;
  return <section>
    <Link to={`/staff/intakes/${intakeId}`}>{m.back}</Link>
    <h2>{canonicalLabel(output, language)}</h2>
    {ref ? <p>{m.original}: {ref.id} · {cm.version} {ref.version} · {cm[ref.disposition]}</p> : null}
    <p>{m.meaning}</p>
    {outputs ? <nav aria-label={cm.outputs}><ul>{Object.keys(outputs).filter((key) => outputReference(outputs, key)).map((key) =>
      <li key={key}><Link aria-current={key === output ? 'page' : undefined} to={`/staff/intakes/${intakeId}/outputs/${key}`}>{canonicalLabel(key, language)}</Link></li>)}</ul></nav> : null}
    {busy ? <p role="status">{common.loading}</p> : null}
    {failed ? <p role="alert">{m.unavailable}</p> : null}
    {outputs ? <button type="button" disabled={busy} onClick={() => void read()}>{restrictedOutput(output) ? m.reveal : m.refresh}</button> : null}
    {facts ? <section><h3>{m.current}</h3>
      {ref && facts.version !== ref.version ? <p role="status">{m.changed}</p> : null}
      <Snapshot value={facts} />
    </section> : null}
    {outputs && hasAddress(output, outputs) && facts ? <>
      {output === 'contact_details' ? <p>{m.addressHint}</p> : null}
      <button type="button" disabled={busy} onClick={() => void read(true)}>{m.reveal}</button>
    </> : null}
    {addressFailed ? <p role="alert">{m.unavailable}</p> : null}
    {address ? <section aria-label={m.reveal}>
      {facts && address.version !== facts.version ? <p role="status">{m.separate}</p> : null}
      <Snapshot value={address} />
    </section> : null}
    {outputs && (restrictedOutput(output) || hasAddress(output, outputs)) ? <button type="button" onClick={hide}>{m.hide}</button> : null}
  </section>;
}
export function CanonicalOutput() {
  const { intakeId = '', output = '' } = useParams();
  return <OutputDetail key={`${intakeId}:${output}`} intakeId={intakeId} output={output} />;
}
