import { useEffect, useRef, useState } from 'react';
import { queryFollowUpOwners } from '../api/intakeClient';
import type { DraftObject, IntakeDetail, StaffChoice } from '../api/intakeContracts';
import { useLanguage } from '../i18n/LanguageProvider';
import { offsetInstantToLocalDateTime, zonedLocalDateTimeToOffsetInstant } from '../time/timeZone';
import { normalizedTimeZone, timeZoneOptions } from '../time/timeZoneOptions';
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
  const reviewSubmission = operation === 'reviews' && outcome === 'intake_reviewed';
  const workflowTimeZone = normalizedTimeZone(value.time_zone);
  const followUpLocalDue =
    offsetInstantToLocalDateTime(value.next_follow_up_at) ??
    (typeof value.next_follow_up_at === 'string' ? value.next_follow_up_at : undefined);
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
                    : { action: 'reschedule', time_zone: workflowTimeZone }),
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
                const nextOutcome = v ?? 'intake_reviewed';
                change({
                  operation,
                  outcome: nextOutcome,
                  ...(nextOutcome === 'needs_follow_up' ? { time_zone: workflowTimeZone } : {}),
                });
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
              <Field
                label={label('due')}
                value={followUpLocalDue}
                type="datetime-local"
                max={100}
                change={(v) => {
                  const instant =
                    typeof v === 'string' ? zonedLocalDateTimeToOffsetInstant(v, workflowTimeZone) : null;
                  edit('next_follow_up_at', instant ?? v);
                }}
              />
              <p>
                {language === 'en'
                  ? 'Choose the local due date and time, then choose the matching time zone. Past deadlines are allowed.'
                  : 'Elija la fecha y hora límite local y luego la zona horaria correspondiente. Se permiten fechas vencidas.'}
              </p>
              <Field
                label={label('zone')}
                value={workflowTimeZone}
                options={timeZoneOptions}
                change={(v) => {
                  const nextTimeZone = normalizedTimeZone(v);
                  const nextDue =
                    typeof followUpLocalDue === 'string'
                      ? zonedLocalDateTimeToOffsetInstant(followUpLocalDue, nextTimeZone) ?? value.next_follow_up_at
                      : value.next_follow_up_at;
                  setConfirmedVersion(null);
                  const next: DraftObject = {
                    ...value,
                    operation,
                    time_zone: nextTimeZone,
                  };
                  if (nextDue === undefined) delete next.next_follow_up_at;
                  else next.next_follow_up_at = nextDue;
                  change(next);
                }}
              />
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
              : reviewSubmission
                ? t('submitReview')
                : operation === 'reviews'
                ? t('review')
                : t(typeof value.action === 'string' ? value.action : 'reschedule')}
          </button>
        </>
      )}
    </fieldset>
  );
}
