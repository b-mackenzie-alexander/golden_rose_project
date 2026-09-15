import { useEffect, useRef, useState } from 'react';
import { queryWorkInterests, saveWorkInterest } from '../api/intakeClient';
import type { DraftObject, WorkInterest } from '../api/intakeContracts';
import { useLanguage } from '../i18n/LanguageProvider';
import { Field } from './IntakeFields';
import { intakeMessages } from './messages';
import { editSection, finishSection, initialSection, type Section } from './saveState';
import { workflowLabel } from './workflowMessages';

function useCatalog(retainPages = false) {
  const [items, setItems] = useState<WorkInterest[]>([]),
    [cursor, setCursor] = useState<string | null>(null),
    [unavailable, setUnavailable] = useState(false);
  const epoch = useRef(0);
  useEffect(() => {
    const token = ++epoch.current;
    void queryWorkInterests(undefined, true).then((result) => {
      if (token !== epoch.current) return;
      setUnavailable(!result.ok);
      setItems(result.ok ? result.value.items : []);
      setCursor(result.ok ? result.value.next_cursor : null);
    });
    const clear = () => {
      ++epoch.current;
      setItems([]);
      setCursor(null);
    };
    window.addEventListener('pagehide', clear);
    return () => {
      epoch.current = token + 1000000;
      window.removeEventListener('pagehide', clear);
    };
  }, []);
  async function more() {
    const token = ++epoch.current;
    const result = await queryWorkInterests(cursor ?? undefined, true);
    if (token !== epoch.current) return;
    setUnavailable(!result.ok);
    setItems((previous) =>
      result.ok
        ? retainPages
          ? [
              ...result.value.items,
              ...previous.filter(
                (entry) => !result.value.items.some((next) => next.interest_id === entry.interest_id),
              ),
            ]
          : result.value.items
        : [],
    );
    setCursor(result.ok ? result.value.next_cursor : null);
  }
  return { items, cursor, unavailable, more, setItems };
}
export function WorkInterestPicker({
  value,
  change,
}: {
  value: DraftObject;
  change: (value: DraftObject) => void;
}) {
  const { language } = useLanguage(),
    catalog = useCatalog(true);
  const [selectedInterest, setSelectedInterest] = useState('');
  const t = (key: string) => workflowLabel(key, language);
  const m = intakeMessages[language];
  const activeItems = catalog.items.filter((entry) => entry.active);
  const selections = (Array.isArray(value.selections) ? value.selections : []).filter(
    (item): item is { interest_id: string; catalog_version: number } =>
      !!item &&
      typeof item === 'object' &&
      !Array.isArray(item) &&
      typeof item.interest_id === 'string' &&
      typeof item.catalog_version === 'number',
  );
  function select(entry: WorkInterest, checked: boolean) {
    const remaining = selections.filter((s) => s.interest_id !== entry.interest_id);
    change({
      ...value,
      selections: checked
        ? [...remaining, { interest_id: entry.interest_id, catalog_version: entry.version }]
        : remaining,
    });
  }
  function addSelected() {
    const entry = catalog.items.find((item) => item.interest_id === selectedInterest);
    if (!entry) return;
    select(entry, true);
    setSelectedInterest('');
  }
  return (
    <fieldset>
      <legend>{t('interests')}</legend>
      {catalog.unavailable ? <p role="status">{t('unavailable')}</p> : null}
      <div className="intake-field">
        <label htmlFor="work-interest-catalog">{m.catalogInterest}</label>
        <select
          id="work-interest-catalog"
          value={selectedInterest}
          disabled={activeItems.length === 0 || selections.length >= 20}
          onChange={(event) => {
            setSelectedInterest(event.target.value);
          }}
        >
          <option value="">{activeItems.length ? m.choose : m.empty}</option>
          {activeItems.map((entry) => (
              <option
                key={entry.interest_id}
                value={entry.interest_id}
                disabled={selections.some((selection) => selection.interest_id === entry.interest_id)}
              >
                {language === 'en' ? entry.label_en : entry.label_es}
              </option>
            ))}
        </select>
      </div>
      <button type="button" disabled={!selectedInterest || selections.length >= 20} onClick={addSelected}>
        {m.addInterest}
      </button>
      {selections
        .filter(
          (s) =>
            !catalog.items.some(
              (item) =>
                item.interest_id === s.interest_id && item.version === s.catalog_version && item.active,
            ),
        )
        .map((s) => (
          <div key={s.interest_id}>
            <p>
              {t(
                catalog.items.some((entry) => entry.interest_id === s.interest_id)
                  ? 'oldSelection'
                  : 'unqueriedSelection',
              )}
              : {s.interest_id} · {s.catalog_version}
            </p>
            <button
              type="button"
              onClick={() => {
                change({
                  ...value,
                  selections: selections.filter((item) => item.interest_id !== s.interest_id),
                });
              }}
            >
              {language === 'en' ? 'Remove selection' : 'Eliminar selección'}
            </button>
          </div>
        ))}
      {selections.filter((selection) =>
        catalog.items.some((item) => item.active && item.interest_id === selection.interest_id),
      ).length ? (
        <ul>
          {selections
            .filter((selection) =>
              catalog.items.some((item) => item.active && item.interest_id === selection.interest_id),
            )
            .map((selection) => {
            const entry = catalog.items.find((item) => item.interest_id === selection.interest_id);
            return (
              <li key={selection.interest_id}>
                {entry ? (language === 'en' ? entry.label_en : entry.label_es) : selection.interest_id} ·{' '}
                {selection.catalog_version}{' '}
                <button
                  type="button"
                  onClick={() => {
                    change({
                      ...value,
                      selections: selections.filter((item) => item.interest_id !== selection.interest_id),
                    });
                  }}
                >
                  {language === 'en' ? 'Remove selection' : 'Eliminar selección'}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
      {catalog.cursor ? (
        <button type="button" onClick={() => void catalog.more()}>
          {t('more')}
        </button>
      ) : null}
    </fieldset>
  );
}
export function WorkInterestCatalog() {
  const { language } = useLanguage(),
    catalog = useCatalog();
  const t = (key: string) => workflowLabel(key, language),
    m = intakeMessages[language];
  const [selected, setSelected] = useState<WorkInterest | null>(null),
    [section, setSection] = useState<Section>(initialSection({})),
    [conflict, setConflict] = useState(false);
  const current = useRef(section),
    active = useRef(true);
  const update = (s: Section) => {
    if (!active.current) return;
    current.current = s;
    setSection(s);
  };
  useEffect(() => {
    active.current = true;
    const clear = () => {
      active.current = false;
      current.current = initialSection({});
      setSection(current.current);
      setSelected(null);
    };
    window.addEventListener('pagehide', clear);
    return () => {
      active.current = false;
      window.removeEventListener('pagehide', clear);
    };
  }, []);
  const edit = (key: string, value: unknown) => {
    update(editSection(current.current, { ...current.current.value, [key]: value as string | boolean }));
  };
  async function save() {
    if (current.current.status === 'saving' || conflict) return;
    const original = current.current;
    const command =
      original.command ??
      Object.freeze({
        key: crypto.randomUUID(),
        generation: original.generation,
        path: selected ? `/work-interests/${selected.interest_id}/revisions` : '/work-interests',
        body: structuredClone(
          selected ? { ...original.value, expected_version: selected.version } : original.value,
        ),
      });
    update({ ...original, status: 'saving', command });
    const result = await saveWorkInterest(command);
    if (!active.current) return;
    if (!result.ok) {
      if (result.failure === 'conflict') setConflict(true);
      update(
        result.failure === 'forbidden'
          ? { ...initialSection({}), status: 'unavailable' }
          : finishSection(current.current, result.failure === 'unknown' ? 'unknown' : 'failed'),
      );
      return;
    }
    if (selected && result.value.current.interest_id !== selected.interest_id) {
      update(finishSection(current.current, 'unknown'));
      return;
    }
    if (result.value.current.version > result.value.result_record_version) {
      setConflict(true);
      update(finishSection(current.current, 'saved'));
      return;
    }
    setSelected(result.value.current);
    catalog.setItems((previous) => [
      result.value.current,
      ...previous.filter((item) => item.interest_id !== result.value.current.interest_id),
    ]);
    const finished = finishSection(current.current, 'saved');
    update({
      ...finished,
      value:
        finished.status === 'saved'
          ? {
              label_en: result.value.current.label_en,
              label_es: result.value.current.label_es,
              active: result.value.current.active,
            }
          : {
              label_en: finished.value.label_en ?? result.value.current.label_en,
              label_es: finished.value.label_es ?? result.value.current.label_es,
              active: finished.value.active ?? result.value.current.active,
            },
    });
  }
  const locked = section.status === 'saving' || section.status === 'unknown';
  return (
    <div className="intake-workspace">
      <h2>{t('catalog')}</h2>
      <p>{t('manageMeaning')}</p>
      {catalog.unavailable ? <p role="status">{t('unavailable')}</p> : null}
      <ul>
        {catalog.items.map((entry) => (
          <li key={entry.interest_id}>
            {language === 'en' ? entry.label_en : entry.label_es} · {entry.code} · {entry.version} ·{' '}
            {t(entry.active ? 'active' : 'retired')}{' '}
            <button
              type="button"
              disabled={locked}
              onClick={() => {
                setSelected(entry);
                setConflict(false);
                update(
                  initialSection({
                    label_en: entry.label_en,
                    label_es: entry.label_es,
                    active: entry.active,
                  }),
                );
              }}
            >
              {t('revise')}
            </button>
          </li>
        ))}
      </ul>
      {catalog.cursor ? (
        <button type="button" onClick={() => void catalog.more()}>
          {t('more')}
        </button>
      ) : null}
      <button
        type="button"
        disabled={locked}
        onClick={() => {
          setSelected(null);
          setConflict(false);
          update(initialSection({}));
        }}
      >
        {t('create')}
      </button>
      {section.status === 'unavailable' ? (
        <p role="status">{t('unavailable')}</p>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void save();
          }}
        >
          <fieldset>
            <legend>{t('manage')}</legend>
            {!selected ? (
              <Field
                label={['Immutable code', 'Código inmutable']}
                max={64}
                value={section.value.code}
                change={(v) => {
                  edit('code', v ?? '');
                }}
              />
            ) : (
              <p>{selected.code}</p>
            )}
            <Field
              label={['English label', 'Etiqueta en inglés']}
              max={100}
              value={section.value.label_en}
              change={(v) => {
                edit('label_en', v ?? '');
              }}
            />
            <Field
              label={['Spanish label', 'Etiqueta en español']}
              max={100}
              value={section.value.label_es}
              change={(v) => {
                edit('label_es', v ?? '');
              }}
            />
            {selected ? (
              <label>
                <input
                  type="checkbox"
                  checked={section.value.active === true}
                  onChange={(e) => {
                    edit('active', e.target.checked);
                  }}
                />
                {t('active')}
              </label>
            ) : null}
            <p role="status">{conflict ? m.conflict : m[section.status]}</p>
            <button type="submit" disabled={conflict || section.status === 'saving'}>
              {section.status === 'unknown' ? m.retry : t('save')}
            </button>
          </fieldset>
        </form>
      )}
    </div>
  );
}
