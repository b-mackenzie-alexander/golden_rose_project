import { useEffect, useRef, useState } from 'react';
import { getRestrictedHistory, queryIntakeHistory } from '../api/intakeClient';
import type { HistoryItem, RestrictedHistory, DraftValue } from '../api/intakeContracts';
import { useLanguage } from '../i18n/LanguageProvider';
import { snapshotEnums, snapshotLabels, workflowLabel } from './workflowMessages';

function localDateTime(value: string, language: 'en' | 'es') {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(language === 'en' ? 'en-US' : 'es-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
    hour12: true,
  }).format(date);
}

export function Snapshot({ value, field }: { value: DraftValue; field?: string }) {
  const { language } = useLanguage();
  if (value === null) return null;
  if (typeof value !== 'object')
    return (
      <span>
        {typeof value === 'boolean'
          ? value
            ? language === 'en'
              ? 'Yes'
              : 'Sí'
            : language === 'en'
              ? 'No'
              : 'No'
          : typeof value === 'string' && field
            ? (snapshotEnums[field]?.[value]?.[language === 'en' ? 0 : 1] ?? value)
            : String(value)}
      </span>
    );
  if (Array.isArray(value))
    return (
      <ol>
        {value.map((item, index) => (
          <li key={index}>
            <Snapshot value={item} />
          </li>
        ))}
      </ol>
    );
  return (
    <dl>
      {Object.entries(value).map(([key, item]) => (
        <div key={key}>
          <dt>{snapshotLabels[key]?.[language === 'en' ? 0 : 1] ?? workflowLabel(key, language)}</dt>
          <dd>
            <Snapshot value={item} field={key} />
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function IntakeHistory({ id, version }: { id: string; version: number }) {
  const { language } = useLanguage();
  const t = (key: string) => workflowLabel(key, language);
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [cursor, setCursor] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [restricted, setRestricted] = useState<RestrictedHistory | null>(null);
  const [denied, setDenied] = useState(false);
  const epoch = useRef(0),
    revealEpoch = useRef(0);
  useEffect(() => {
    const request = ++epoch.current;
    ++revealEpoch.current;
    void queryIntakeHistory(id).then((result) => {
      if (epoch.current !== request) return;
      setRestricted(null);
      setSelected(null);
      setDenied(false);
      setFailed(!result.ok);
      setItems(result.ok ? result.value.items : null);
      setCursor(result.ok ? result.value.next_cursor : null);
    });
    const clear = () => {
      ++epoch.current;
      ++revealEpoch.current;
      setItems(null);
      setRestricted(null);
      setSelected(null);
      setCursor(null);
    };
    window.addEventListener('pagehide', clear);
    return () => {
      epoch.current = request + 1000000;
      revealEpoch.current = request + 1000000;
      window.removeEventListener('pagehide', clear);
    };
  }, [id, version]);
  async function more() {
    const request = ++epoch.current;
    const result = await queryIntakeHistory(id, cursor ?? undefined);
    if (request !== epoch.current) return;
    setFailed(!result.ok);
    setItems(result.ok ? result.value.items : null);
    setCursor(result.ok ? result.value.next_cursor : null);
    ++revealEpoch.current;
    setRestricted(null);
    setSelected(null);
  }
  async function reveal(eventId: string) {
    const request = ++revealEpoch.current;
    setRestricted(null);
    setDenied(false);
    setSelected(eventId);
    const result = await getRestrictedHistory(id, eventId);
    if (request !== revealEpoch.current) return;
    setDenied(!result.ok);
    setRestricted(result.ok ? result.value : null);
  }
  return (
    <section aria-label={t('history')}>
      <h3>{t('history')}</h3>
      {failed ? (
        <p role="status">{t('unavailable')}</p>
      ) : items?.length === 0 ? (
        <p>{t('empty')}</p>
      ) : null}
      <ul>
        {items?.map((item) => (
          <li className="intake-history-item" key={item.event_id}>
            <p className="intake-history-event">{t(item.event_type)}</p>
            <dl className="intake-history-meta">
              <div>
                <dt>{t('updatedAt')}</dt>
                <dd>
                  <time dateTime={item.occurred_at}>{localDateTime(item.occurred_at, language)}</time>
                </dd>
              </div>
              <div>
                <dt>{t('actor')}</dt>
                <dd>{item.actor_display_name}</dd>
              </div>
              <div>
                <dt>{t('version')}</dt>
                <dd>{item.version}</dd>
              </div>
              <div>
                <dt>{t('contentVersion')}</dt>
                <dd>{item.content_version}</dd>
              </div>
              {item.outcome ? (
                <div>
                  <dt>{t('outcome')}</dt>
                  <dd>{t(item.outcome)}</dd>
                </div>
              ) : null}
            </dl>
            {item.owner_staff_id ? (
              <p>
                {t('owner')}: {item.owner_staff_id}
                {item.next_follow_up_at ? (
                  <>
                    {' · '}
                    <time dateTime={item.next_follow_up_at}>
                      {localDateTime(item.next_follow_up_at, language)}
                    </time>
                  </>
                ) : null}
              </p>
            ) : null}
            <button type="button" onClick={() => void reveal(item.event_id)}>
              {t('reveal')}
            </button>
            {selected === item.event_id ? (
              <div>
                {denied ? (
                  <p role="status">{t('unavailable')}</p>
                ) : restricted ? (
                  <>
                    <p>{restricted.note ?? t('noNote')}</p>
                    {restricted.follow_up ? (
                      <dl>
                        <dt>{t('action')}</dt>
                        <dd>{t(restricted.follow_up.action)}</dd>
                        {restricted.follow_up.reason_code ? (
                          <>
                            <dt>{t('reasonCode')}</dt>
                            <dd>{t(restricted.follow_up.reason_code)}</dd>
                          </>
                        ) : null}
                        <dt>{t('reason')}</dt>
                        <dd>{restricted.follow_up.reason_text}</dd>
                        <dt>{t('zone')}</dt>
                        <dd>{restricted.follow_up.time_zone}</dd>
                        {restricted.follow_up.method ? (
                          <>
                            <dt>{t('method')}</dt>
                            <dd>{t(restricted.follow_up.method)}</dd>
                          </>
                        ) : null}
                        {restricted.follow_up.outcome ? (
                          <>
                            <dt>{t('outcome')}</dt>
                            <dd>{t(restricted.follow_up.outcome)}</dd>
                          </>
                        ) : null}
                      </dl>
                    ) : null}
                    {restricted.reviewed_content ? (
                      <>
                        <h4>{t('snapshot')}</h4>
                        <Snapshot value={restricted.reviewed_content} />
                      </>
                    ) : null}
                  </>
                ) : null}
                <button
                  type="button"
                  onClick={() => {
                    ++revealEpoch.current;
                    setRestricted(null);
                    setSelected(null);
                    setDenied(false);
                  }}
                >
                  {t('hide')}
                </button>
              </div>
            ) : null}
          </li>
        ))}
      </ul>
      {cursor ? (
        <button type="button" onClick={() => void more()}>
          {t('more')}
        </button>
      ) : null}
    </section>
  );
}
