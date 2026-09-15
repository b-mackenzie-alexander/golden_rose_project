import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router';
import { getCanonicalIntake, getIntakeAddress, queryIntakes, saveIntake, saveCanonicalIntake } from '../api/intakeClient';
import type {
  AddressSection,
  DraftObject,
  IntakeDetail,
  IntakeKind,
  IntakeSummary,
} from '../api/intakeContracts';
import { useLanguage } from '../i18n/LanguageProvider';
import { AddressFields, Field, IntakeFields } from './IntakeFields';
import { intakeMessages } from './messages';
import { IntakeCanonical } from './IntakeCanonical';
import { canonicalLabel, canonicalMessages } from './canonicalMessages';
import { IntakeWorkflow } from './IntakeWorkflow';
import { IntakeHistory } from './IntakeHistory';
import { workflowLabel } from './workflowMessages';
import {
  allSaved,
  editSection,
  finishSection,
  initialSection,
  submitSection,
  type Section,
} from './saveState';

type EditorState = {
  detail: IntakeDetail | null;
  sections: Record<string, Section>;
  error: 'failure' | 'conflict' | null;
  confirmedConflict?: boolean;
  busy: boolean;
  canonicalEpoch?: number;
  resolvedAddresses?: Record<string, DraftObject | null>;
};
const addressSections = (kind: IntakeKind): AddressSection[] =>
  kind === 'worker' ? ['worker_residence'] : ['party_address', 'worksite_address'];

function IntakeEditor({ id, kind: initialKind }: { id?: string; kind: IntakeKind }) {
  const { language } = useLanguage();
  const m = intakeMessages[language];
  const cm = canonicalMessages[language];
  const t = (key: string) => workflowLabel(key, language);
  const [state, setState] = useState<EditorState>(() => ({
    detail: null,
    sections: { content: { ...initialSection({}), status: 'unsaved' } },
    error: null,
    busy: !!id,
  }));
  const current = useRef(state);
  const active = useRef(true);
  const addressReads = useRef<Record<string, { epoch: number; pending: boolean }>>({});
  const update = (fn: (previous: EditorState) => EditorState) => {
    if (!active.current) return;
    current.current = fn(current.current);
    setState(current.current);
  };
  const kind = state.detail?.summary.kind ?? initialKind;
  const dirty = Object.values(state.sections).some((s) =>
    ['unsaved', 'saving', 'unknown', 'failed', 'refresh'].includes(s.status),
  );
  useEffect(() => {
    active.current = true;
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (
        Object.values(current.current.sections).some((s) =>
          ['unsaved', 'saving', 'unknown', 'failed', 'refresh'].includes(s.status),
        )
      ) {
        event.preventDefault();
      }
    };
    const navigation = (event: MouseEvent) => {
      const target = event.target instanceof Element ? event.target.closest('a[href]') : null;
      if (
        target &&
        Object.values(current.current.sections).some((s) =>
          ['unsaved', 'saving', 'unknown', 'failed', 'refresh'].includes(s.status),
        ) &&
        !window.confirm(m.leave)
      ) {
        event.preventDefault();
        event.stopPropagation();
      }
    };
    const clear = () => {
      active.current = false;
      addressReads.current = {};
      current.current = { detail: null, sections: {}, busy: false, error: null };
      setState(current.current);
    };
    const restore = (event: PageTransitionEvent) => {
      if (event.persisted) window.location.reload();
    };
    window.addEventListener('beforeunload', beforeUnload);
    window.addEventListener('pagehide', clear);
    window.addEventListener('pageshow', restore);
    document.addEventListener('click', navigation, true);
    return () => {
      active.current = false;
      window.removeEventListener('beforeunload', beforeUnload);
      window.removeEventListener('pagehide', clear);
      window.removeEventListener('pageshow', restore);
      document.removeEventListener('click', navigation, true);
    };
  }, [m.leave]);
  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    const isCancelled = () => cancelled || !active.current;
    void getCanonicalIntake(id).then(async (result) => {
      if (isCancelled()) return;
      if (!result.ok) {
        update((s) => ({ ...s, error: 'failure', busy: false }));
        return;
      }
      const detail = result.value;
      update((s) => ({
        ...s,
        detail,
        busy: false,
        sections: {
          content: initialSection(detail.candidate),
          ...Object.fromEntries(
            addressSections(detail.summary.kind).map((name) => [
              name,
              { ...initialSection({}), status: 'loading' as const },
            ]),
          ),
        },
      }));
      if (detail.summary.lifecycle === 'finalized') return;
      for (const section of addressSections(detail.summary.kind)) {
        const address = await getIntakeAddress(id, section);
        if (isCancelled()) return;
        update((s) =>
          s.error === 'conflict'
            ? s
            : {
                ...s,
                resolvedAddresses: { ...s.resolvedAddresses, [section]: address.ok ? address.value.resolved : null },
                ...(address.ok && address.value.version !== s.detail?.summary.version
                  ? { error: 'conflict' as const }
                  : {}),
                sections: {
                  ...s.sections,
                  [section]: address.ok
                    ? initialSection(address.value.candidate ?? {})
                    : { ...initialSection({}), status: 'unavailable' },
                },
              },
        );
      }
    });
    return () => {
      cancelled = true;
    };
  }, [id]);
  const change = (name: string, value: DraftObject) => {
    update((s) => ({
      ...s,
      sections: { ...s.sections, [name]: editSection(s.sections[name] ?? initialSection({}), value) },
    }));
  };
  const currentReadEpoch = (section: AddressSection) => addressReads.current[section]?.epoch;
  async function loadAddress(section: AddressSection) {
    const selected = current.current.detail;
    const previousRead = addressReads.current[section];
    // The synchronous guard also covers double clicks before React paints the disabled button.
    if (!selected || current.current.error === 'conflict' || previousRead?.pending) return;
    const epoch = (previousRead?.epoch ?? 0) + 1;
    const generation = current.current.sections[section]?.generation ?? 0;
    addressReads.current[section] = { epoch, pending: true };
    update((s) => ({
      ...s,
      sections: {
        ...s.sections,
        [section]: { ...(s.sections[section] ?? initialSection({})), readPending: true },
      },
    }));
    const result = await getIntakeAddress(selected.summary.intake_id, section);
    if (
      !active.current ||
      currentReadEpoch(section) !== epoch ||
      current.current.detail?.summary.intake_id !== selected.summary.intake_id
    )
      return;
    addressReads.current[section] = { epoch, pending: false };
    update((s) => {
      const own = s.sections[section] ?? initialSection({});
      const hasEdits = own.generation !== generation || own.generation > own.confirmedGeneration;
      const next: Section = result.ok
        ? hasEdits
          ? { ...own, readPending: false, status: 'unsaved' }
          : initialSection(result.value.candidate ?? {})
        : result.failure !== 'forbidden' && (own.status === 'refresh' || hasEdits)
          ? { ...own, readPending: false, status: 'refresh' }
          : { ...initialSection({}), status: 'unavailable' };
      return {
        ...s,
        resolvedAddresses: { ...s.resolvedAddresses, [section]: result.ok ? result.value.resolved : null },
        error: result.ok && result.value.version !== s.detail?.summary.version ? 'conflict' : s.error,
        sections: { ...s.sections, [section]: next },
      };
    });
  }
  async function save(name: string) {
    const s = current.current;
    const section = s.sections[name] ?? (['workflow', 'canonical'].includes(name) ? initialSection({}) : undefined);
    if (
      !section ||
      s.detail?.summary.lifecycle === 'finalized' ||
      section.readPending ||
      s.error === 'conflict' ||
      Object.entries(s.sections).some(
        ([key, value]) => value.status === 'saving' || (key !== name && value.status === 'unknown'),
      )
    )
      return;
    const intakeId = s.detail?.summary.intake_id;
    const canonical = name === 'canonical';
    const workflow = name === 'workflow' || canonical;
    if (
      workflow &&
      !section.command &&
      section.value.operation !== 'follow-ups' &&
      !Object.entries(s.sections)
        .filter(([key]) => key !== name)
        .every(([, value]) => value.status === 'saved' && !value.readPending)
    )
      return;
    if (canonical && !section.command && section.value.operation === 'finalizations' &&
      (!s.detail?.summary.complete || s.detail.summary.review_status !== 'current' ||
        s.detail.dependency_stale || s.detail.latest_review?.review_id !== section.value.review_id)) return;
    const path = canonical
      ? `/intakes/${intakeId ?? ''}/${section.value.operation === 'links' ? 'links' : 'finalizations'}`
      : workflow
      ? `/intakes/${intakeId ?? ''}/${section.value.operation === 'follow-ups' ? 'follow-ups' : 'reviews'}`
      : !intakeId
        ? '/intakes'
        : name === 'content'
          ? `/intakes/${intakeId}/revisions`
          : `/intakes/${intakeId}/addresses/${name}/revisions`;
    const pending = section.command
      ? { ...section, status: 'saving' as const }
      : workflow
        ? {
            ...section,
            status: 'saving' as const,
            command: Object.freeze({
              key: crypto.randomUUID(),
              path,
              generation: section.generation,
              body: structuredClone({
                expected_version: s.detail?.summary.version ?? 0,
                ...Object.fromEntries(
                  Object.entries(section.value).filter(([key]) => key !== 'operation'),
                ),
                ...(!canonical && section.value.operation !== 'follow-ups' && !section.value.outcome
                  ? { outcome: 'intake_reviewed' }
                  : {}),
              }),
            }),
          }
        : submitSection(
            section,
            crypto.randomUUID(),
            s.detail?.summary.version ?? 0,
            path,
            name !== 'content',
            intakeId ? undefined : kind,
          );
    update((previous) => ({ ...previous, sections: { ...previous.sections, [name]: pending } }));
    if (!pending.command) return;
    const result = await (canonical ? saveCanonicalIntake : saveIntake)(pending.command);
    if (!active.current) return;
    if (!result.ok) {
      update((previous) => ({
        ...previous,
        error: result.failure === 'conflict' ? 'conflict' : previous.error,
        resolvedAddresses: result.failure === 'forbidden' && !workflow
          ? { ...previous.resolvedAddresses, [name]: null } : previous.resolvedAddresses,
        sections: {
          ...previous.sections,
          [name]:
            result.failure === 'forbidden'
              ? { ...initialSection({}), status: 'unavailable' }
              : finishSection(
                  previous.sections[name] ?? section,
                  result.failure === 'unknown' ? 'unknown' : 'failed',
                ),
        },
      }));
      return;
    }
    if (
      result.value.current.summary.kind !== kind ||
      (intakeId && result.value.current.summary.intake_id !== intakeId)
    ) {
      update((previous) => ({
        ...previous,
        sections: {
          ...previous.sections,
          [name]: finishSection(previous.sections[name] ?? section, 'unknown'),
        },
      }));
      return;
    }
    const detail = result.value.current;
    if (detail.summary.lifecycle === 'finalized' && pending.command.path.endsWith('/finalizations')) {
      addressReads.current = {};
      update((previous) => ({ ...previous, detail, sections: {}, resolvedAddresses: {} }));
      return;
    }
    if (detail.summary.version > result.value.result_record_version || detail.summary.lifecycle === 'finalized') {
      // The receipt confirms our command, but the newer aggregate version includes unseen edits.
      // Do not adopt it as an expected-version baseline for any retained local section.
      addressReads.current = {};
      update((previous) => ({
        ...previous,
        detail: previous.detail ?? detail,
        error: 'conflict',
        confirmedConflict: true,
        sections: {
          ...Object.fromEntries(
            Object.entries(previous.sections).map(([key, value]) => [
              key,
              { ...value, readPending: false },
            ]),
          ),
          [name]: { ...finishSection(previous.sections[name] ?? section, 'saved'), readPending: false },
        },
      }));
      return;
    }
    update((previous) => {
      const own = previous.sections[name] ?? section;
      const finished = finishSection(own, 'saved');
      return {
        ...previous,
        detail,
        canonicalEpoch: canonical ? (previous.canonicalEpoch ?? 0) + 1 : previous.canonicalEpoch,
        sections: {
          ...previous.sections,
          ...(!workflow && name !== 'content' && previous.sections.content?.status === 'saved'
            ? { content: initialSection(detail.candidate) }
            : {}),
          ...(!intakeId
            ? Object.fromEntries(
                addressSections(kind).map((address) => [
                  address,
                  { ...initialSection({}), status: 'loading' as const },
                ]),
              )
            : {}),
          [name]:
            name === 'content' && finished.status === 'saved'
              ? { ...finished, value: detail.candidate }
              : workflow
                ? finished.status === 'saved'
                  ? initialSection({})
                  : finished
                : name !== 'content'
                  ? { ...own, status: 'saving' as const }
                  : finished,
        },
      };
    });
    if (canonical) {
      update((previous) => ({ ...previous, resolvedAddresses: {}, sections: { ...previous.sections,
        ...Object.fromEntries(addressSections(kind).map((address) => [address, { ...(previous.sections[address] ?? initialSection({})), status: 'loading' as const }])) } }));
      for (const address of addressSections(kind)) await loadAddress(address);
    } else if (!intakeId) {
      for (const address of addressSections(kind)) await loadAddress(address);
    } else if (name !== 'content' && !workflow) {
      const address = await getIntakeAddress(intakeId, name as AddressSection);
      update((previous) => {
        const own = finishSection(previous.sections[name] ?? section, 'saved');
        if (!address.ok)
          return {
            ...previous,
            resolvedAddresses: { ...previous.resolvedAddresses, [name]: null },
            sections: {
              ...previous.sections,
              [name]:
                address.failure === 'forbidden'
                  ? { ...initialSection({}), status: 'unavailable' }
                  : { ...own, status: 'refresh' },
            },
          };
        return {
          ...previous,
          resolvedAddresses: { ...previous.resolvedAddresses, [name]: address.value.resolved },
          error:
            address.value.version !== previous.detail?.summary.version ? 'conflict' : previous.error,
          sections: {
            ...previous.sections,
            [name]: own.status === 'saved' ? { ...own, value: address.value.candidate ?? {} } : own,
          },
        };
      });
    }
  }
  const locked =
    state.error === 'conflict' ||
    Object.values(state.sections).some((s) => s.status === 'saving' || s.status === 'unknown');
  const finalizing = !!state.sections.canonical?.command &&
    state.sections.canonical.command.path.endsWith('/finalizations');
  const addressTitle = (name: string) =>
    name === 'worker_residence' ? m.residence : name === 'party_address' ? m.party : m.worksite;
  if (state.busy) return <p role="status">{m.loading}</p>;
  if (id && !state.detail) return <p role="alert">{m.failure}</p>;
  if (state.detail?.summary.lifecycle === 'finalized') return <section>
    <Link to={`/staff/intakes/${kind === 'worker' ? 'workers' : 'employers'}`}>{m.back}</Link>
    <h2>{cm.finalized}</h2><p>{state.detail.summary.display_name}</p>
    <h3>{cm.outputs}</h3><ul>{Object.entries(state.detail.finalization ?? {}).filter(([name]) => name !== 'kind').map(([name, ref]) =>
      <li key={name}>{ref && typeof ref !== 'string' ? <Link to={`/staff/intakes/${state.detail?.summary.intake_id ?? ''}/outputs/${name}`}>{canonicalLabel(name, language)}</Link> : canonicalLabel(name, language)}: {ref && typeof ref !== 'string' ? `${ref.id} · ${cm.version} ${String(ref.version)} · ${cm[ref.disposition]}` : '—'}</li>)}</ul>
    <IntakeHistory id={state.detail.summary.intake_id} version={state.detail.summary.version} />
  </section>;
  return (
    <section className="intake-editor" aria-label={m.content}>
      {state.detail ? (
        <>
          <Link to={`/staff/intakes/${kind === 'worker' ? 'workers' : 'employers'}`}>{m.back}</Link>
          <p>
            {m.version} {state.detail.summary.version} ·{' '}
            {state.detail.summary.complete ? m.complete : m.incomplete} ·{' '}
            {t(state.detail.summary.review_status)}
          </p>
          <p className="intake-reference">
            <Link to={`/staff/intakes/${state.detail.summary.intake_id}`}>
              {state.detail.summary.intake_id}
            </Link>
          </p>
        </>
      ) : null}
      <p role="status" className="intake-save-banner">
        {!state.error && allSaved(Object.values(state.sections)) && state.detail
          ? m.allSaved
          : m.pending}
      </p>
      {!allSaved(Object.values(state.sections)) ? (
        <ul>
          {Object.entries(state.sections)
            .filter(([, section]) => section.status !== 'saved')
            .map(([name, section]) => (
              <li key={name}>
                {name === 'content'
                  ? m.content
                  : name === 'canonical' ? cm.title : name === 'workflow'
                    ? t('workflow')
                    : addressTitle(name)}
                : {m[section.status]}
                {section.status === 'failed' ? ` — ${m.fieldGuidance}` : ''}
              </li>
            ))}
        </ul>
      ) : null}
      {state.error ? <p role="alert">{m[state.error]}</p> : null}
      {state.confirmedConflict ? <p role="status">{m.confirmedConflict}</p> : null}
      {state.error === 'conflict' && state.detail ? (
        <a href={`/staff/intakes/${state.detail.summary.intake_id}`}>{m.open}</a>
      ) : null}
      {state.detail && Object.keys(state.detail.links).length ? <section>
        <h3>{cm.saved}</h3><ul>{Object.entries(state.detail.links).map(([name, ref]) => <li key={name}>{canonicalLabel(name, language)}: {ref.id} · {cm.version} {ref.version}</li>)}</ul>
        {state.detail.dependency_stale ? <p role="alert">{cm.stale}</p> : null}
        <fieldset disabled><legend>{cm.resolved}</legend>{kind === 'worker' ? <IntakeFields kind={kind} value={state.detail.resolved} change={() => {}} /> :
          Object.entries(state.detail.resolved).map(([key, value]) => <Field key={key}
            label={key === 'employer_type' ? ['Employer type', 'Tipo de empleador'] : key === 'display_name'
              ? ['Employer name', 'Nombre del empleador'] : key === 'phone' ? ['Phone', 'Teléfono']
                : ['Representative name', 'Nombre del representante']}
            value={value} change={() => {}}
            {...(key === 'employer_type' ? { options: [['business', 'Business', 'Empresa'], ['household', 'Household', 'Hogar']] as const } : {})} />)}</fieldset>
        <p>{cm.selection}</p><h3>{cm.candidate}</h3>
      </section> : null}
      <fieldset disabled={finalizing}>
        <legend>{m.content}</legend>
        {state.sections.content?.status === 'unavailable' ? (
          <p role="status">{m.unavailable}</p>
        ) : (
          <>
            <IntakeFields
              kind={kind}
              value={state.sections.content?.value ?? {}}
              showValidation={state.sections.content?.status === 'failed'}
              change={(value) => {
                change('content', value);
              }}
            />
            <p role="status">{m[state.sections.content?.status ?? 'unsaved']}</p>
            <button
              type="button"
              disabled={
                state.error === 'conflict' ||
                (locked && state.sections.content?.status !== 'unknown') ||
                state.sections.content?.status === 'saved'
              }
              onClick={() => void save('content')}
            >
              {state.sections.content?.status === 'unknown' ? m.retry : m.save}
            </button>
          </>
        )}
      </fieldset>
      {!state.detail ? (
        <p>{m.noAddressYet}</p>
      ) : (
        addressSections(kind).map((name) => {
          const section = state.sections[name];
          return (
            <fieldset key={name} disabled={finalizing}>
              <legend>{addressTitle(name)}</legend>
              {state.resolvedAddresses?.[name] ? <fieldset disabled><legend>{cm.resolved}</legend>
                <AddressFields value={state.resolvedAddresses[name]} change={() => {}} /></fieldset> : null}
              {!section || section.status === 'loading' || section.status === 'unavailable' ? (
                <>
                  <p role="status">{section?.status === 'unavailable' ? m.unavailable : m.loading}</p>
                  {section?.status === 'unavailable' ? (
                    <button
                      type="button"
                      disabled={locked || section.readPending}
                      onClick={() => void loadAddress(name)}
                    >
                      {m.reveal}
                    </button>
                  ) : null}
                </>
              ) : (
                <>
                  {name === 'worksite_address' &&
                  state.sections.party_address &&
                  !['loading', 'unavailable'].includes(state.sections.party_address.status) ? (
                    <button
                      type="button"
                      onClick={() => {
                        change(
                          name,
                          structuredClone(current.current.sections.party_address?.value ?? {}),
                        );
                      }}
                    >
                      {m.copyAddress}
                    </button>
                  ) : null}
                  <AddressFields
                    value={section.value}
                    change={(value) => {
                      change(name, value);
                    }}
                  />
                  <p role="status">{m[section.status]}</p>
                  {section.status === 'refresh' ? (
                    <button
                      type="button"
                      disabled={locked || section.readPending}
                      onClick={() => void loadAddress(name)}
                    >
                      {m.reveal}
                    </button>
                  ) : null}
                  <button
                    type="button"
                    disabled={
                      state.error === 'conflict' ||
                      (locked && section.status !== 'unknown') ||
                      section.status === 'saved' ||
                      section.status === 'refresh'
                    }
                    onClick={() => void save(name)}
                  >
                    {section.status === 'unknown' ? m.retry : `${m.saveAddress}: ${addressTitle(name)}`}
                  </button>
                </>
              )}
            </fieldset>
          );
        })
      )}
      {state.detail ? (
        <>
          <IntakeCanonical
            key={`${state.detail.summary.intake_id}:${String(state.canonicalEpoch ?? 0)}`}
            detail={state.detail} section={state.sections.canonical ?? initialSection({})}
            ready={!state.error && Object.entries(state.sections).filter(([key]) => key !== 'canonical')
              .every(([, section]) => section.status === 'saved' && !section.readPending)}
            locked={locked}
            discard={() => { update((previous) => ({ ...previous, canonicalEpoch: (previous.canonicalEpoch ?? 0) + 1, sections: { ...previous.sections, canonical: initialSection({}) } })); }}
            change={(value) => { change('canonical', value); }}
            save={(value) => { if (value) change('canonical', value); void save('canonical'); }}
          />
          <IntakeWorkflow
            detail={state.detail}
            section={state.sections.workflow ?? initialSection({})}
            ready={
              !state.error &&
              Object.entries(state.sections)
                .filter(([key]) => key !== 'workflow')
                .every(([, section]) => section.status === 'saved' && !section.readPending)
            }
            locked={locked}
            change={(value) => {
              change('workflow', value);
            }}
            save={() => void save('workflow')}
          />
          <IntakeHistory
            key={`${state.detail.summary.intake_id}:${String(state.detail.summary.version)}`}
            id={state.detail.summary.intake_id}
            version={state.detail.summary.version}
          />
        </>
      ) : null}
      {dirty ? <p>{m.unsaved}</p> : null}
    </section>
  );
}

export function IntakeWorkspace({ kind = 'worker' }: { kind?: IntakeKind }) {
  const { intakeId } = useParams();
  const { language } = useLanguage();
  const m = intakeMessages[language];
  const t = (key: string) => workflowLabel(key, language);
  const [items, setItems] = useState<IntakeSummary[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [cursor, setCursor] = useState<string | null>(null);
  const [filter, setFilter] = useState('');
  const [byReference, setByReference] = useState(false);
  const appliedFilter = useRef<DraftObject>({});
  const [newDraft, setNewDraft] = useState(false);
  const requestNumber = useRef(0);
  async function query(next?: string) {
    const request = ++requestNumber.current;
    if (!next)
      appliedFilter.current = filter.trim()
        ? { [byReference ? 'reference' : 'name_query']: filter.trim() }
        : {};
    const result = await queryIntakes(kind, {
      ...appliedFilter.current,
      ...(next ? { cursor: next } : {}),
    });
    if (request !== requestNumber.current) return;
    if (result.ok) {
      setItems(result.value.items);
      setCursor(result.value.next_cursor);
      setFailed(false);
    } else {
      setItems(null);
      setCursor(null);
      setFailed(true);
    }
  }
  useEffect(() => {
    const request = ++requestNumber.current;
    if (!intakeId)
      void queryIntakes(kind).then((result) => {
        if (request !== requestNumber.current) return;
        if (result.ok) {
          setItems(result.value.items);
          setCursor(result.value.next_cursor);
        } else {
          setItems(null);
          setCursor(null);
          setFailed(true);
        }
      });
    const clear = () => {
      ++requestNumber.current;
      appliedFilter.current = {};
      setItems(null);
      setFilter('');
      setCursor(null);
    };
    window.addEventListener('pagehide', clear);
    return () => {
      requestNumber.current = request + 1000000;
      window.removeEventListener('pagehide', clear);
    };
  }, [kind, intakeId]);
  return (
    <div className="intake-workspace">
      <h2>{intakeId ? m.content : m[kind]}</h2>
      <p>{m.intro}</p>
      {intakeId ? (
        <>
          <IntakeEditor key={intakeId} id={intakeId} kind={kind} />
        </>
      ) : (
        <>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void query();
            }}
            className="intake-search"
          >
            <label>
              <input
                type="checkbox"
                checked={byReference}
                onChange={(event) => {
                  setByReference(event.target.checked);
                  setFilter('');
                }}
              />
              {m.reference}
            </label>
            <label htmlFor="intake-name-query">{byReference ? m.reference : m.query}</label>
            <input
              id="intake-name-query"
              value={filter}
              minLength={byReference ? 36 : 2}
              maxLength={100}
              onChange={(e) => {
                setFilter(e.target.value);
              }}
            />
            <button type="submit">{m.search}</button>
          </form>
          {failed ? (
            <p role="alert">{m.unavailableDraft}</p>
          ) : items === null ? (
            <p role="status">{m.loading}</p>
          ) : !items.length ? (
            <p>{m.empty}</p>
          ) : (
            <ul className="intake-list">
              {items.map((item) => (
                <li key={item.intake_id}>
                  <Link to={`/staff/intakes/${item.intake_id}`}>
                    {m.open}: {item.display_name || m.unnamed} — {item.intake_id}
                  </Link>
                  <span>
                    {item.complete === null ? m.completenessUnavailable : item.complete ? m.complete : m.incomplete} · {m.saved} · {t(item.review_status)} ·{' '}
                    {m.version} {item.version}
                  </span>
                  {item.complete === false ? (
                    <span>
                      {t('missing')}: {item.missing_fields.map((field) => t(field)).join(', ')}
                    </span>
                  ) : null}
                  {item.follow_up ? (
                    <span>
                      {t('retained')}: {item.follow_up.next_follow_up_at}
                      {item.follow_up.overdue ? ` · ${t('overdue')}` : ''}
                    </span>
                  ) : null}
                  {item.offer ? (
                    <span>
                      {typeof item.offer.minimum === 'string' ? item.offer.minimum : ''}
                      {item.offer.maximum
                        ? `–${typeof item.offer.maximum === 'string' ? item.offer.maximum : ''}`
                        : ''}{' '}
                      {typeof item.offer.currency === 'string' ? item.offer.currency : ''}{' '}
                      {typeof item.offer.basis === 'string' && Object.hasOwn(m.basis, item.offer.basis)
                        ? m.basis[item.offer.basis as keyof typeof m.basis]
                        : ''}{' '}
                      {item.offer.per_worker === true ? m.offer : ''}{' '}
                      {item.offer.negotiable === true
                        ? language === 'en'
                          ? 'Negotiable'
                          : 'Negociable'
                        : ''}
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
          {cursor ? (
            <button type="button" onClick={() => void query(cursor)}>
              {m.more}
            </button>
          ) : null}
          <button
            type="button"
            onClick={() => {
              setNewDraft(true);
            }}
          >
            {m.create}
          </button>
          {newDraft ? <IntakeEditor key={kind} kind={kind} /> : null}
        </>
      )}
    </div>
  );
}
