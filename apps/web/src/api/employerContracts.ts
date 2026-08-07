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

export type EmployerSearchResult = {
  items: EmployerSummary[];
  nextCursor: string | null;
};

export type CreateEmployerInput = {
  employerType: EmployerType;
  displayName: string;
  commandId: string;
};

export type ApiFailureKind =
  | 'validation'
  | 'forbidden'
  | 'not_found'
  | 'conflict'
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
