import { useMemo } from 'react';

import type { OperationsAreaSummaryItem, OperationsZoneSummaryItem } from '../api/operationsProjectionClient';
import { buildPilotZones, type Language } from './NYCZoneMapData';

type NYCZoneMapProps = {
  areaSummary: OperationsAreaSummaryItem[];
  compact?: boolean;
  decorative?: boolean;
  language: Language;
  zoneSummary?: OperationsZoneSummaryItem[];
};

const osmTiles = [
  { gridColumn: 1, gridRow: 1, x: 300, y: 384 },
  { gridColumn: 2, gridRow: 1, x: 301, y: 384 },
  { gridColumn: 3, gridRow: 1, x: 302, y: 384 },
  { gridColumn: 1, gridRow: 2, x: 300, y: 385 },
  { gridColumn: 2, gridRow: 2, x: 301, y: 385 },
  { gridColumn: 3, gridRow: 2, x: 302, y: 385 },
  { gridColumn: 1, gridRow: 3, x: 300, y: 386 },
  { gridColumn: 2, gridRow: 3, x: 301, y: 386 },
  { gridColumn: 3, gridRow: 3, x: 302, y: 386 },
];

function countLabel(value: number, singular: string, pluralText: string) {
  return `${String(value)} ${value === 1 ? singular : pluralText}`;
}

function zoneDetail(summary: OperationsZoneSummaryItem, language: Language) {
  return language === 'es'
    ? `${countLabel(summary.requestCount, 'solicitud', 'solicitudes')} / ${countLabel(summary.workerSlots, 'cupo', 'cupos')}`
    : `${countLabel(summary.requestCount, 'request', 'requests')} / ${countLabel(summary.workerSlots, 'slot', 'slots')}`;
}

export function NYCZoneMap({ areaSummary, compact = false, decorative = false, language, zoneSummary = [] }: NYCZoneMapProps) {
  const zones = useMemo(() => buildPilotZones(areaSummary, zoneSummary), [areaSummary, zoneSummary]);

  return (
    <div className={compact ? 'nyc-zone-map nyc-zone-map--compact' : 'nyc-zone-map'}>
      <div className="nyc-zone-map__frame">
        <div
          aria-label={decorative ? undefined : language === 'es' ? 'Mapa base de NYC de OpenStreetMap' : 'OpenStreetMap NYC basemap'}
          aria-hidden={decorative ? 'true' : undefined}
          className="nyc-zone-map__base"
          role={decorative ? undefined : 'img'}
        >
          {osmTiles.map((tile) => (
            <img
              alt=""
              aria-hidden="true"
              decoding="async"
              key={`${String(tile.x)}-${String(tile.y)}`}
              loading="lazy"
              src={`https://tile.openstreetmap.org/10/${String(tile.x)}/${String(tile.y)}.png`}
              style={{ gridColumn: tile.gridColumn, gridRow: tile.gridRow }}
            />
          ))}
        </div>
        <div className="nyc-zone-map__mask" aria-hidden="true" />
        <div
          aria-label={language === 'es' ? 'Zonas operativas piloto de NYC' : 'NYC pilot operational zones'}
          className="nyc-zone-map__zones"
          role={decorative ? undefined : 'list'}
        >
          {zones.map((zone) => {
            const hasDemand = zone.summary.requestCount > 0 || zone.summary.workerSlots > 0 || zone.summary.workerResidenceCount > 0 || zone.summary.worksiteCount > 0;
            const ariaLabel = language === 'es'
              ? `${zone.label.es}. ${String(zone.summary.workerResidenceCount)} residencias de trabajadores, ${String(zone.summary.worksiteCount)} lugares de trabajo, ${String(zone.summary.requestCount)} solicitudes, ${String(zone.summary.workerSlots)} cupos.`
              : `${zone.label.en}. ${String(zone.summary.workerResidenceCount)} worker residences, ${String(zone.summary.worksiteCount)} worksites, ${String(zone.summary.requestCount)} requests, ${String(zone.summary.workerSlots)} slots.`;
            return (
              <div
                aria-label={decorative ? undefined : ariaLabel}
                className="nyc-zone-map__zone"
                data-has-demand={hasDemand ? 'true' : 'false'}
                data-intensity={zone.intensity}
                key={zone.id}
                role={decorative ? undefined : 'listitem'}
                style={{
                  height: `${String(zone.height)}%`,
                  left: `${String(zone.left)}%`,
                  top: `${String(zone.top)}%`,
                  width: `${String(zone.width)}%`,
                }}
                tabIndex={decorative ? undefined : 0}
              >
                <span className="nyc-zone-map__zone-label">
                  <strong>{zone.label[language]}</strong>
                  <span>
                    {language === 'es'
                      ? `${String(zone.summary.workerResidenceCount)} trabajadores / ${String(zone.summary.worksiteCount)} lugares`
                      : `${String(zone.summary.workerResidenceCount)} workers / ${String(zone.summary.worksiteCount)} worksites`}
                  </span>
                  <small>{zoneDetail(zone.summary, language)}</small>
                </span>
              </div>
            );
          })}
        </div>
        {decorative ? (
          <span className="nyc-zone-map__attribution">OpenStreetMap</span>
        ) : (
          <a
            className="nyc-zone-map__attribution focus-ring"
            href="https://www.openstreetmap.org/copyright"
            rel="noreferrer"
            target="_blank"
          >
            {language === 'es' ? 'Mapa: OpenStreetMap' : 'Map: OpenStreetMap'}
          </a>
        )}
      </div>
      {!compact ? (
        <p className="nyc-zone-map__note">
          {language === 'es'
            ? 'Las zonas piloto estan listas para renombrarse o combinarse; los agregados actuales se muestran sin puntos individuales ni direcciones exactas.'
            : 'Pilot zones can be renamed or combined later; current aggregates are shown without individual dots or exact addresses.'}
        </p>
      ) : null}
    </div>
  );
}
