export type EmployerType = 'household' | 'business';
export type LifecycleStatus = 'draft';
export type SourceChannel = 'staff_entry';

export type EmployerSummary = {
  employerId: string;
  employerType: EmployerType;
  displayName: string;
  lifecycleStatus: LifecycleStatus;
};

export type EmployerDetail = EmployerSummary & {
  sourceChannel: SourceChannel;
};

export type RevisionEmployerDetail = EmployerDetail & {
  version: number;
  updatedAt: string;
};

export type EmployerSearchResult = {
  items: EmployerSummary[];
  nextCursor: string | null;
};

export type CreateEmployerInput = {
  employerType: EmployerType;
  displayName: string;
  commandId: string;
};

export type ReviseEmployerInput = {
  employerId: string;
  commandId: string;
  expectedVersion: number;
  employerType: EmployerType;
  displayName: string;
};

export type ReviseEmployerResult = {
  detail: RevisionEmployerDetail;
  resultVersion: number;
  replayed: boolean;
};
export type ApiFailureKind =
  | 'validation'
  | 'forbidden'
  | 'not_found'
  | 'conflict'
  | 'stale'
  | 'unavailable'
  | 'unknown_outcome'
  | 'unexpected';

export type ApiFailure = {
  ok: false;
  failure: {
    kind: ApiFailureKind;
  };
};

export type ApiSuccess<T> = {
  ok: true;
  value: T;
};

export type ApiResult<T> = ApiSuccess<T> | ApiFailure;

export type SearchEmployersInput = {
  displayNameQuery: string;
  employerType?: EmployerType;
  cursor?: string | null;
  signal?: AbortSignal;
};
