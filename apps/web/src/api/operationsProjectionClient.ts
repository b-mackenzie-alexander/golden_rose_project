export type OperationsProjectionFailureKind =
  | 'forbidden'
  | 'validation'
  | 'unavailable'
  | 'unexpected';

export type OperationsProjectionResult<T> =
  | { ok: true; value: T }
  | { ok: false; failure: { kind: OperationsProjectionFailureKind } };

export type OperationsRequestItem = {
  itemType: 'staffing_request';
  sourceIntakeId: string | null;
  employerId: string;
  employerName: string;
  staffingRequestId: string;
  requestStatus: 'draft' | 'pending_review';
  roleTitle: string;
  workerCount: number;
  version: number;
  receivedAt: string;
  updatedAt: string;
};

export type OperationsShiftItem = {
  itemType: 'shift_need';
  sourceIntakeId: string | null;
  employerId: string;
  employerName: string;
  staffingRequestId: string;
  shiftNeedId: string;
  requestStatus: 'draft' | 'pending_review';
  shiftStatus: 'draft' | 'pending_review';
  roleTitle: string;
  workerCount: number;
  startsAt: string;
  endsAt: string;
  timeZone: string;
  version: number;
  updatedAt: string;
};

export type OperationsAreaKey = 'bronx' | 'brooklyn' | 'manhattan' | 'queens' | 'staten_island';

export type OperationsAreaSummaryItem = {
  areaKey: OperationsAreaKey;
  areaLabel: 'Bronx' | 'Brooklyn' | 'Manhattan' | 'Queens' | 'Staten Island';
  requestCount: number;
  shiftCount: number;
  workerSlots: number;
  pendingReviewCount: number;
};

export type OperationsReportSummary = {
  requestCount: number;
  shiftCount: number;
  workerSlots: number;
  pendingReviewCount: number;
  activeAreaCount: number;
  unmappedRequestCount: number;
};

export type OperationsProjection = {
  requestItems: OperationsRequestItem[];
  shiftItems: OperationsShiftItem[];
  areaSummary: OperationsAreaSummaryItem[];
  reportSummary: OperationsReportSummary;
};

const areaLabels: Record<OperationsAreaKey, OperationsAreaSummaryItem['areaLabel']> = {
  bronx: 'Bronx',
  brooklyn: 'Brooklyn',
  manhattan: 'Manhattan',
  queens: 'Queens',
  staten_island: 'Staten Island',
};

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function text(value: unknown, max = 1000): value is string {
  return typeof value === 'string' && value.trim().length > 0 && Array.from(value).length <= max;
}

function positive(value: unknown, max = 2147483647): value is number {
  return Number.isSafeInteger(value) && Number(value) >= 1 && Number(value) <= max;
}

function uuidText(value: unknown): value is string {
  if (typeof value !== 'string') return false;
  const parts = value.trim().split('-');
  return (
    parts.length === 5 &&
    [8, 4, 4, 4, 12].every((length, index) => parts[index]?.length === length) &&
    parts.every((part) => /^[0-9a-f]+$/i.test(part))
  );
}

function timestamp(value: unknown): value is string {
  return typeof value === 'string' && !Number.isNaN(Date.parse(value));
}

function parseRequestItem(value: unknown): OperationsRequestItem | null {
  if (!object(value)) return null;
  if (value.item_type !== 'staffing_request') return null;
  const sourceIntakeId = value.source_intake_id === undefined ? null : value.source_intake_id;
  if (sourceIntakeId !== null && !uuidText(sourceIntakeId)) return null;
  if (!uuidText(value.employer_id)) return null;
  if (!text(value.employer_name, 200)) return null;
  if (!uuidText(value.staffing_request_id)) return null;
  if (!['draft', 'pending_review'].includes(String(value.request_status))) return null;
  if (!text(value.role_title, 200) || !positive(value.worker_count, 1000) || !positive(value.version)) return null;
  if (!timestamp(value.received_at) || !timestamp(value.updated_at)) return null;
  return {
    itemType: 'staffing_request',
    sourceIntakeId: sourceIntakeId === null ? null : sourceIntakeId.trim(),
    employerId: value.employer_id.trim(),
    employerName: value.employer_name,
    staffingRequestId: value.staffing_request_id.trim(),
    requestStatus: value.request_status as OperationsRequestItem['requestStatus'],
    roleTitle: value.role_title,
    workerCount: value.worker_count,
    version: value.version,
    receivedAt: value.received_at,
    updatedAt: value.updated_at,
  };
}

function parseShiftItem(value: unknown): OperationsShiftItem | null {
  if (!object(value)) return null;
  if (value.item_type !== 'shift_need') return null;
  const sourceIntakeId = value.source_intake_id === undefined ? null : value.source_intake_id;
  if (sourceIntakeId !== null && !uuidText(sourceIntakeId)) return null;
  if (!uuidText(value.employer_id)) return null;
  if (!text(value.employer_name, 200)) return null;
  if (!uuidText(value.staffing_request_id)) return null;
  if (!uuidText(value.shift_need_id)) return null;
  if (!['draft', 'pending_review'].includes(String(value.request_status))) return null;
  if (!['draft', 'pending_review'].includes(String(value.shift_status))) return null;
  if (!text(value.role_title, 200) || !positive(value.worker_count, 1000)) return null;
  if (!timestamp(value.starts_at) || !timestamp(value.ends_at) || Date.parse(value.starts_at) >= Date.parse(value.ends_at)) return null;
  if (!text(value.time_zone, 200) || !positive(value.version) || !timestamp(value.updated_at)) return null;
  return {
    itemType: 'shift_need',
    sourceIntakeId: sourceIntakeId === null ? null : sourceIntakeId.trim(),
    employerId: value.employer_id.trim(),
    employerName: value.employer_name,
    staffingRequestId: value.staffing_request_id.trim(),
    shiftNeedId: value.shift_need_id.trim(),
    requestStatus: value.request_status as OperationsShiftItem['requestStatus'],
    shiftStatus: value.shift_status as OperationsShiftItem['shiftStatus'],
    roleTitle: value.role_title,
    workerCount: value.worker_count,
    startsAt: value.starts_at,
    endsAt: value.ends_at,
    timeZone: value.time_zone,
    version: value.version,
    updatedAt: value.updated_at,
  };
}

function nonNegative(value: unknown, max = 2147483647): value is number {
  return Number.isSafeInteger(value) && Number(value) >= 0 && Number(value) <= max;
}

function parseAreaSummaryItem(value: unknown): OperationsAreaSummaryItem | null {
  if (!object(value)) return null;
  const key = value.area_key;
  if (!['bronx', 'brooklyn', 'manhattan', 'queens', 'staten_island'].includes(String(key))) return null;
  const areaKey = key as OperationsAreaKey;
  if (value.area_label !== areaLabels[areaKey]) return null;
  if (
    !nonNegative(value.request_count) ||
    !nonNegative(value.shift_count) ||
    !nonNegative(value.worker_slots) ||
    !nonNegative(value.pending_review_count)
  ) return null;
  return {
    areaKey,
    areaLabel: areaLabels[areaKey],
    requestCount: value.request_count,
    shiftCount: value.shift_count,
    workerSlots: value.worker_slots,
    pendingReviewCount: value.pending_review_count,
  };
}

function parseReportSummary(value: unknown): OperationsReportSummary | null {
  if (!object(value)) return null;
  if (
    !nonNegative(value.request_count) ||
    !nonNegative(value.shift_count) ||
    !nonNegative(value.worker_slots) ||
    !nonNegative(value.pending_review_count) ||
    !nonNegative(value.active_area_count, 5) ||
    !nonNegative(value.unmapped_request_count)
  ) return null;
  return {
    requestCount: value.request_count,
    shiftCount: value.shift_count,
    workerSlots: value.worker_slots,
    pendingReviewCount: value.pending_review_count,
    activeAreaCount: value.active_area_count,
    unmappedRequestCount: value.unmapped_request_count,
  };
}

function parseProjection(value: unknown): OperationsProjection | null {
  if (
    !object(value) ||
    !Array.isArray(value.request_items) ||
    !Array.isArray(value.shift_items) ||
    !Array.isArray(value.area_summary)
  ) return null;
  if (value.request_items.length > 50 || value.shift_items.length > 50 || value.area_summary.length !== 5) return null;
  const requestItems = value.request_items.map(parseRequestItem);
  const shiftItems = value.shift_items.map(parseShiftItem);
  const areaSummary = value.area_summary.map(parseAreaSummaryItem);
  const reportSummary = parseReportSummary(value.report_summary);
  const areaKeys = new Set(areaSummary.map((item) => item?.areaKey));
  if (
    requestItems.some((item) => item === null) ||
    shiftItems.some((item) => item === null) ||
    areaSummary.some((item) => item === null) ||
    areaKeys.size !== 5 ||
    reportSummary === null
  ) return null;
  return {
    requestItems: requestItems as OperationsRequestItem[],
    shiftItems: shiftItems as OperationsShiftItem[],
    areaSummary: areaSummary as OperationsAreaSummaryItem[],
    reportSummary,
  };
}

function failure(status: number): OperationsProjectionResult<never> {
  if (status === 400 || status === 422) return { ok: false, failure: { kind: 'validation' } };
  if (status === 403) return { ok: false, failure: { kind: 'forbidden' } };
  if (status === 503) return { ok: false, failure: { kind: 'unavailable' } };
  return { ok: false, failure: { kind: 'unexpected' } };
}

export async function getOperationsProjection(): Promise<OperationsProjectionResult<OperationsProjection>> {
  let response: Response;
  try {
    response = await fetch('/api/staff/v1/operations/projection', {
      method: 'GET',
      headers: { Accept: 'application/json' },
      cache: 'no-store',
      credentials: 'same-origin',
      mode: 'same-origin',
      redirect: 'error',
      referrerPolicy: 'no-referrer',
    });
  } catch {
    return { ok: false, failure: { kind: 'unavailable' } };
  }
  if (response.status !== 200) {
    try { await response.body?.cancel(); } catch { /* best effort */ }
    return failure(response.status);
  }
  if (!/^application\/json(?:\s*;.*)?$/i.test(response.headers.get('Content-Type') ?? '')) {
    try { await response.body?.cancel(); } catch { /* best effort */ }
    return { ok: false, failure: { kind: 'unexpected' } };
  }
  try {
    const parsed = parseProjection(await response.json());
    return parsed ? { ok: true, value: parsed } : { ok: false, failure: { kind: 'unexpected' } };
  } catch {
    return { ok: false, failure: { kind: 'unexpected' } };
  }
}
