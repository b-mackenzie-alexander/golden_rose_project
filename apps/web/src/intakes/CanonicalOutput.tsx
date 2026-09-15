import { CanonicalCorrectionForm } from './CanonicalCorrectionForm';
import { CanonicalCurrentReview } from './CanonicalCurrentReview';
import { correctionPath } from '../api/canonicalCorrectionClient';
import { useContext, useEffect, useRef, useState } from 'react';
import { NavigationGuardContext } from '../app/navigationGuardContext';
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
  const [lockedSection, setLockedSection] = useState<string | null>(null);
  const [dirtySections, setDirtySections] = useState<Record<string, boolean>>({});
  const hasDirty = Object.values(dirtySections).some(Boolean);
  const [committedVersion, setCommittedVersion] = useState<number>();
  const [savedNotice, setSavedNotice] = useState(false);
  const [reviewLocked, setReviewLocked] = useState(false);
  const [reviewEpoch, setReviewEpoch] = useState(0);
  const epoch = useRef(0), pending = useRef(false);
  const setNavigationBlocked = useContext(NavigationGuardContext);
  useEffect(() => {
    setNavigationBlocked?.(hasDirty || lockedSection !== null || reviewLocked);
    return () => { setNavigationBlocked?.(false); };
  }, [hasDirty, lockedSection, reviewLocked, setNavigationBlocked]);
  useEffect(() => {
    if (!hasDirty && !lockedSection && !reviewLocked) return;
    const navigation = (event: MouseEvent) => {
      if (event.target instanceof Element && event.target.closest('a[href]')) { event.preventDefault(); event.stopPropagation(); }
    };
    const unload = (event: BeforeUnloadEvent) => { event.preventDefault(); };
    document.addEventListener('click', navigation, true); window.addEventListener('beforeunload', unload);
    return () => { document.removeEventListener('click', navigation, true); window.removeEventListener('beforeunload', unload); };
  }, [hasDirty, lockedSection, reviewLocked]);
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
  function deny() {
    setFacts(null); setAddress(null); setDirtySections({}); setLockedSection(null); setFailed(true);
  }
  function correction(values: DraftObject, addressSection = false) {
    if (!outputs) return null;
    const path = correctionPath(outputs, output, addressSection), reference = outputReference(outputs, output);
    if (!path || !reference) return null;
    const sectionKey = addressSection ? 'address' : 'facts';
    const keys = outputs.kind === 'worker' ? ({ worker: ['full_name'], contact: ['phone'], residence: ['address'], preferences: ['interests', 'availability'] } as Record<string, string[]>)[output]
      : addressSection || output === 'business_address' ? ['address'] : output === 'contact_details' ? ['representative_name', 'phone'] : ['role_title', 'duties_summary', 'worker_count', 'schedule', 'offer'];
    const initial = Object.fromEntries(Object.entries(values).filter(([key]) => keys?.includes(key)));
    return <CanonicalCorrectionForm path={path} targetId={reference.id} output={output} initial={initial} version={Number(values.version)} committedVersion={committedVersion} blocked={reviewLocked || (lockedSection !== null && lockedSection !== sectionKey)}
      onDirty={(dirty) => { setDirtySections((sections) => ({ ...sections, [sectionKey]: dirty })); }}
      onLock={(locked) => { setLockedSection(locked ? sectionKey : null); }}
      onDenied={deny}
      onSaved={async (version) => {
        if (version !== null) setCommittedVersion(version);
        const token = epoch.current;
        const fresh = await getCanonicalOutput(outputs, output, addressSection);
        if (token !== epoch.current) return false;
        setSavedNotice(!fresh.ok);
        if (fresh.ok) { if (addressSection) setAddress(fresh.value); else setFacts(fresh.value); }
        else if (fresh.failure === 'forbidden') deny();
        setReviewEpoch((value) => value + 1);
        return fresh.ok;
      }} />;
  }
  const ref = outputs ? outputReference(outputs, output) : null;
  return <section>
    <Link onClick={(event) => { if (hasDirty || lockedSection) event.preventDefault(); }} aria-disabled={hasDirty || !!lockedSection} to={`/staff/intakes/${intakeId}`}>{m.back}</Link>
    <h2>{canonicalLabel(output, language)}</h2>
    {ref ? <p>{m.original}: {ref.id} · {cm.version} {ref.version} · {cm[ref.disposition]}</p> : null}
    <p>{m.meaning}</p>
    {hasDirty || lockedSection || reviewLocked ? <p role="status">{language === 'en' ? 'Save, retry, or cancel pending changes before refreshing or leaving this record.' : 'Guarde, reintente o cancele los cambios pendientes antes de actualizar o salir de este registro.'}</p> : null}
    {outputs ? <nav aria-label={cm.outputs}><ul>{Object.keys(outputs).filter((key) => outputReference(outputs, key)).map((key) =>
      <li key={key}><Link onClick={(event) => { if (hasDirty || lockedSection) event.preventDefault(); }} aria-disabled={hasDirty || !!lockedSection} aria-current={key === output ? 'page' : undefined} to={`/staff/intakes/${intakeId}/outputs/${key}`}>{canonicalLabel(key, language)}</Link></li>)}</ul></nav> : null}
    {busy ? <p role="status">{common.loading}</p> : null}
    {failed ? <p role="alert">{m.unavailable}</p> : null}
    {outputs ? <button type="button" disabled={busy || lockedSection !== null || hasDirty || reviewLocked} onClick={() => void read()}>{restrictedOutput(output) ? m.reveal : m.refresh}</button> : null}
    {facts ? <section><h3>{m.current}</h3>
      {ref && facts.version !== ref.version ? <p role="status">{m.changed}</p> : null}
      <Snapshot value={facts} />
      {correction(facts)}
    </section> : null}
    {outputs && hasAddress(output, outputs) && facts ? <>
      {output === 'contact_details' ? <p>{m.addressHint}</p> : null}
      <button type="button" disabled={busy || lockedSection !== null || hasDirty || reviewLocked} onClick={() => void read(true)}>{m.reveal}</button>
    </> : null}
    {addressFailed ? <p role="alert">{m.unavailable}</p> : null}
    {address ? <section aria-label={m.reveal}>
      {facts && address.version !== facts.version ? <p role="status">{m.separate}</p> : null}
      <Snapshot value={address} />
      {correction(address, true)}
    </section> : null}
    {outputs && (restrictedOutput(output) || hasAddress(output, outputs)) ? <button type="button" disabled={lockedSection !== null || hasDirty || reviewLocked} onClick={hide}>{m.hide}</button> : null}
    {savedNotice ? <p role="status">{language === 'en' ? 'Correction saved; current detail is unavailable.' : 'Corrección guardada; datos actuales no disponibles.'}</p> : null}
    {outputs ? <CanonicalCurrentReview key={reviewEpoch} onDenied={deny} onLock={setReviewLocked} intakeId={intakeId} outputs={outputs} blocked={lockedSection !== null || hasDirty} /> : null}
  </section>;
}
export function CanonicalOutput() {
  const { intakeId = '', output = '' } = useParams();
  return <OutputDetail key={`${intakeId}:${output}`} intakeId={intakeId} output={output} />;
}
