import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router';
import { getIntake, getIntakeAddress, queryIntakes, saveIntake } from '../api/intakeClient';
import type {
  AddressSection,
  DraftObject,
  IntakeDetail,
  IntakeKind,
  IntakeSummary,
} from '../api/intakeContracts';
import { useLanguage } from '../i18n/LanguageProvider';
import { AddressFields, IntakeFields } from './IntakeFields';
import { intakeMessages } from './messages';
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
};
const addressSections = (kind: IntakeKind): AddressSection[] =>
  kind === 'worker' ? ['worker_residence'] : ['party_address', 'worksite_address'];

function IntakeEditor({ id, kind: initialKind }: { id?: string; kind: IntakeKind }) {
  const { language } = useLanguage();
  const m = intakeMessages[language];
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
    void getIntake(id).then(async (result) => {
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
      for (const section of addressSections(detail.summary.kind)) {
        const address = await getIntakeAddress(id, section);
        if (isCancelled()) return;
        update((s) =>
          s.error === 'conflict'
            ? s
            : {
                ...s,
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
        error: result.ok && result.value.version !== s.detail?.summary.version ? 'conflict' : s.error,
        sections: { ...s.sections, [section]: next },
      };
    });
  }
  async function save(name: string) {
    const s = current.current;
    const section = s.sections[name] ?? (name === 'workflow' ? initialSection({}) : undefined);
    if (
      !section ||
      section.readPending ||
      s.error === 'conflict' ||
      Object.entries(s.sections).some(
        ([key, value]) => value.status === 'saving' || (key !== name && value.status === 'unknown'),
      )
    )
      return;
    const intakeId = s.detail?.summary.intake_id;
    const workflow = name === 'workflow';
    if (
      workflow &&
      !section.command &&
      section.value.operation !== 'follow-ups' &&
      !Object.entries(s.sections)
        .filter(([key]) => key !== 'workflow')
        .every(([, value]) => value.status === 'saved' && !value.readPending)
    )
      return;
    const path = workflow
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
                ...(section.value.operation !== 'follow-ups' && !section.value.outcome
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
    const result = await saveIntake(pending.command);
    if (!active.current) return;
    if (!result.ok) {
      update((previous) => ({
        ...previous,
        error: result.failure === 'conflict' ? 'conflict' : previous.error,
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
    if (detail.summary.version > result.value.result_record_version) {
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
    if (!intakeId) {
      for (const address of addressSections(kind)) await loadAddress(address);
    } else if (name !== 'content' && !workflow) {
      const address = await getIntakeAddress(intakeId, name as AddressSection);
      update((previous) => {
        const own = finishSection(previous.sections[name] ?? section, 'saved');
        if (!address.ok)
          return {
            ...previous,
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
  const addressTitle = (name: string) =>
    name === 'worker_residence' ? m.residence : name === 'party_address' ? m.party : m.worksite;
  if (state.busy) return <p role="status">{m.loading}</p>;
  if (id && !state.detail) return <p role="alert">{m.failure}</p>;
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
                  : name === 'workflow'
                    ? t('workflow')
                    : addressTitle(name)}
                : {m[section.status]}
              </li>
            ))}
        </ul>
      ) : null}
      {state.error ? <p role="alert">{m[state.error]}</p> : null}
      {state.confirmedConflict ? <p role="status">{m.confirmedConflict}</p> : null}
      {state.error === 'conflict' && state.detail ? (
        <a href={`/staff/intakes/${state.detail.summary.intake_id}`}>{m.open}</a>
      ) : null}
      <fieldset>
        <legend>{m.content}</legend>
        {state.sections.content?.status === 'unavailable' ? (
          <p role="status">{m.unavailable}</p>
        ) : (
          <>
            <IntakeFields
              kind={kind}
              value={state.sections.content?.value ?? {}}
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
            <fieldset key={name}>
              <legend>{addressTitle(name)}</legend>
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
                    {item.complete ? m.complete : m.incomplete} · {m.saved} · {t(item.review_status)} ·{' '}
                    {m.version} {item.version}
                  </span>
                  {!item.complete ? (
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
