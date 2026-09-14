export type IntakeKind = 'worker' | 'employer';
export type AddressSection = 'worker_residence' | 'party_address' | 'worksite_address';
export type DraftValue = string | number | boolean | null | DraftObject | DraftValue[];
export type DraftObject = { [key: string]: DraftValue };
export type IntakeSummary = {
  intake_id: string;
  kind: IntakeKind;
  version: number;
  lifecycle: 'draft';
  display_name?: string;
  complete: boolean;
  missing_fields: string[];
  review_status: 'unreviewed';
  updated_at: string;
  offer?: DraftObject;
};
export type IntakeDetail = {
  summary: IntakeSummary;
  content_version: number;
  candidate: DraftObject;
  resolved: DraftObject;
  links: DraftObject;
  dependency_stale: boolean;
};
export type AddressDetail = {
  intake_id: string;
  version: number;
  section: AddressSection;
  candidate: DraftObject | null;
  resolved: DraftObject | null;
};
export type IntakeCommandResult = {
  command_id: string;
  result_record_version: number;
  current: IntakeDetail;
};
export type Failure = 'unknown' | 'failed' | 'forbidden' | 'conflict';
export type Result<T> = { ok: true; value: T } | { ok: false; failure: Failure };
