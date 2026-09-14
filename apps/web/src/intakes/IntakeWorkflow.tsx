import { useEffect, useRef, useState } from 'react';
import { queryFollowUpOwners } from '../api/intakeClient';
import type { DraftObject, IntakeDetail, StaffChoice } from '../api/intakeContracts';
import { useLanguage } from '../i18n/LanguageProvider';
import { Field } from './IntakeFields';
import { intakeMessages } from './messages';
import type { Section } from './saveState';
import { workflowLabel } from './workflowMessages';

export function IntakeWorkflow({
  detail,
  section,
  ready,
  locked,
  change,
  save,
}: {
  detail: IntakeDetail;
  section: Section;
  ready: boolean;
  locked: boolean;
  change: (value: DraftObject) => void;
  save: () => void;
}) {
  const { language } = useLanguage(),
    m = intakeMessages[language];
  const t = (key: string) => workflowLabel(key, language);
  const [owners, setOwners] = useState<StaffChoice[]>([]),
    [cursor, setCursor] = useState<string | null>(null),
    [unavailable, setUnavailable] = useState(false),
    [confirmedVersion, setConfirmedVersion] = useState<number | null>(null);
  const confirmed = confirmedVersion === detail.summary.version;
  const epoch = useRef(0);
  const id = detail.summary.intake_id;
  useEffect(() => {
    const token = ++epoch.current;
    void queryFollowUpOwners(id).then((result) => {
      if (token !== epoch.current) return;
      setUnavailable(!result.ok);
      setOwners(result.ok ? result.value.items : []);
      setCursor(result.ok ? result.value.next_cursor : null);
    });
    const clear = () => {
      ++epoch.current;
      setOwners([]);
      setCursor(null);
      setConfirmedVersion(null);
    };
    window.addEventListener('pagehide', clear);
    return () => {
      epoch.current = token + 1000000;
      window.removeEventListener('pagehide', clear);
    };
  }, [id]);
  async function more() {
    const token = ++epoch.current;
    const result = await queryFollowUpOwners(id, cursor ?? undefined);
    if (token !== epoch.current) return;
    setUnavailable(!result.ok);
    setOwners((previous) =>
      result.ok
        ? [
            ...result.value.items,
            ...previous.filter(
              (owner) => !result.value.items.some((next) => next.staff_id === owner.staff_id),
            ),
          ]
        : [],
    );
    if (!result.ok) setConfirmedVersion(null);
    setCursor(result.ok ? result.value.next_cursor : null);
  }
  const value = section.value,
    operation = value.operation === 'follow-ups' ? 'follow-ups' : 'reviews';
  const outcome = typeof value.outcome === 'string' ? value.outcome : 'intake_reviewed';
  const follow = operation === 'follow-ups' || outcome === 'needs_follow_up';
  const label = (key: string) => [workflowLabel(key, 'en'), workflowLabel(key, 'es')] as const;
  function edit(key: string, v: unknown) {
    setConfirmedVersion(null);
    const next = Object.fromEntries(
      Object.entries({ ...value, operation, [key]: v }).filter(([, item]) => item !== undefined),
    );
    change(next as DraftObject);
  }
  const field = (key: string, title: string, max = 512) => (
    <Field
      key={key}
      label={label(title)}
      value={value[key]}
      max={max}
      change={(v) => {
        edit(key, v);
      }}
    />
  );
  const options = (keys: string[]) =>
    keys.map((key) => [key, workflowLabel(key, 'en'), workflowLabel(key, 'es')] as const);
  return (
    <fieldset>
      <legend>{t('workflow')}</legend>
      <p>{t('meaning')}</p>
      <p>{t('shared')}</p>
      {detail.latest_review ? (
        <p>
          {t('actor')}: {detail.latest_review.actor_display_name} · {t('version')}{' '}
          {detail.latest_review.reviewed_record_version} · {t('contentVersion')}{' '}
          {detail.latest_review.reviewed_content_version}
        </p>
      ) : null}
      {detail.summary.follow_up ? (
        <p>
          {t('retained')}: {detail.summary.follow_up.next_follow_up_at} · {t('owner')}:{' '}
          {owners.find((owner) => owner.staff_id === detail.summary.follow_up?.owner_staff_id)
            ?.display_name ?? detail.summary.follow_up.owner_staff_id}
          {detail.summary.follow_up.overdue ? ` · ${t('overdue')}` : ''}
        </p>
      ) : null}
      {section.status === 'unavailable' ? (
        <p role="status">{t('unavailable')}</p>
      ) : (
        <>
          <label>
            {t('action')}
            <select
              value={operation}
              disabled={locked}
              onChange={(e) => {
                setConfirmedVersion(null);
                change({
                  operation: e.target.value,
                  ...(e.target.value === 'reviews'
                    ? { outcome: 'intake_reviewed' }
                    : { action: 'reschedule' }),
                });
              }}
            >
              <option value="reviews">{t('review')}</option>
              {detail.summary.follow_up ? (
                <option value="follow-ups">
                  {t('reschedule')} / {t('reassign')} / {t('attempt')}
                </option>
              ) : null}
            </select>
          </label>
          {operation === 'reviews' ? (
            <Field
              label={label('disposition')}
              value={outcome}
              options={options(['intake_reviewed', 'needs_follow_up'])}
              change={(v) => {
                setConfirmedVersion(null);
                change({ operation, outcome: v ?? 'intake_reviewed' });
              }}
            />
          ) : (
            <Field
              label={label('action')}
              value={value.action ?? 'reschedule'}
              options={options(['reschedule', 'reassign', 'attempt'])}
              change={(v) => {
                const next: DraftObject = { ...value, action: v ?? 'reschedule' };
                delete next.method;
                delete next.outcome;
                setConfirmedVersion(null);
                change(next);
              }}
            />
          )}
          {follow ? (
            <>
              {operation === 'reviews' ? (
                <Field
                  label={label('reasonCode')}
                  value={value.reason_code}
                  options={options(['missing_information', 'clarification', 'other'])}
                  change={(v) => {
                    edit('reason_code', v);
                  }}
                />
              ) : null}
              {field('reason_text', 'reason')}
              {unavailable ? <p role="status">{t('unavailable')}</p> : null}
              <Field
                label={label('owner')}
                value={value.owner_staff_id}
                options={owners.map((owner) => [owner.staff_id, owner.display_name, owner.display_name])}
                change={(v) => {
                  edit('owner_staff_id', v);
                }}
              />
              {cursor ? (
                <button type="button" onClick={() => void more()}>
                  {t('more')}
                </button>
              ) : null}
              {field('next_follow_up_at', 'due', 100)}
              <p>
                {language === 'en'
                  ? 'Enter a date and time with an explicit offset, for example 2026-09-14T15:00:00-04:00, and its matching IANA time zone. Past deadlines are allowed.'
                  : 'Ingrese fecha y hora con desplazamiento explícito, por ejemplo 2026-09-14T15:00:00-04:00, y su zona horaria IANA correspondiente. Se permiten fechas vencidas.'}
              </p>
              {field('time_zone', 'zone', 100)}
              {operation === 'follow-ups' && value.action === 'attempt' ? (
                <>
                  <Field
                    label={label('method')}
                    value={value.method}
                    options={options(['phone', 'email', 'in_person', 'other'])}
                    change={(v) => {
                      edit('method', v);
                    }}
                  />
                  <Field
                    label={label('outcome')}
                    value={value.outcome}
                    options={options([
                      'no_answer',
                      'voicemail_left',
                      'callback_requested',
                      'contact_reached_information_pending',
                      'invalid_contact_information',
                      'information_received',
                      'other',
                    ])}
                    change={(v) => {
                      edit('outcome', v);
                    }}
                  />
                </>
              ) : null}
            </>
          ) : null}
          {field('note', 'note')}
          <label>
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => {
                setConfirmedVersion(e.target.checked ? detail.summary.version : null);
              }}
            />
            {t('confirm')}
          </label>
          {!ready && operation === 'reviews' ? <p>{t('ready')}</p> : null}
          <p role="status">{m[section.status]}</p>
          <button
            type="button"
            disabled={
              section.status !== 'unknown' &&
              (locked ||
                !confirmed ||
                (follow &&
                  (unavailable || !owners.some((owner) => owner.staff_id === value.owner_staff_id))) ||
                (operation === 'reviews' &&
                  (!ready || (outcome === 'intake_reviewed' && !detail.summary.complete))))
            }
            onClick={() => {
              setConfirmedVersion(null);
              save();
            }}
          >
            {section.status === 'unknown'
              ? m.retry
              : operation === 'reviews'
                ? t('review')
                : t(typeof value.action === 'string' ? value.action : 'reschedule')}
          </button>
        </>
      )}
    </fieldset>
  );
}
