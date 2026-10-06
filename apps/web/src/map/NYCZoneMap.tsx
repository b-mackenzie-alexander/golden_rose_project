import { useMemo } from 'react';

import type { OperationsAreaSummaryItem } from '../api/operationsProjectionClient';
import { buildPilotZones, type Language } from './NYCZoneMapData';

type NYCZoneMapProps = {
  areaSummary: OperationsAreaSummaryItem[];
  compact?: boolean;
  decorative?: boolean;
  language: Language;
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

export function NYCZoneMap({ areaSummary, compact = false, decorative = false, language }: NYCZoneMapProps) {
  const zones = useMemo(() => buildPilotZones(areaSummary), [areaSummary]);

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
            const hasDemand = zone.aggregateAnchor && (zone.aggregate.requestCount > 0 || zone.aggregate.workerSlots > 0);
            const ariaLabel = language === 'es'
              ? `${zone.label.es}. 0 residencias de trabajadores, 0 lugares de trabajo asignados. ${String(zone.aggregate.workerSlots)} cupos de trabajadores del agregado de ${zone.aggregate.areaLabel} esperan asignacion de zona.`
              : `${zone.label.en}. 0 worker residences, 0 worksites assigned. ${String(zone.aggregate.workerSlots)} worker slots from the ${zone.aggregate.areaLabel} aggregate await zone assignment.`;
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
                  <span>{language === 'es' ? '0 trabajadores / 0 lugares' : '0 workers / 0 worksites'}</span>
                  {zone.aggregateAnchor ? (
                    <small>
                      {language === 'es'
                        ? `${String(zone.aggregate.workerSlots)} cupos por asignar`
                        : `${String(zone.aggregate.workerSlots)} slots pending`}
                    </small>
                  ) : null}
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
