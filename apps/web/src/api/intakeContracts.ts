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
  review_status: 'unreviewed' | 'needs_follow_up' | 'current' | 'stale';
  follow_up?: { owner_staff_id: string; next_follow_up_at: string; overdue: boolean };
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
  latest_review?: {
    review_id: string;
    reviewed_record_version: number;
    reviewed_content_version: number;
    outcome: string;
    actor_id: string;
    actor_display_name: string;
    occurred_at: string;
  };
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

export type WorkInterest = {
  interest_id: string;
  code: string;
  version: number;
  label_en: string;
  label_es: string;
  active: boolean;
};
export type HistoryItem = {
  event_id: string;
  version: number;
  content_version: number;
  event_type: string;
  actor_id: string;
  actor_display_name: string;
  occurred_at: string;
  review_id?: string;
  outcome?: string;
  owner_staff_id?: string;
  next_follow_up_at?: string;
};
export type Page<T> = { items: T[]; next_cursor: string | null };
export type RestrictedHistory = {
  event_id: string;
  note?: string;
  reviewed_content?: DraftObject;
  follow_up?: {
    action: 'needs_follow_up' | 'reschedule' | 'reassign' | 'attempt';
    reason_code?: 'missing_information' | 'clarification' | 'other';
    reason_text: string;
    method?: 'phone' | 'email' | 'in_person' | 'other';
    outcome?: string;
    time_zone: string;
  };
};
export type StaffChoice = { staff_id: string; display_name: string };
export type CatalogResult = { command_id: string; result_record_version: number; current: WorkInterest };
