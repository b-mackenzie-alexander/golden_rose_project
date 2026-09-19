import { useEffect, useRef, useState } from 'react';
import { canonicalReference } from '../api/intakeCanonicalContracts';
import { discover, type Choice, type Collection } from '../api/canonicalDiscovery';
import type { DraftObject, IntakeDetail } from '../api/intakeContracts';
import { useLanguage } from '../i18n/LanguageProvider';
import { canonicalLabel, canonicalMessages } from './canonicalMessages';
import { intakeMessages } from './messages';
import type { Section } from './saveState';

function Choices({ kind, parent, collection, choose, disabled }: {
  kind: 'worker' | 'employer'; parent?: string; collection?: Collection;
  choose: (choice: Choice | null) => void; disabled: boolean;
}) {
  const { language } = useLanguage(), m = canonicalMessages[language], status = intakeMessages[language];
  const [query, setQuery] = useState(''), [items, setItems] = useState<Choice[]>([]);
  const [cursor, setCursor] = useState<string | null>(null), [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false), [searched, setSearched] = useState(false);
  const epoch = useRef(0), pending = useRef(false);
  useEffect(() => {
    const token = ++epoch.current;
    const clear = () => { ++epoch.current; setItems([]); setCursor(null); };
    window.addEventListener('pagehide', clear);
    return () => { epoch.current = token + 1000000; window.removeEventListener('pagehide', clear); };
  }, []);
  async function search(more = false) {
    if (pending.current || disabled) return;
    pending.current = true;
    const token = ++epoch.current;
    setBusy(true); setFailed(false);
    const result = await discover(kind, query, more ? cursor ?? undefined : undefined, parent, collection);
    if (token !== epoch.current) return;
    pending.current = false;
    setBusy(false); setSearched(true); setFailed(!result.ok);
    setItems((old) => result.ok ? [...(more ? old.filter((x) => !result.value.items.some((y) => y.id === x.id)) : []), ...result.value.items] : []);
    setCursor(result.ok ? result.value.next_cursor : null);
  }
  return <fieldset disabled={disabled}>
    <legend>{collection ? m[collection] : m.party}</legend>
    {!parent ? <label>{m.query}<input value={query} maxLength={100} onChange={(e) => {
      ++epoch.current; pending.current = false; setBusy(false); setItems([]); setCursor(null); setSearched(false); setQuery(e.target.value);
    }} /></label> : null}
    <button type="button" disabled={busy || (!parent && query.trim().length < 2)} onClick={() => void search()}>{m.search}</button>
    {busy ? <p role="status">{status.loading}</p> : null}
    {failed ? <p role="alert">{status.unavailable}</p> : null}
    {searched && !busy && !failed && !items.length ? <p>{m.empty}</p> : null}
    <label>{m.choose}<select defaultValue="" disabled={busy} onChange={(e) => {
      choose(e.target.value === 'new' ? null : items.find((x) => x.id === e.target.value) ?? null);
    }} key={`${query}:${items.map((x) => `${x.id}:${String(x.version)}`).join(',')}`}>
      <option value="" disabled>{m.choose}</option><option value="new">{m.new}</option>
      {items.map((x) => <option key={x.id} value={x.id}>{x.label} · {x.id} · {m.version} {x.version}</option>)}
    </select></label>
    {cursor ? <button type="button" disabled={busy} onClick={() => void search(true)}>{m.more}</button> : null}
  </fieldset>;
}
export function IntakeCanonical({ detail, section, ready, locked, change, save, discard }: {
  detail: IntakeDetail; section: Section; ready: boolean; locked: boolean;
  discard?: () => void; change: (value: DraftObject) => void; save: (value?: DraftObject) => void;
}) {
  const { language } = useLanguage(), m = canonicalMessages[language], status = intakeMessages[language];
  const [confirmation, setConfirmation] = useState<string | null>(null);
  const [party, setParty] = useState<Choice | null>(null);
  const reviewKey = `${String(detail.summary.version)}:${detail.latest_review?.review_id ?? ''}`;
  const value = section.value;
  const children = party && detail.summary.kind === 'employer'
    ? (party.employerType === 'business' ? ['contacts', 'worksites', 'addresses'] : ['contacts', 'worksites']) as Collection[] : [];
  const linkReady = value.operation === 'links' && Object.hasOwn(value, 'party') &&
    children.every((x) => Object.hasOwn(value, x === 'contacts' ? 'contact' : x === 'worksites' ? 'worksite' : 'business_address'));
  const canFinalize = ready && detail.summary.complete && detail.summary.review_status === 'current' &&
    !detail.dependency_stale && detail.latest_review?.outcome === 'intake_reviewed';
  const showFinalization = detail.latest_review !== undefined || detail.summary.review_status === 'current';
  if (section.status === 'unknown') return <fieldset><legend>{m.title}</legend>
    <p role="status">{status.unknown}</p><button type="button" onClick={() => { save(); }}>{status.retry}</button></fieldset>;
  if (section.status === 'unavailable') return <p role="status">{status.unavailable}</p>;
  return <fieldset disabled={locked}>
    <legend>{m.title}</legend><p>{m.selection}</p>
    {detail.dependency_stale ? <p role="alert">{m.stale}</p> : null}
    <Choices kind={detail.summary.kind} disabled={locked} choose={(choice) => {
      setParty(choice); setConfirmation(null);
      change({ operation: 'links', party: choice ? { id: choice.id, version: choice.version } : null });
    }} />
    {children.map((collection) => <Choices key={`${party?.id ?? ""}:${String(party?.version)}:${collection}`}
      kind="employer" parent={party?.id} collection={collection} disabled={locked} choose={(choice) => {
        change({ ...value, [collection === 'contacts' ? 'contact' : collection === 'worksites' ? 'worksite' : 'business_address']:
          choice ? { id: choice.id, version: choice.version } : null });
      }} />)}
    {value.operation === 'links' ? <section><h3>{m.selected}</h3><ul>{Object.entries(value).filter(([key]) => key !== 'operation').map(([key, ref]) =>
      <li key={key}>{canonicalLabel(key, language)}: {canonicalReference(ref)
        ? `${ref.id} · ${m.version} ${String(ref.version)}` : m.new}</li>)}</ul></section> : null}
    <button type="button" disabled={!ready || !linkReady} onClick={() => { save(); }}>{m.apply}</button>
    {Object.keys(detail.links).length ? <button type="button" disabled={!ready} onClick={() => {
      setParty(null); save({ operation: 'links', party: null });
    }}>{m.unlink}</button> : null}
    {discard && ['unsaved', 'failed'].includes(section.status) ? <button type="button" onClick={() => { setParty(null); setConfirmation(null); discard(); }}>{m.discard}</button> : null}
    {showFinalization ? (
      <>
        <p>{m.meaning}</p><label><input type="checkbox" checked={confirmation === reviewKey}
          onChange={(e) => { setConfirmation(e.target.checked ? reviewKey : null); }} />{m.confirm}</label>
        {!canFinalize ? <p>{m.ready}</p> : null}
        <button type="button" disabled={!canFinalize || confirmation !== reviewKey || !(section.status === 'saved' || (section.status === 'failed' && value.operation === 'finalizations'))} onClick={() => {
          setConfirmation(null); save({ operation: 'finalizations', review_id: detail.latest_review?.review_id ?? '' });
        }}>{m.finalize}</button>
      </>
    ) : null}
    <p role="status">{status[section.status]}</p>
  </fieldset>;
}
