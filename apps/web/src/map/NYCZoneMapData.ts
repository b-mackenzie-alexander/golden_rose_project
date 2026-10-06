import type { OperationsAreaKey, OperationsAreaSummaryItem } from '../api/operationsProjectionClient';

export type Language = 'en' | 'es';
export type MapMode = 'zones' | 'heat';

export type PilotZoneDefinition = {
  areaKey: OperationsAreaKey;
  aggregateAnchor?: boolean;
  height: number;
  id: string;
  label: Record<Language, string>;
  left: number;
  top: number;
  width: number;
};

export type PilotZone = PilotZoneDefinition & {
  aggregate: OperationsAreaSummaryItem;
  intensity: 'high' | 'low' | 'medium' | 'mediumHigh';
};

const areaOrder: OperationsAreaKey[] = ['bronx', 'brooklyn', 'manhattan', 'queens', 'staten_island'];

const areaLabels: Record<OperationsAreaKey, OperationsAreaSummaryItem['areaLabel']> = {
  bronx: 'Bronx',
  brooklyn: 'Brooklyn',
  manhattan: 'Manhattan',
  queens: 'Queens',
  staten_island: 'Staten Island',
};

export const emptyOperationsAreaSummary: OperationsAreaSummaryItem[] = areaOrder.map((areaKey) => ({
  areaKey,
  areaLabel: areaLabels[areaKey],
  pendingReviewCount: 0,
  requestCount: 0,
  shiftCount: 0,
  workerSlots: 0,
}));

export const pilotZones: PilotZoneDefinition[] = [
  {
    aggregateAnchor: true,
    areaKey: 'bronx',
    height: 13,
    id: 'south-bronx',
    label: { en: 'South Bronx', es: 'Sur del Bronx' },
    left: 54,
    top: 12,
    width: 17,
  },
  {
    aggregateAnchor: true,
    areaKey: 'manhattan',
    height: 22,
    id: 'upper-manhattan-harlem',
    label: { en: 'Upper Manhattan / Harlem', es: 'Alto Manhattan / Harlem' },
    left: 43,
    top: 24,
    width: 12,
  },
  {
    areaKey: 'manhattan',
    height: 21,
    id: 'midtown-lower-manhattan',
    label: { en: 'Midtown / Lower Manhattan', es: 'Midtown / Bajo Manhattan' },
    left: 39,
    top: 48,
    width: 11,
  },
  {
    aggregateAnchor: true,
    areaKey: 'queens',
    height: 16,
    id: 'northwest-queens',
    label: { en: 'Northwest Queens', es: 'Noroeste de Queens' },
    left: 62,
    top: 31,
    width: 20,
  },
  {
    areaKey: 'queens',
    height: 17,
    id: 'central-queens',
    label: { en: 'Central Queens', es: 'Queens central' },
    left: 67,
    top: 50,
    width: 22,
  },
  {
    areaKey: 'queens',
    height: 18,
    id: 'northeast-queens',
    label: { en: 'Northeast Queens', es: 'Noreste de Queens' },
    left: 78,
    top: 23,
    width: 17,
  },
  {
    areaKey: 'brooklyn',
    height: 18,
    id: 'north-brooklyn',
    label: { en: 'North Brooklyn', es: 'Norte de Brooklyn' },
    left: 50,
    top: 54,
    width: 17,
  },
  {
    aggregateAnchor: true,
    areaKey: 'brooklyn',
    height: 19,
    id: 'central-brooklyn',
    label: { en: 'Central Brooklyn', es: 'Brooklyn central' },
    left: 49,
    top: 72,
    width: 20,
  },
  {
    areaKey: 'brooklyn',
    height: 14,
    id: 'south-brooklyn',
    label: { en: 'South Brooklyn', es: 'Sur de Brooklyn' },
    left: 39,
    top: 83,
    width: 20,
  },
  {
    aggregateAnchor: true,
    areaKey: 'staten_island',
    height: 13,
    id: 'north-shore-staten-island',
    label: { en: 'North Shore Staten Island', es: 'North Shore Staten Island' },
    left: 14,
    top: 76,
    width: 19,
  },
];

function intensityFor(value: number, maximum: number): PilotZone['intensity'] {
  if (maximum <= 0 || value <= 0) return 'low';
  const ratio = value / maximum;
  if (ratio >= 0.8) return 'high';
  if (ratio >= 0.55) return 'mediumHigh';
  if (ratio >= 0.25) return 'medium';
  return 'low';
}

function fallbackArea(areaKey: OperationsAreaKey) {
  return {
    areaKey,
    areaLabel: areaLabels[areaKey],
    pendingReviewCount: 0,
    requestCount: 0,
    shiftCount: 0,
    workerSlots: 0,
  };
}

function areaSummaryByKey(areaSummary: OperationsAreaSummaryItem[]) {
  const empty = new Map(emptyOperationsAreaSummary.map((area) => [area.areaKey, area]));
  return new Map([...empty, ...areaSummary.map((area) => [area.areaKey, area] as const)]);
}

export function aggregateAreaSummary(areaSummary: OperationsAreaSummaryItem[]) {
  const byKey = areaSummaryByKey(areaSummary);
  return areaOrder.map((areaKey) => byKey.get(areaKey) ?? fallbackArea(areaKey));
}

export function buildPilotZones(areaSummary: OperationsAreaSummaryItem[]): PilotZone[] {
  const normalizedSummary = aggregateAreaSummary(areaSummary);
  const byKey = new Map(normalizedSummary.map((area) => [area.areaKey, area]));
  const maximum = Math.max(...normalizedSummary.map((area) => area.workerSlots), 0);
  return pilotZones.map((zone) => {
    const aggregate = byKey.get(zone.areaKey) ?? fallbackArea(zone.areaKey);
    return {
      ...zone,
      aggregate,
      intensity: zone.aggregateAnchor ? intensityFor(aggregate.workerSlots, maximum) : 'low',
    };
  });
}

function plural(value: number, singular: string, pluralText: string) {
  return `${String(value)} ${value === 1 ? singular : pluralText}`;
}

export function aggregateSummaryText(area: OperationsAreaSummaryItem, language: Language) {
  if (language === 'es') {
    return `${plural(area.requestCount, 'solicitud', 'solicitudes')} / ${plural(area.workerSlots, 'cupo', 'cupos')}`;
  }
  return `${plural(area.requestCount, 'request', 'requests')} / ${plural(area.workerSlots, 'slot', 'slots')}`;
}
