import type {
  OperationsAreaKey,
  OperationsAreaSummaryItem,
  OperationsZoneKey,
  OperationsZoneSummaryItem,
} from '../api/operationsProjectionClient';

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
  zoneKey: OperationsZoneKey;
};

export type PilotZone = PilotZoneDefinition & {
  aggregate: OperationsAreaSummaryItem;
  intensity: 'high' | 'low' | 'medium' | 'mediumHigh';
  summary: OperationsZoneSummaryItem;
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
    zoneKey: 'south_bronx',
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
    zoneKey: 'upper_manhattan_harlem',
  },
  {
    areaKey: 'manhattan',
    height: 21,
    id: 'midtown-lower-manhattan',
    label: { en: 'Midtown / Lower Manhattan', es: 'Midtown / Bajo Manhattan' },
    left: 39,
    top: 48,
    width: 11,
    zoneKey: 'midtown_lower_manhattan',
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
    zoneKey: 'northwest_queens',
  },
  {
    areaKey: 'queens',
    height: 17,
    id: 'central-queens',
    label: { en: 'Central Queens', es: 'Queens central' },
    left: 67,
    top: 50,
    width: 22,
    zoneKey: 'central_queens',
  },
  {
    areaKey: 'queens',
    height: 18,
    id: 'northeast-queens',
    label: { en: 'Northeast Queens', es: 'Noreste de Queens' },
    left: 78,
    top: 23,
    width: 17,
    zoneKey: 'northeast_queens',
  },
  {
    areaKey: 'brooklyn',
    height: 18,
    id: 'north-brooklyn',
    label: { en: 'North Brooklyn', es: 'Norte de Brooklyn' },
    left: 50,
    top: 54,
    width: 17,
    zoneKey: 'north_brooklyn',
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
    zoneKey: 'central_brooklyn',
  },
  {
    areaKey: 'brooklyn',
    height: 14,
    id: 'south-brooklyn',
    label: { en: 'South Brooklyn', es: 'Sur de Brooklyn' },
    left: 39,
    top: 83,
    width: 20,
    zoneKey: 'south_brooklyn',
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
    zoneKey: 'north_shore_staten_island',
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

const zoneLabels: Record<OperationsZoneKey, OperationsZoneSummaryItem['zoneLabel']> = {
  south_bronx: 'South Bronx',
  upper_manhattan_harlem: 'Upper Manhattan / Harlem',
  midtown_lower_manhattan: 'Midtown / Lower Manhattan',
  northwest_queens: 'Northwest Queens',
  central_queens: 'Central Queens',
  northeast_queens: 'Northeast Queens',
  north_brooklyn: 'North Brooklyn',
  central_brooklyn: 'Central Brooklyn',
  south_brooklyn: 'South Brooklyn',
  north_shore_staten_island: 'North Shore Staten Island',
};

function fallbackZoneSummary(zone: PilotZoneDefinition, aggregate: OperationsAreaSummaryItem): OperationsZoneSummaryItem {
  return {
    areaKey: zone.areaKey,
    intakeWorkerResidenceCount: 0,
    intakeWorksiteCount: 0,
    pendingReviewCount: zone.aggregateAnchor ? aggregate.pendingReviewCount : 0,
    requestCount: zone.aggregateAnchor ? aggregate.requestCount : 0,
    shiftCount: zone.aggregateAnchor ? aggregate.shiftCount : 0,
    workerResidenceCount: 0,
    workerSlots: zone.aggregateAnchor ? aggregate.workerSlots : 0,
    worksiteCount: 0,
    zoneKey: zone.zoneKey,
    zoneLabel: zoneLabels[zone.zoneKey],
  };
}

function zoneSummaryByKey(zoneSummary: OperationsZoneSummaryItem[]) {
  return new Map(zoneSummary.map((zone) => [zone.zoneKey, zone] as const));
}

function areaSummaryByKey(areaSummary: OperationsAreaSummaryItem[]) {
  const empty = new Map(emptyOperationsAreaSummary.map((area) => [area.areaKey, area]));
  return new Map([...empty, ...areaSummary.map((area) => [area.areaKey, area] as const)]);
}

export function aggregateAreaSummary(areaSummary: OperationsAreaSummaryItem[]) {
  const byKey = areaSummaryByKey(areaSummary);
  return areaOrder.map((areaKey) => byKey.get(areaKey) ?? fallbackArea(areaKey));
}

export function buildPilotZones(
  areaSummary: OperationsAreaSummaryItem[],
  zoneSummary: OperationsZoneSummaryItem[] = [],
): PilotZone[] {
  const normalizedSummary = aggregateAreaSummary(areaSummary);
  const byKey = new Map(normalizedSummary.map((area) => [area.areaKey, area]));
  const zoneByKey = zoneSummaryByKey(zoneSummary);
  const maximum = Math.max(
    ...zoneSummary.map((zone) => zone.workerSlots),
    ...normalizedSummary.map((area) => area.workerSlots),
    0,
  );
  return pilotZones.map((zone) => {
    const aggregate = byKey.get(zone.areaKey) ?? fallbackArea(zone.areaKey);
    const summary = zoneByKey.get(zone.zoneKey) ?? fallbackZoneSummary(zone, aggregate);
    return {
      ...zone,
      aggregate,
      intensity: intensityFor(summary.workerSlots, maximum),
      summary,
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
