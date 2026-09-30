# Staff Intake Form Fields Reference

Date: 2026-09-30

This reference lists the fields currently used by the staff-facing worker and employer intake forms. It is for product and implementation reference only; it is not a legal intake template, a live-data collection instruction, or a production admission checklist.

Source surfaces reflected here:

- `apps/web/src/intakes/IntakeFields.tsx`
- `apps/web/src/intakes/IntakeWorkspace.tsx`
- `apps/web/src/intakes/WorkInterests.tsx`
- `apps/web/src/api/intakeClient.ts`
- `src/golden_rose/application/intake_contracts.py`
- `src/golden_rose/persistence/intakes.py`

The UI renders English and Spanish labels for the same payload fields. The payload keys below are stable across languages.

## Worker Intake

### Content Fields

| UI label | Payload key | Type / choices | Completion role | Notes |
| --- | --- | --- | --- | --- |
| First name | `full_name` | Text, stored as part of full name | Required | The UI splits name entry into first, middle, and last fields, then stores one `full_name` string. |
| Middle initial | `full_name` | Text, max 10 in UI | Optional | Stored as part of `full_name` when present. |
| Last name | `full_name` | Text, stored as part of full name | Required | The UI requires first and last name when save validation is shown. |
| Phone | `phone` | Telephone text, max 40 | Required | The frontend normalizes 10- or 11-digit US numbers to `+1...`; backend allows valid phone text with 7-15 main digits. |

### Work Interests

| UI label / control | Payload key | Type / choices | Completion role | Notes |
| --- | --- | --- | --- | --- |
| Catalog interest | `interests.selections[].interest_id` | Work-interest UUID from active catalog | Required unless manual interest is present | Staff select from the active work-interest catalog. |
| Catalog version | `interests.selections[].catalog_version` | Positive integer | Required with catalog selection | Stored automatically from the selected catalog item. |
| Manual interest | `interests.other_description` | Text, max 200 backend; displayed as up to 20 semicolon-separated entries in UI | Required unless catalog selection is present | The UI stores manual entries as one semicolon-separated text value. |

### Availability

| UI label / control | Payload key | Type / choices | Completion role | Notes |
| --- | --- | --- | --- | --- |
| Availability | `availability.mode` | `unknown`, `flexible`, `weekly` | Required to be non-`unknown` for completion | `weekly` exposes the weekly range fields. |
| Time zone | `availability.time_zone` | IANA time zone from frontend options | Required when mode is `weekly` | Defaults through the staff time-zone helper when weekly mode is selected. |
| Day | `availability.ranges[].weekday` | 1-7, Monday-Sunday | Required when mode is `weekly` | Up to 28 weekly ranges. |
| Start time | `availability.ranges[].start_local` | `HH:MM` local time | Required when mode is `weekly` | Backend validates non-overlapping ranges. |
| End time | `availability.ranges[].end_local` | `HH:MM` local time | Required when mode is `weekly` | Must form a valid interval with `end_day_offset`. |
| Ends on | `availability.ranges[].end_day_offset` | `0` same day, `1` next day | Required when mode is `weekly` | Allows overnight availability. |
| Availability exception note | `availability.exception_note` | Text, max 500 | Optional | Free-text exception context. |

Weekly availability also has convenience controls for adding/removing ranges, marking a range as any time, copying a range to weekdays, and copying a range to all days. Those controls edit the `availability.ranges` values; they are not separate persisted fields.

### Residential Address

Worker residential address is saved as a separate address section, not inside the main content payload.

Section key: `worker_residence`

| UI label | Address key | Type / choices | Completion role | Notes |
| --- | --- | --- | --- | --- |
| Address line 1 | `line1` | Text, max 200 | Required for complete address | Exact address access remains permission-gated. |
| Address line 2 | `line2` | Text, max 200 | Optional | Apartment, unit, or similar detail. |
| City / locality | `locality` | Text, max 100 | Required for complete address |  |
| State / region | `region` | Text, max 100 | Required for US complete address |  |
| Postal code | `postal_code` | Text, max 32 | Required for US complete address |  |
| Country | `country` | ISO alpha-2 text | Auto-set by frontend | The visible form does not expose a country input; the frontend sets `US` when address content exists. |

## Employer Intake

### Content Fields

| UI label | Payload key | Type / choices | Completion role | Notes |
| --- | --- | --- | --- | --- |
| Employer type | `employer_type` | `household`, `business` | Required | Determines household/business handling downstream; it does not make an automatic eligibility or placement decision. |
| Employer name | `display_name` | Text, max 200 | Required | Display/search name for the intake. |
| Representative name | `representative_name` | Text, max 200 | Required | Primary staff-facing contact name for the employer intake. |
| Phone | `phone` | Telephone text, max 40 | Required | Same frontend/backend phone handling as worker intake. |
| Role title | `role_title` | Text, max 200 | Required | Human-readable requested role. |
| Number of workers | `worker_count` | Integer, 1-1000 | Required | Quantity requested; it is not an automated staffing commitment. |
| Duties | `duties_summary` | Text area, max 1000 | Required | Free-text summary of duties. |

### Requested Schedule

| UI label / control | Payload key | Type / choices | Completion role | Notes |
| --- | --- | --- | --- | --- |
| Requested schedule | `schedule.mode` | `unknown`, `to_be_discussed`, `specified` | Required to be non-`unknown` for completion | `specified` exposes date/timed schedule fields. |
| Requested start date | `schedule.requested_start_date` | `YYYY-MM-DD` date | Required only for date-only specified schedule | Mutually exclusive with timed interval fields. |
| Start date and time | `schedule.starts_at` | Offset-aware instant derived from local datetime | Required for timed specified schedule | UI accepts local datetime, then converts with the selected time zone. |
| End date and time | `schedule.ends_at` | Offset-aware instant derived from local datetime | Required for timed specified schedule | Must be after `starts_at`. |
| Schedule time zone | `schedule.time_zone` | IANA time-zone text | Required for timed specified schedule | Defaults through the staff time-zone helper. |
| Schedule note | `schedule.note` | Text, max 500 | Optional | Free-text schedule context. |

A specified schedule is valid either as a date-only requested start date or as a timed interval with start, end, and time zone. The backend rejects a mix of both forms.

### Offer

| UI label / control | Payload key | Type / choices | Completion role | Notes |
| --- | --- | --- | --- | --- |
| Minimum amount | `offer.minimum` | Decimal text, up to 9 integer digits and 2 decimals | Required | Zero is allowed by the contract but the UI shows a warning status. |
| Maximum amount | `offer.maximum` | Decimal text, optional | Optional | Must not be below minimum when present. |
| Currency code | `offer.currency` | Three-letter currency from pinned frontend catalog | Required | Stored as uppercase code. |
| Pay basis | `offer.basis` | `hour`, `day`, `week`, `month`, `year`, `task` | Required |  |
| Amount is per worker | `offer.per_worker` | Boolean checkbox | Required for completion | Backend accepts only `true` when present; completion requires the field to be present. |
| Negotiable | `offer.negotiable` | Boolean checkbox | Optional | Defaults false when absent. |
| Offer terms | `offer.terms` | Text area, max 500 | Optional | Free-text terms context. |

### Party Address

Employer party address is saved as a separate address section.

Section key: `party_address`

| UI label | Address key | Type / choices | Completion role | Notes |
| --- | --- | --- | --- | --- |
| Address line 1 | `line1` | Text, max 200 | Required for complete address | Exact address access remains permission-gated. |
| Address line 2 | `line2` | Text, max 200 | Optional | Apartment, suite, unit, or similar detail. |
| City / locality | `locality` | Text, max 100 | Required for complete address |  |
| State / region | `region` | Text, max 100 | Required for US complete address |  |
| Postal code | `postal_code` | Text, max 32 | Required for US complete address |  |
| Country | `country` | ISO alpha-2 text | Auto-set by frontend | The visible form does not expose a country input; the frontend sets `US` when address content exists. |

### Worksite Address

Employer worksite address is saved as a separate address section.

Section key: `worksite_address`

| UI label | Address key | Type / choices | Completion role | Notes |
| --- | --- | --- | --- | --- |
| Address line 1 | `line1` | Text, max 200 | Required for complete address | Exact worksite access remains permission-gated. |
| Address line 2 | `line2` | Text, max 200 | Optional | Apartment, suite, unit, or similar detail. |
| City / locality | `locality` | Text, max 100 | Required for complete address |  |
| State / region | `region` | Text, max 100 | Required for US complete address |  |
| Postal code | `postal_code` | Text, max 32 | Required for US complete address |  |
| Country | `country` | ISO alpha-2 text | Auto-set by frontend | The visible form does not expose a country input; the frontend sets `US` when address content exists. |

The employer form includes a convenience control to copy the party address into the worksite address. That control edits the worksite address fields; it is not a separate persisted field.

## Review, Linking, And Finalization Fields

The intake editor also includes review, follow-up, canonical linking, finalization, and history controls after an intake exists. Those are workflow actions around an intake record rather than fields in the initial worker/employer intake forms.

System/client fields used by those actions include:

- `kind`
- `expected_version`
- `operation`
- `outcome`
- `review_id`
- `owner_staff_id`
- `next_follow_up_at`
- `time_zone`
- `reason_code`
- `reason_text`
- `method`
- `command_id` / idempotency key

These values support version safety, review evidence, follow-up scheduling, and canonical output decisions. They should not be treated as staff-entered intake questionnaire fields.

## Deliberately Excluded

The current request/shift lifecycle surfaces are not listed as worker or employer intake form fields here. They operate after employer intake/finalization and remain separate from the base intake form reference.
