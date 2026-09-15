import { useEffect, useId, useRef, useState } from 'react';
import type { DraftObject, DraftValue, IntakeKind } from '../api/intakeContracts';
import { useLanguage } from '../i18n/LanguageProvider';
import { currencies } from './catalogs';
import { intakeMessages } from './messages';
import { WorkInterestPicker } from './WorkInterests';

type Label = readonly [string, string];
type FieldProps = {
  label: Label;
  value: DraftValue | undefined;
  change: (value: DraftValue | undefined) => void;
  type?: string;
  max?: number;
  options?: readonly (readonly [string, string, string])[];
  error?: string;
};
export function Field({ label, value, change, type = 'text', max = 200, options, error }: FieldProps) {
  const id = useId();
  const errorId = `${id}-error`;
  const { language } = useLanguage();
  const m = intakeMessages[language];
  const inputValue = typeof value === 'string' || typeof value === 'number' ? value : '';
  const text = label[language === 'en' ? 0 : 1];
  const describedBy = error ? errorId : undefined;
  return (
    <div className={`intake-field${error ? ' intake-field--invalid' : ''}`}>
      <label htmlFor={id}>
        {text}
        {error ? (
          <span className="intake-field-help" title={error} aria-hidden="true">
            ?
          </span>
        ) : null}
      </label>
      {options ? (
        <select
          id={id}
          value={String(inputValue)}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={describedBy}
          onChange={(event) => {
            change(event.target.value || undefined);
          }}
        >
          <option value="">{m.choose}</option>
          {options.map(([key, en, es]) => (
            <option key={key} value={key}>
              {language === 'en' ? en : es}
            </option>
          ))}
        </select>
      ) : type === 'textarea' ? (
        <textarea
          id={id}
          maxLength={max}
          value={inputValue}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={describedBy}
          onChange={(event) => {
            change(event.target.value || undefined);
          }}
        />
      ) : (
        <input
          id={id}
          type={type}
          maxLength={max}
          value={inputValue}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={describedBy}
          onChange={(event) => {
            change(
              event.target.value
                ? type === 'number'
                  ? Number(event.target.value)
                  : event.target.value
                : undefined,
            );
          }}
        />
      )}
      {error ? (
        <p className="intake-field-error" id={errorId}>
          {error}
        </p>
      ) : null}
    </div>
  );
}
const obj = (value: DraftValue | undefined): DraftObject =>
  value && typeof value === 'object' && !Array.isArray(value) ? value : {};
const textList = (value: DraftValue | undefined) =>
  typeof value === 'string'
    ? value
        .split(';')
        .map((item) => item.trim())
        .filter(Boolean)
    : [];
const interestText = (items: string[]) => Array.from(new Set(items.map((item) => item.trim()).filter(Boolean))).join('; ');
function splitWorkerName(value: DraftValue | undefined) {
  const parts = typeof value === 'string' ? value.trim().split(/\s+/).filter(Boolean) : [];
  if (parts.length === 0) return { first: '', middle: '', last: '' };
  if (parts.length === 1) return { first: parts[0] ?? '', middle: '', last: '' };
  if (parts.length === 2) return { first: parts[0] ?? '', middle: '', last: parts[1] ?? '' };
  return { first: parts[0] ?? '', middle: parts.slice(1, -1).join(' '), last: parts.at(-1) ?? '' };
}
function joinWorkerName(first: string, middle: string, last: string) {
  return [first.trim(), middle.trim(), last.trim()].filter(Boolean).join(' ') || undefined;
}
type WorkerNameParts = ReturnType<typeof splitWorkerName>;
function WorkerNameFields({
  value,
  change,
  labels,
  showValidation = false,
}: {
  value: DraftValue | undefined;
  change: (value: DraftValue | undefined) => void;
  labels: {
    firstName: string;
    middleInitial: string;
    lastName: string;
    firstNameRequired: string;
    lastNameRequired: string;
  };
  showValidation?: boolean;
}) {
  const source = typeof value === 'string' ? value : '';
  const lastEmitted = useRef(source);
  const [parts, setParts] = useState<WorkerNameParts>(() => splitWorkerName(source));
  useEffect(() => {
    if (source === lastEmitted.current) return;
    lastEmitted.current = source;
    setParts(splitWorkerName(source));
  }, [source]);
  const setPart = (part: keyof WorkerNameParts, next: DraftValue | undefined) => {
    setParts((previous) => {
      const draft = { ...previous, [part]: typeof next === 'string' ? next : '' };
      const joined = joinWorkerName(draft.first, draft.middle, draft.last);
      lastEmitted.current = joined ?? '';
      change(joined);
      return draft;
    });
  };
  const firstError = showValidation && !parts.first.trim() ? labels.firstNameRequired : undefined;
  const lastError = showValidation && !parts.last.trim() ? labels.lastNameRequired : undefined;
  return (
    <>
      <Field
        label={[labels.firstName, labels.firstName]}
        value={parts.first}
        error={firstError}
        change={(v) => {
          setPart('first', v);
        }}
      />
      <Field
        label={[labels.middleInitial, labels.middleInitial]}
        value={parts.middle}
        max={10}
        change={(v) => {
          setPart('middle', v);
        }}
      />
      <Field
        label={[labels.lastName, labels.lastName]}
        value={parts.last}
        error={lastError}
        change={(v) => {
          setPart('last', v);
        }}
      />
    </>
  );
}
function normalizeUsPhone(value: string) {
  const digits = value.replace(/\D/g, '');
  if (digits.length === 10) return `+1${digits}`;
  if (digits.length === 11 && digits.startsWith('1')) return `+${digits}`;
  return value || undefined;
}
function withValue(object: DraftObject, key: string, value: DraftValue | undefined): DraftObject {
  return value === undefined
    ? Object.fromEntries(Object.entries(object).filter(([name]) => name !== key))
    : { ...object, [key]: value };
}
function addressWithUsCountry(value: DraftObject): DraftObject {
  const content = value;
  return Object.keys(content).length ? { ...content, country: 'US' } : {};
}
export function AddressFields({
  value,
  change,
}: {
  value: DraftObject;
  change: (value: DraftObject) => void;
}) {
  const fields: [string, Label, number][] = [
    ['line1', ['Address line 1', 'Dirección, línea 1'], 200],
    ['line2', ['Address line 2', 'Dirección, línea 2'], 200],
    ['locality', ['City / locality', 'Ciudad / localidad'], 100],
    ['region', ['State / region', 'Estado / región'], 100],
    ['postal_code', ['Postal code', 'Código postal'], 32],
  ];
  return (
    <div className="intake-fields">
      {fields.map(([key, label, max]) => (
        <Field
          key={key}
          label={label}
          max={max}
          value={value[key]}
          change={(v) => {
            change(addressWithUsCountry(withValue(value, key, v)));
          }}
        />
      ))}
    </div>
  );
}
export function IntakeFields({
  kind,
  value,
  change,
  sectionOnly = false,
  showValidation = false,
}: {
  kind: IntakeKind;
  sectionOnly?: boolean;
  value: DraftObject;
  change: (value: DraftObject) => void;
  showValidation?: boolean;
}) {
  const { language } = useLanguage();
  const m = intakeMessages[language];
  const field = (key: string, label: Label, type = 'text', max = 200) => (
    <Field
      key={key}
      label={label}
      type={type}
      max={max}
      value={value[key]}
      change={(v) => {
        change(withValue(value, key, v));
      }}
    />
  );
  const nested = (section: string, key: string, v: DraftValue | undefined) => {
    change({ ...value, [section]: withValue(obj(value[section]), key, v) });
  };
  const availability = obj(value.availability);
  const schedule = obj(value.schedule);
  const offer = obj(value.offer);
  const ranges = Array.isArray(availability.ranges) ? availability.ranges.map(obj) : [];
  const manualInterests = textList(obj(value.interests).other_description);
  const selections = obj(value.interests).selections;
  const hasCatalogInterest = Array.isArray(selections) && selections.length > 0;
  const phoneDigits = typeof value.phone === 'string' ? value.phone.replace(/\D/g, '') : '';
  const workerIssues = kind === 'worker' && showValidation ? {
    phone: phoneDigits.length < 7 || phoneDigits.length > 15 ? m.phoneRequired : undefined,
    interests: !hasCatalogInterest && !manualInterests.length ? m.interestsRequired : undefined,
    availability: typeof availability.mode === 'string' ? undefined : m.availabilityRequired,
    timeZone:
      availability.mode === 'weekly' && typeof availability.time_zone !== 'string'
        ? m.timeZoneRequired
        : undefined,
    ranges: availability.mode === 'weekly' && !ranges.length ? m.rangesRequired : undefined,
  } : {};
  const hasDuplicateRange = ranges.some((range, index) =>
    ranges.some((other, otherIndex) =>
      index !== otherIndex &&
      range.weekday === other.weekday &&
      range.start_local === other.start_local &&
      range.end_local === other.end_local &&
      range.end_day_offset === other.end_day_offset,
    ),
  );
  const dedupeRanges = (next: DraftObject[]) => next.filter((range, index) =>
    next.findIndex((other) =>
      other.weekday === range.weekday &&
      other.start_local === range.start_local &&
      other.end_local === range.end_local &&
      other.end_day_offset === range.end_day_offset,
    ) === index,
  );
  const setRanges = (next: DraftObject[]) => {
    nested('availability', 'ranges', dedupeRanges(next));
  };
  const weekdays = [
    ['1', 'Monday', 'lunes'],
    ['2', 'Tuesday', 'martes'],
    ['3', 'Wednesday', 'miércoles'],
    ['4', 'Thursday', 'jueves'],
    ['5', 'Friday', 'viernes'],
    ['6', 'Saturday', 'sábado'],
    ['7', 'Sunday', 'domingo'],
  ] as const;
  const setManualInterest = (index: number, interest: string) => {
    const next = [...manualInterests];
    if (interest.trim()) next[index] = interest;
    else next.splice(index, 1);
    nested('interests', 'other_description', next.length ? interestText(next) : undefined);
  };
  return (
    <>
      {!sectionOnly ? <div className="intake-fields">
        {kind === 'worker' ? (
          <WorkerNameFields
            value={value.full_name}
            labels={m}
            showValidation={showValidation}
            change={(v) => {
              change(withValue(value, 'full_name', v));
            }}
          />
        ) : (
          <>
            <Field
              label={['Employer type', 'Tipo de empleador']}
              value={value.employer_type}
              change={(v) => {
                change(withValue(value, 'employer_type', v));
              }}
              options={[
                ['household', 'Household', 'Hogar'],
                ['business', 'Business', 'Empresa'],
              ]}
            />
            {field('display_name', ['Employer name', 'Nombre del empleador'])}
            {field('representative_name', ['Representative name', 'Nombre del representante'])}
          </>
        )}
        <Field
          label={['Phone', 'Teléfono']}
          type="tel"
          max={40}
          value={value.phone}
          error={workerIssues.phone}
          change={(v) => {
            change(withValue(value, 'phone', typeof v === 'string' ? normalizeUsPhone(v) : undefined));
          }}
        />
      </div> : null}
      {kind === 'worker' ? (
        <>
          <p>{m.selfReported}</p>
          <WorkInterestPicker
            value={obj(value.interests)}
            change={(v) => {
              change({ ...value, interests: v });
            }}
          />
          {workerIssues.interests ? (
            <p className="intake-field-error" role="status">
              <span className="intake-field-help" title={workerIssues.interests} aria-hidden="true">
                ?
              </span>{' '}
              {workerIssues.interests}
            </p>
          ) : null}
          <fieldset>
            <legend>{m.selectedManualInterests}</legend>
            {[...manualInterests, ''].slice(0, 20).map((interest, index) => (
              <div className="intake-range" key={`manual-interest-${String(index)}`}>
                <Field
                  label={[
                    `${m.manualInterest} ${String(index + 1)}`,
                    `${m.manualInterest} ${String(index + 1)}`,
                  ]}
                  value={interest}
                  change={(v) => {
                    setManualInterest(index, typeof v === 'string' ? v : '');
                  }}
                />
                {interest ? (
                  <button
                    type="button"
                    onClick={() => {
                      setManualInterest(index, '');
                    }}
                  >
                    {m.removeInterest}
                  </button>
                ) : null}
              </div>
            ))}
          </fieldset>
          <Field
            label={['Availability', 'Disponibilidad']}
            value={availability.mode}
            error={workerIssues.availability}
            change={(v) => {
              change(
                withValue(
                  value,
                  'availability',
                  v
                    ? {
                        mode: v,
                        ...(availability.exception_note
                          ? { exception_note: availability.exception_note }
                          : {}),
                      }
                    : undefined,
                ),
              );
            }}
            options={[
              ['unknown', 'Unknown', 'Desconocida'],
              ['flexible', 'Flexible', 'Flexible'],
              ['weekly', 'Specific days', 'Días específicos'],
            ]}
          />
          {availability.mode === 'weekly' ? (
            <fieldset>
              <legend>{m.weekly}</legend>
              <Field
                label={['IANA time zone', 'Zona horaria IANA']}
                value={availability.time_zone}
                error={workerIssues.timeZone}
                change={(v) => {
                  nested('availability', 'time_zone', v);
                }}
              />
              {workerIssues.ranges ? (
                <p className="intake-field-error" role="status">
                  <span className="intake-field-help" title={workerIssues.ranges} aria-hidden="true">
                    ?
                  </span>{' '}
                  {workerIssues.ranges}
                </p>
              ) : null}
              {ranges.map((range, index) => (
                <div className="intake-range" key={index}>
                  <Field
                    label={['Day', 'Día']}
                    value={range.weekday}
                    options={weekdays}
                    change={(v) => {
                      nested(
                          'availability',
                          'ranges',
                          dedupeRanges(ranges.map((r, i) =>
                            i === index
                              ? withValue(r, 'weekday', v === undefined ? undefined : Number(v))
                              : r,
                          )),
                      );
                    }}
                  />
                  {(['start_local', 'end_local'] as const).map((key, i) => (
                    <Field
                      key={key}
                      label={i ? ['End time', 'Hora final'] : ['Start time', 'Hora inicial']}
                      type="time"
                      value={range[key]}
                      change={(v) => {
                        nested(
                          'availability',
                          'ranges',
                          dedupeRanges(ranges.map((r, j) => (j === index ? withValue(r, key, v) : r))),
                        );
                      }}
                    />
                  ))}
                  <Field
                    label={['Ends on', 'Finaliza el']}
                    value={range.end_day_offset}
                    options={[
                      ['0', 'Same day', 'Mismo día'],
                      ['1', 'Next day', 'Día siguiente'],
                    ]}
                    change={(v) => {
                      nested(
                          'availability',
                          'ranges',
                          dedupeRanges(ranges.map((r, j) =>
                            j === index
                              ? withValue(r, 'end_day_offset', v === undefined ? undefined : Number(v))
                              : r,
                          )),
                      );
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setRanges(ranges.map((r, i) => i === index
                        ? { ...r, start_local: '00:00', end_local: '00:00', end_day_offset: 1 }
                        : r));
                    }}
                  >
                    {m.anyTime}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      const source = {
                        start_local: range.start_local ?? '09:00',
                        end_local: range.end_local ?? '17:00',
                        end_day_offset: range.end_day_offset ?? 0,
                      };
                      setRanges([1, 2, 3, 4, 5].map((weekday) => ({ weekday, ...source })));
                    }}
                  >
                    {m.copyWeekdays}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      const source = {
                        start_local: range.start_local ?? '09:00',
                        end_local: range.end_local ?? '17:00',
                        end_day_offset: range.end_day_offset ?? 0,
                      };
                      setRanges([1, 2, 3, 4, 5, 6, 7].map((weekday) => ({ weekday, ...source })));
                    }}
                  >
                    {m.copyAllDays}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      nested(
                        'availability',
                        'ranges',
                        ranges.filter((_, i) => i !== index),
                      );
                    }}
                  >
                    {m.remove}
                  </button>
                </div>
              ))}
              <button
                type="button"
                disabled={ranges.length >= 28}
                onClick={() => {
                  setRanges([
                    ...ranges,
                    { weekday: 1, start_local: '09:00', end_local: '17:00', end_day_offset: 0 },
                  ]);
                }}
              >
                {m.add}
              </button>
              {hasDuplicateRange ? <p role="status">{m.duplicateBlock}</p> : null}
            </fieldset>
          ) : null}
          <Field
            label={['Availability exception note', 'Nota de excepción de disponibilidad']}
            max={500}
            value={availability.exception_note}
            change={(v) => {
              nested('availability', 'exception_note', v);
            }}
          />
        </>
      ) : (
        <>
          <div className="intake-fields">
            {field('role_title', ['Role title', 'Puesto solicitado'])}
            {field('worker_count', ['Number of workers', 'Número de trabajadores'], 'number')}
            {field('duties_summary', ['Duties', 'Funciones'], 'textarea', 1000)}
          </div>
          <Field
            label={['Requested schedule', 'Horario solicitado']}
            value={schedule.mode}
            options={[
              ['unknown', 'Unknown', 'Desconocido'],
              ['to_be_discussed', 'To be discussed', 'Por conversar'],
              ['specified', 'Specified', 'Especificado'],
            ]}
            change={(v) => {
              change(
                withValue(
                  value,
                  'schedule',
                  v ? { mode: v, ...(schedule.note ? { note: schedule.note } : {}) } : undefined,
                ),
              );
            }}
          />
          {schedule.mode === 'specified' ? (
            <div className="intake-fields">
              <Field
                label={[
                  'Requested start date (or use timed interval)',
                  'Fecha de inicio (o utilice intervalo con hora)',
                ]}
                type="date"
                value={schedule.requested_start_date}
                change={(v) => {
                  nested('schedule', 'requested_start_date', v);
                }}
              />
              <Field
                label={['Start instant with UTC offset', 'Inicio con desplazamiento UTC']}
                value={schedule.starts_at}
                change={(v) => {
                  nested('schedule', 'starts_at', v);
                }}
              />
              <Field
                label={['End instant with UTC offset', 'Fin con desplazamiento UTC']}
                value={schedule.ends_at}
                change={(v) => {
                  nested('schedule', 'ends_at', v);
                }}
              />
              <Field
                label={['Schedule IANA time zone', 'Zona horaria IANA del horario']}
                value={schedule.time_zone}
                change={(v) => {
                  nested('schedule', 'time_zone', v);
                }}
              />
            </div>
          ) : null}
          <Field
            label={['Schedule note', 'Nota del horario']}
            max={500}
            value={schedule.note}
            change={(v) => {
              nested('schedule', 'note', v);
            }}
          />
          <fieldset>
            <legend>{m.offer}</legend>
            {typeof offer.minimum === 'string' && /^0(?:\.0{1,2})?$/.test(offer.minimum) ? (
              <p role="status">{m.zeroOffer}</p>
            ) : null}
            <div className="intake-fields">
              <Field
                label={['Minimum amount (decimal)', 'Importe mínimo (decimal)']}
                value={offer.minimum}
                change={(v) => {
                  nested('offer', 'minimum', v);
                }}
              />
              <Field
                label={['Maximum amount (optional)', 'Importe máximo (opcional)']}
                value={offer.maximum}
                change={(v) => {
                  nested('offer', 'maximum', v);
                }}
              />
              <Field
                label={['Currency code (3 uppercase letters)', 'Moneda (3 letras mayúsculas)']}
                max={3}
                options={currencies.map((code) => [code, code, code] as const)}
                value={offer.currency}
                change={(v) => {
                  nested('offer', 'currency', v);
                }}
              />
              <Field
                label={['Pay basis', 'Base del pago']}
                value={offer.basis}
                options={[
                  ['hour', 'Hour', 'Hora'],
                  ['day', 'Day', 'Día'],
                  ['week', 'Week', 'Semana'],
                  ['month', 'Month', 'Mes'],
                  ['year', 'Year', 'Año'],
                  ['task', 'Task', 'Tarea'],
                ]}
                change={(v) => {
                  nested('offer', 'basis', v);
                }}
              />
            </div>
            <label>
              <input
                type="checkbox"
                checked={offer.per_worker === true}
                onChange={(e) => {
                  nested('offer', 'per_worker', e.target.checked ? true : undefined);
                }}
              />
              {language === 'en' ? 'Amount is per worker' : 'Importe por trabajador'}
            </label>
            <label>
              <input
                type="checkbox"
                checked={offer.negotiable === true}
                onChange={(e) => {
                  nested('offer', 'negotiable', e.target.checked);
                }}
              />
              {language === 'en' ? 'Negotiable' : 'Negociable'}
            </label>
            <Field
              label={['Offer terms', 'Condiciones de la oferta']}
              type="textarea"
              max={500}
              value={offer.terms}
              change={(v) => {
                nested('offer', 'terms', v);
              }}
            />
          </fieldset>
        </>
      )}
    </>
  );
}
