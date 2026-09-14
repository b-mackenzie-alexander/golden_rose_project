import { useId } from 'react';
import type { DraftObject, DraftValue, IntakeKind } from '../api/intakeContracts';
import { useLanguage } from '../i18n/LanguageProvider';
import { countries, currencies } from './catalogs';
import { intakeMessages } from './messages';

type Label = readonly [string, string];
type FieldProps = {
  label: Label;
  value: DraftValue | undefined;
  change: (value: DraftValue | undefined) => void;
  type?: string;
  max?: number;
  options?: readonly (readonly [string, string, string])[];
};
export function Field({ label, value, change, type = 'text', max = 200, options }: FieldProps) {
  const id = useId();
  const { language } = useLanguage();
  const m = intakeMessages[language];
  const inputValue = typeof value === 'string' || typeof value === 'number' ? value : '';
  const text = label[language === 'en' ? 0 : 1];
  return (
    <div className="intake-field">
      <label htmlFor={id}>{text}</label>
      {options ? (
        <select
          id={id}
          value={String(inputValue)}
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
    </div>
  );
}
const obj = (value: DraftValue | undefined): DraftObject =>
  value && typeof value === 'object' && !Array.isArray(value) ? value : {};
function withValue(object: DraftObject, key: string, value: DraftValue | undefined): DraftObject {
  return value === undefined
    ? Object.fromEntries(Object.entries(object).filter(([name]) => name !== key))
    : { ...object, [key]: value };
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
    ['country', ['Country code (2 uppercase letters)', 'Código de país (2 letras mayúsculas)'], 2],
  ];
  return (
    <div className="intake-fields">
      {fields.map(([key, label, max]) => (
        <Field
          key={key}
          label={label}
          max={max}
          options={key === 'country' ? countries.map((code) => [code, code, code] as const) : undefined}
          value={value[key]}
          change={(v) => {
            change(withValue(value, key, v));
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
}: {
  kind: IntakeKind;
  value: DraftObject;
  change: (value: DraftObject) => void;
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
  return (
    <>
      <div className="intake-fields">
        {kind === 'worker' ? (
          field('full_name', ['Full name', 'Nombre completo'])
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
        {field('phone', ['Phone', 'Teléfono'], 'tel', 40)}
      </div>
      {kind === 'worker' ? (
        <>
          <p>{m.selfReported}</p>
          <Field
            label={['Other work interests', 'Otros intereses laborales']}
            value={obj(value.interests).other_description}
            change={(v) => {
              nested('interests', 'other_description', v);
            }}
          />
          <Field
            label={['Availability', 'Disponibilidad']}
            value={availability.mode}
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
              ['flexible', 'Flexible / discuss with staff', 'Flexible / hablar con el personal'],
              ['weekly', 'Weekly', 'Semanal'],
            ]}
          />
          {availability.mode === 'weekly' ? (
            <fieldset>
              <legend>{m.weekly}</legend>
              <Field
                label={['IANA time zone', 'Zona horaria IANA']}
                value={availability.time_zone}
                change={(v) => {
                  nested('availability', 'time_zone', v);
                }}
              />
              {ranges.map((range, index) => (
                <div className="intake-range" key={index}>
                  <Field
                    label={['Weekday (Monday = 1, Sunday = 7)', 'Día (lunes = 1, domingo = 7)']}
                    type="number"
                    value={range.weekday}
                    change={(v) => {
                      nested(
                        'availability',
                        'ranges',
                        ranges.map((r, i) => (i === index ? withValue(r, 'weekday', v) : r)),
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
                          ranges.map((r, j) => (j === index ? withValue(r, key, v) : r)),
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
                        ranges.map((r, j) =>
                          j === index
                            ? withValue(r, 'end_day_offset', v === undefined ? undefined : Number(v))
                            : r,
                        ),
                      );
                    }}
                  />
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
                  nested('availability', 'ranges', [...ranges, {}]);
                }}
              >
                {m.add}
              </button>
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
