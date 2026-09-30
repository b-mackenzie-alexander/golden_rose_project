# ruff: noqa: E501
"""PostgreSQL 16 schema contract through 0009a, captured from disposable migrations."""

EXPECTED_INTAKE_CONSTRAINTS = {
    "alembic_version.alembic_version_pkc": "PRIMARY KEY (version_num)",
    "audit_events.audit_events_pkey": "PRIMARY KEY (audit_event_id)",
    "audit_events.ck_audit_events_actor_type": "CHECK (actor_type::text = 'staff'::text)",
    "audit_events.ck_audit_events_correlation_matches_command": "CHECK (correlation_id = command_id)",
    "audit_events.ck_audit_events_entity_sequence_matches_new_record_version": "CHECK "
    "(entity_sequence = "
    "new_record_version)",
    "audit_events.ck_audit_events_entity_type": "CHECK ((entity_type::text = ANY "
    "(ARRAY['employer'::character varying::text, "
    "'employer_contact'::character varying::text, "
    "'intake'::character varying::text, "
    "'work_interest'::character varying::text, "
    "'worker'::character varying::text, "
    "'worker_contact'::character varying::text, "
    "'worker_residence'::character varying::text, "
    "'worker_preferences'::character varying::text, "
    "'employer_contact_details'::character varying::text, "
    "'employer_address'::character varying::text, "
    "'worksite'::character varying::text, "
    "'staffing_request'::character varying::text])) OR "
    "entity_type::text = 'canonical_output_review'::text)",
    "audit_events.ck_audit_events_event_type": "CHECK ((event_type::text = ANY "
    "(ARRAY['employer.created'::character varying::text, "
    "'employer_contact.created'::character varying::text, "
    "'employer.draft_revised'::character varying::text, "
    "'intake.created'::character varying::text, "
    "'intake.revised'::character varying::text, "
    "'intake.reviewed'::character varying::text, "
    "'intake.follow_up_recorded'::character varying::text, "
    "'work_interest.created'::character varying::text, "
    "'work_interest.revised'::character varying::text, "
    "'intake.finalized'::character varying::text, "
    "'worker.created'::character varying::text, "
    "'worker_contact.created'::character varying::text, "
    "'worker_residence.created'::character varying::text, "
    "'worker_preferences.created'::character "
    "varying::text, "
    "'employer_contact_details.created'::character "
    "varying::text, 'employer_address.created'::character "
    "varying::text, 'worksite.created'::character "
    "varying::text, 'staffing_request.created'::character "
    "varying::text, 'intake.linked'::character "
    "varying::text])) OR (event_type::text = ANY "
    "(ARRAY['worker.corrected'::character varying::text, "
    "'worker_contact.corrected'::character varying::text, "
    "'worker_residence.corrected'::character "
    "varying::text, "
    "'worker_preferences.corrected'::character "
    "varying::text, "
    "'employer_contact_details.corrected'::character "
    "varying::text, "
    "'employer_address.corrected'::character "
    "varying::text, 'worksite.corrected'::character "
    "varying::text, "
    "'staffing_request.corrected'::character "
    "varying::text])) OR event_type::text = "
    "'canonical_output_review.reviewed'::text)",
    "audit_events.ck_audit_events_one_step_version_advance": "CHECK (new_record_version = "
    "(prior_record_version + 1))",
    "audit_events.ck_audit_events_payload_classification": "CHECK (payload_classification::text = "
    "'sensitive_operational'::text)",
    "audit_events.ck_audit_events_schema_matches_type": "CHECK (event_schema_name::text = "
    "event_type::text)",
    "audit_events.ck_audit_events_schema_name": "CHECK ((event_schema_name::text = ANY "
    "(ARRAY['employer.created'::character varying::text, "
    "'employer_contact.created'::character varying::text, "
    "'employer.draft_revised'::character varying::text, "
    "'intake.created'::character varying::text, "
    "'intake.revised'::character varying::text, "
    "'intake.reviewed'::character varying::text, "
    "'intake.follow_up_recorded'::character "
    "varying::text, 'work_interest.created'::character "
    "varying::text, 'work_interest.revised'::character "
    "varying::text, 'intake.finalized'::character "
    "varying::text, 'worker.created'::character "
    "varying::text, 'worker_contact.created'::character "
    "varying::text, 'worker_residence.created'::character "
    "varying::text, "
    "'worker_preferences.created'::character "
    "varying::text, "
    "'employer_contact_details.created'::character "
    "varying::text, 'employer_address.created'::character "
    "varying::text, 'worksite.created'::character "
    "varying::text, 'staffing_request.created'::character "
    "varying::text, 'intake.linked'::character "
    "varying::text])) OR (event_schema_name::text = ANY "
    "(ARRAY['worker.corrected'::character varying::text, "
    "'worker_contact.corrected'::character varying::text, "
    "'worker_residence.corrected'::character "
    "varying::text, "
    "'worker_preferences.corrected'::character "
    "varying::text, "
    "'employer_contact_details.corrected'::character "
    "varying::text, "
    "'employer_address.corrected'::character "
    "varying::text, 'worksite.corrected'::character "
    "varying::text, "
    "'staffing_request.corrected'::character "
    "varying::text])) OR event_schema_name::text = "
    "'canonical_output_review.reviewed'::text)",
    "audit_events.ck_audit_events_schema_version": "CHECK (event_schema_version = 1)",
    "audit_events.ck_audit_events_source_type": "CHECK (source_type::text = 'staff_api'::text)",
    "audit_events.fk_audit_events_command_result": "FOREIGN KEY (command_id, entity_type, entity_id, "
    "new_record_version, event_type, actor_id) "
    "REFERENCES command_results(command_id, "
    "entity_type, entity_id, result_version, "
    "event_type, actor_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "audit_events.fk_audit_events_entity_authority": "FOREIGN KEY (entity_type, entity_id) REFERENCES "
    "entity_authorities(entity_type, entity_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "audit_events.guard_intake_link_event": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "audit_events.guard_intake_workflow_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "audit_events.guard_work_interest_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "audit_events.uq_audit_events_command_entity": "UNIQUE (command_id, entity_type, entity_id)",
    "audit_events.uq_audit_events_command_event_type": "UNIQUE (command_id, event_type)",
    "audit_events.uq_audit_events_entity_sequence": "UNIQUE (entity_type, entity_id, entity_sequence)",
    "audit_events.uq_audit_events_result_authority": "UNIQUE (command_id, entity_id, "
    "new_record_version, event_type, actor_id)",
    "canonical_correction_payloads.canonical_correction_payloads_after_check": "CHECK "
    "(jsonb_typeof(after) "
    "= 'object'::text)",
    "canonical_correction_payloads.canonical_correction_payloads_before_check": "CHECK "
    "(jsonb_typeof(before) "
    "= 'object'::text)",
    "canonical_correction_payloads.canonical_correction_payloads_check": "CHECK (before IS DISTINCT "
    "FROM after)",
    "canonical_correction_payloads.canonical_correction_payloads_check1": "CHECK "
    "(octet_length(before::text) "
    "<= 65536 AND "
    "octet_length(after::text) "
    "<= 65536)",
    "canonical_correction_payloads.canonical_correction_payloads_event_id_fkey": "FOREIGN KEY "
    "(event_id) "
    "REFERENCES "
    "canonical_corrections(event_id) "
    "DEFERRABLE "
    "INITIALLY DEFERRED",
    "canonical_correction_payloads.canonical_correction_payloads_pkey": "PRIMARY KEY (event_id)",
    "canonical_correction_payloads.canonical_correction_payloads_reason_text_check": "CHECK "
    "(btrim(reason_text::text) "
    "<> ''::text)",
    "canonical_correction_payloads.guard_correction_evidence": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "canonical_corrections.canonical_corrections_check": "CHECK (result_version = (previous_version + "
    "1))",
    "canonical_corrections.canonical_corrections_check1": "CHECK (corrects_event_id IS DISTINCT FROM "
    "event_id)",
    "canonical_corrections.canonical_corrections_command_id_fkey": "FOREIGN KEY (command_id) "
    "REFERENCES "
    "command_receipts(command_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "canonical_corrections.canonical_corrections_command_id_key": "UNIQUE (command_id)",
    "canonical_corrections.canonical_corrections_corrects_event_id_entity_type_entity_fkey": "FOREIGN "
    "KEY "
    "(corrects_event_id, "
    "entity_type, "
    "entity_id) "
    "REFERENCES "
    "canonical_corrections(event_id, "
    "entity_type, "
    "entity_id)",
    "canonical_corrections.canonical_corrections_entity_type_entity_id_fkey": "FOREIGN KEY "
    "(entity_type, "
    "entity_id) REFERENCES "
    "entity_authorities(entity_type, "
    "entity_id)",
    "canonical_corrections.canonical_corrections_entity_type_entity_id_result_version_key": "UNIQUE "
    "(entity_type, "
    "entity_id, "
    "result_version)",
    "canonical_corrections.canonical_corrections_event_id_entity_type_entity_id_key": "UNIQUE "
    "(event_id, "
    "entity_type, "
    "entity_id)",
    "canonical_corrections.canonical_corrections_event_id_fkey": "FOREIGN KEY (event_id) REFERENCES "
    "audit_events(audit_event_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "canonical_corrections.canonical_corrections_pkey": "PRIMARY KEY (event_id)",
    "canonical_corrections.canonical_corrections_previous_version_check": "CHECK (previous_version >= "
    "1)",
    "canonical_corrections.ck_canonical_correction_command": "CHECK (command_type::text = "
    "'correct_worker'::text AND "
    "entity_type::text = 'worker'::text OR "
    "command_type::text = "
    "'correct_worker_contact'::text AND "
    "entity_type::text = "
    "'worker_contact'::text OR "
    "command_type::text = "
    "'correct_worker_residence'::text AND "
    "entity_type::text = "
    "'worker_residence'::text OR "
    "command_type::text = "
    "'correct_worker_preferences'::text AND "
    "entity_type::text = "
    "'worker_preferences'::text OR "
    "command_type::text = "
    "'correct_contact_details'::text AND "
    "entity_type::text = "
    "'employer_contact_details'::text OR "
    "command_type::text = "
    "'correct_contact_address'::text AND "
    "entity_type::text = "
    "'employer_contact_details'::text OR "
    "command_type::text = "
    "'correct_employer_address'::text AND "
    "entity_type::text = "
    "'employer_address'::text OR "
    "command_type::text = "
    "'correct_worksite_address'::text AND "
    "entity_type::text = 'worksite'::text OR "
    "command_type::text = "
    "'correct_staffing_request'::text AND "
    "entity_type::text = "
    "'staffing_request'::text)",
    "canonical_corrections.guard_correction_evidence": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "canonical_output_review_payloads.canonical_output_review_payloads_note_check": "CHECK (note IS "
    "NULL OR "
    "btrim(note::text) "
    "<> ''::text)",
    "canonical_output_review_payloads.canonical_output_review_payloads_pkey": "PRIMARY KEY "
    "(review_id)",
    "canonical_output_review_payloads.canonical_output_review_payloads_review_id_fkey": "FOREIGN KEY "
    "(review_id) "
    "REFERENCES "
    "canonical_output_reviews(review_id) "
    "DEFERRABLE "
    "INITIALLY "
    "DEFERRED",
    "canonical_output_review_payloads.canonical_output_review_payloads_reviewed_content_check": "CHECK "
    "(jsonb_typeof(reviewed_content) "
    "= "
    "'object'::text)",
    "canonical_output_review_payloads.canonical_output_review_payloads_reviewed_content_check1": "CHECK "
    "(octet_length(reviewed_content::text) "
    "<= "
    "65536)",
    "canonical_output_review_payloads.guard_canonical_review": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "canonical_output_reviews.canonical_output_reviews_command_id_fkey": "FOREIGN KEY (command_id) "
    "REFERENCES "
    "command_receipts(command_id) "
    "DEFERRABLE INITIALLY "
    "DEFERRED",
    "canonical_output_reviews.canonical_output_reviews_command_id_key": "UNIQUE (command_id)",
    "canonical_output_reviews.canonical_output_reviews_dependencies_check": "CHECK "
    "(jsonb_typeof(dependencies) "
    "= 'object'::text)",
    "canonical_output_reviews.canonical_output_reviews_event_id_fkey": "FOREIGN KEY (event_id) "
    "REFERENCES "
    "audit_events(audit_event_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "canonical_output_reviews.canonical_output_reviews_event_id_key": "UNIQUE (event_id)",
    "canonical_output_reviews.canonical_output_reviews_intake_id_fkey": "FOREIGN KEY (intake_id) "
    "REFERENCES "
    "canonical_review_heads(intake_id)",
    "canonical_output_reviews.canonical_output_reviews_intake_id_result_version_key": "UNIQUE "
    "(intake_id, "
    "result_version)",
    "canonical_output_reviews.canonical_output_reviews_intake_id_review_id_key": "UNIQUE (intake_id, "
    "review_id)",
    "canonical_output_reviews.canonical_output_reviews_original_review_id_fkey": "FOREIGN KEY "
    "(original_review_id) "
    "REFERENCES "
    "intake_reviews(review_id)",
    "canonical_output_reviews.canonical_output_reviews_pkey": "PRIMARY KEY (review_id)",
    "canonical_output_reviews.canonical_output_reviews_result_version_check": "CHECK (result_version "
    ">= 1)",
    "canonical_output_reviews.guard_canonical_review": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "canonical_review_heads.canonical_review_heads_check": "CHECK (canonical_output_review_id = "
    "intake_id)",
    "canonical_review_heads.canonical_review_heads_check1": "CHECK (version = 0 AND latest_review_id "
    "IS NULL AND updated_by IS NULL AND "
    "updated_at IS NULL OR version > 0 AND "
    "latest_review_id IS NOT NULL AND "
    "updated_by IS NOT NULL AND updated_at IS "
    "NOT NULL)",
    "canonical_review_heads.canonical_review_heads_intake_id_fkey": "FOREIGN KEY (intake_id) "
    "REFERENCES "
    "intake_finalizations(intake_id)",
    "canonical_review_heads.canonical_review_heads_intake_id_key": "UNIQUE (intake_id)",
    "canonical_review_heads.canonical_review_heads_intake_id_latest_review_id_fkey": "FOREIGN KEY "
    "(intake_id, "
    "latest_review_id) "
    "REFERENCES "
    "canonical_output_reviews(intake_id, "
    "review_id) "
    "DEFERRABLE "
    "INITIALLY "
    "DEFERRED",
    "canonical_review_heads.canonical_review_heads_pkey": "PRIMARY KEY (canonical_output_review_id)",
    "canonical_review_heads.canonical_review_heads_version_check": "CHECK (version >= 0)",
    "canonical_review_heads.guard_canonical_review": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "command_receipts.ck_command_receipts_command_type": "CHECK ((command_type::text = ANY "
    "(ARRAY['create_draft_employer'::character "
    "varying::text, "
    "'create_employer_contact'::character "
    "varying::text, "
    "'revise_draft_employer'::character "
    "varying::text, 'create_intake'::character "
    "varying::text, 'revise_intake'::character "
    "varying::text, "
    "'revise_intake_address'::character "
    "varying::text, 'review_intake'::character "
    "varying::text, "
    "'follow_up_intake'::character "
    "varying::text, "
    "'create_work_interest'::character "
    "varying::text, "
    "'revise_work_interest'::character "
    "varying::text, 'finalize_intake'::character "
    "varying::text, 'link_intake'::character "
    "varying::text])) OR (command_type::text = "
    "ANY (ARRAY['correct_worker'::character "
    "varying::text, "
    "'correct_worker_contact'::character "
    "varying::text, "
    "'correct_worker_residence'::character "
    "varying::text, "
    "'correct_worker_preferences'::character "
    "varying::text, "
    "'correct_contact_details'::character "
    "varying::text, "
    "'correct_contact_address'::character "
    "varying::text, "
    "'correct_employer_address'::character "
    "varying::text, "
    "'correct_worksite_address'::character "
    "varying::text, "
    "'correct_staffing_request'::character "
    "varying::text])) OR command_type::text = "
    "'review_canonical_outputs'::text)",
    "command_receipts.ck_command_receipts_entity_type": "CHECK ((result_entity_type::text = ANY "
    "(ARRAY['employer'::character varying::text, "
    "'employer_contact'::character varying::text, "
    "'intake'::character varying::text, "
    "'work_interest'::character varying::text])) "
    "OR (result_entity_type::text = ANY "
    "(ARRAY['worker'::character varying::text, "
    "'worker_contact'::character varying::text, "
    "'worker_residence'::character varying::text, "
    "'worker_preferences'::character "
    "varying::text, "
    "'employer_contact_details'::character "
    "varying::text, 'employer_address'::character "
    "varying::text, 'worksite'::character "
    "varying::text, 'staffing_request'::character "
    "varying::text])) OR result_entity_type::text "
    "= 'canonical_output_review'::text)",
    "command_receipts.ck_command_receipts_request_fingerprint_len": "CHECK "
    "(octet_length(request_fingerprint) "
    "= 32)",
    "command_receipts.ck_command_receipts_result_authority_shape": "CHECK (command_type::text = "
    "'create_draft_employer'::text AND "
    "result_entity_type::text = "
    "'employer'::text AND "
    "result_event_type::text = "
    "'employer.created'::text AND "
    "result_record_version = 1 OR "
    "command_type::text = "
    "'create_employer_contact'::text "
    "AND result_entity_type::text = "
    "'employer_contact'::text AND "
    "result_event_type::text = "
    "'employer_contact.created'::text "
    "AND result_record_version = 1 OR "
    "command_type::text = "
    "'revise_draft_employer'::text AND "
    "result_entity_type::text = "
    "'employer'::text AND "
    "result_event_type::text = "
    "'employer.draft_revised'::text "
    "AND result_record_version >= 2 OR "
    "command_type::text = "
    "'create_intake'::text AND "
    "result_entity_type::text = "
    "'intake'::text AND "
    "result_event_type::text = "
    "'intake.created'::text AND "
    "result_record_version = 1 OR "
    "(command_type::text = ANY "
    "(ARRAY['revise_intake'::character "
    "varying::text, "
    "'revise_intake_address'::character "
    "varying::text])) AND "
    "result_entity_type::text = "
    "'intake'::text AND "
    "result_event_type::text = "
    "'intake.revised'::text AND "
    "result_record_version >= 2 OR "
    "command_type::text = "
    "'review_intake'::text AND "
    "result_entity_type::text = "
    "'intake'::text AND "
    "result_event_type::text = "
    "'intake.reviewed'::text AND "
    "result_record_version >= 2 OR "
    "command_type::text = "
    "'follow_up_intake'::text AND "
    "result_entity_type::text = "
    "'intake'::text AND "
    "result_event_type::text = "
    "'intake.follow_up_recorded'::text "
    "AND result_record_version >= 2 OR "
    "command_type::text = "
    "'create_work_interest'::text AND "
    "result_entity_type::text = "
    "'work_interest'::text AND "
    "result_event_type::text = "
    "'work_interest.created'::text AND "
    "result_record_version = 1 OR "
    "command_type::text = "
    "'revise_work_interest'::text AND "
    "result_entity_type::text = "
    "'work_interest'::text AND "
    "result_event_type::text = "
    "'work_interest.revised'::text AND "
    "result_record_version >= 2 OR "
    "command_type::text = "
    "'finalize_intake'::text AND "
    "result_entity_type::text = "
    "'intake'::text AND "
    "result_event_type::text = "
    "'intake.finalized'::text AND "
    "result_record_version >= 3 OR "
    "command_type::text = "
    "'link_intake'::text AND "
    "result_entity_type::text = "
    "'intake'::text AND "
    "result_event_type::text = "
    "'intake.linked'::text AND "
    "result_record_version >= 2 OR "
    "command_type::text = "
    "'correct_worker'::text AND "
    "result_entity_type::text = "
    "'worker'::text AND "
    "result_event_type::text = "
    "'worker.corrected'::text AND "
    "result_record_version >= 2 OR "
    "command_type::text = "
    "'correct_worker_contact'::text "
    "AND result_entity_type::text = "
    "'worker_contact'::text AND "
    "result_event_type::text = "
    "'worker_contact.corrected'::text "
    "AND result_record_version >= 2 OR "
    "command_type::text = "
    "'correct_worker_residence'::text "
    "AND result_entity_type::text = "
    "'worker_residence'::text AND "
    "result_event_type::text = "
    "'worker_residence.corrected'::text "
    "AND result_record_version >= 2 OR "
    "command_type::text = "
    "'correct_worker_preferences'::text "
    "AND result_entity_type::text = "
    "'worker_preferences'::text AND "
    "result_event_type::text = "
    "'worker_preferences.corrected'::text "
    "AND result_record_version >= 2 OR "
    "command_type::text = "
    "'correct_contact_details'::text "
    "AND result_entity_type::text = "
    "'employer_contact_details'::text "
    "AND result_event_type::text = "
    "'employer_contact_details.corrected'::text "
    "AND result_record_version >= 2 OR "
    "command_type::text = "
    "'correct_contact_address'::text "
    "AND result_entity_type::text = "
    "'employer_contact_details'::text "
    "AND result_event_type::text = "
    "'employer_contact_details.corrected'::text "
    "AND result_record_version >= 2 OR "
    "command_type::text = "
    "'correct_employer_address'::text "
    "AND result_entity_type::text = "
    "'employer_address'::text AND "
    "result_event_type::text = "
    "'employer_address.corrected'::text "
    "AND result_record_version >= 2 OR "
    "command_type::text = "
    "'correct_worksite_address'::text "
    "AND result_entity_type::text = "
    "'worksite'::text AND "
    "result_event_type::text = "
    "'worksite.corrected'::text AND "
    "result_record_version >= 2 OR "
    "command_type::text = "
    "'correct_staffing_request'::text "
    "AND result_entity_type::text = "
    "'staffing_request'::text AND "
    "result_event_type::text = "
    "'staffing_request.corrected'::text "
    "AND result_record_version >= 2 OR "
    "command_type::text = "
    "'review_canonical_outputs'::text "
    "AND result_entity_type::text = "
    "'canonical_output_review'::text "
    "AND result_event_type::text = "
    "'canonical_output_review.reviewed'::text "
    "AND result_record_version >= 1)",
    "command_receipts.ck_command_receipts_result_record_version_positive": "CHECK "
    "(result_record_version >= "
    "1)",
    "command_receipts.ck_command_receipts_schema_version": "CHECK (command_schema_version = 1)",
    "command_receipts.command_receipts_pkey": "PRIMARY KEY (command_id)",
    "command_receipts.fk_command_receipts_creation_event": "FOREIGN KEY (command_id, "
    "result_entity_type, result_entity_id) "
    "REFERENCES audit_events(command_id, "
    "entity_type, entity_id) DEFERRABLE "
    "INITIALLY DEFERRED",
    "command_receipts.fk_command_receipts_primary_result": "FOREIGN KEY (command_id, "
    "result_entity_type, result_entity_id, "
    "result_record_version, result_event_type, "
    "actor_id) REFERENCES "
    "command_results(command_id, entity_type, "
    "entity_id, result_version, event_type, "
    "actor_id) DEFERRABLE INITIALLY DEFERRED",
    "command_receipts.fk_command_receipts_result_audit_event": "FOREIGN KEY (command_id, "
    "result_entity_id, "
    "result_record_version, "
    "result_event_type, actor_id) "
    "REFERENCES audit_events(command_id, "
    "entity_id, new_record_version, "
    "event_type, actor_id) DEFERRABLE "
    "INITIALLY DEFERRED",
    "command_receipts.fk_command_receipts_result_entity_authority": "FOREIGN KEY (result_entity_type, "
    "result_entity_id) REFERENCES "
    "entity_authorities(entity_type, "
    "entity_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "command_receipts.guard_canonical_review": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "command_receipts.guard_correction_evidence": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "command_receipts.guard_finalization_results": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "command_receipts.uq_command_receipts_actor_command": "UNIQUE (command_id, actor_id, "
    "command_type)",
    "command_receipts.uq_command_receipts_command_result": "UNIQUE (command_id, result_entity_id)",
    "command_receipts.uq_command_receipts_command_result_entity": "UNIQUE (command_id, "
    "result_entity_type, "
    "result_entity_id)",
    "command_receipts.uq_command_receipts_result_authority": "UNIQUE (command_id, result_entity_type, "
    "result_entity_id, "
    "result_record_version, "
    "result_event_type, actor_id)",
    "command_results.ck_command_results_authority_shape": "CHECK (command_type::text = "
    "'create_draft_employer'::text AND "
    "entity_type::text = 'employer'::text AND "
    "event_type::text = "
    "'employer.created'::text AND "
    "result_version = 1 OR command_type::text = "
    "'create_employer_contact'::text AND "
    "entity_type::text = "
    "'employer_contact'::text AND "
    "event_type::text = "
    "'employer_contact.created'::text AND "
    "result_version = 1 OR command_type::text = "
    "'revise_draft_employer'::text AND "
    "entity_type::text = 'employer'::text AND "
    "event_type::text = "
    "'employer.draft_revised'::text AND "
    "result_version >= 2 OR command_type::text "
    "= 'create_intake'::text AND "
    "entity_type::text = 'intake'::text AND "
    "event_type::text = 'intake.created'::text "
    "AND result_version = 1 OR "
    "(command_type::text = ANY "
    "(ARRAY['revise_intake'::character "
    "varying::text, "
    "'revise_intake_address'::character "
    "varying::text])) AND entity_type::text = "
    "'intake'::text AND event_type::text = "
    "'intake.revised'::text AND result_version "
    ">= 2 OR command_type::text = "
    "'review_intake'::text AND "
    "entity_type::text = 'intake'::text AND "
    "event_type::text = 'intake.reviewed'::text "
    "AND result_version >= 2 OR "
    "command_type::text = "
    "'follow_up_intake'::text AND "
    "entity_type::text = 'intake'::text AND "
    "event_type::text = "
    "'intake.follow_up_recorded'::text AND "
    "result_version >= 2 OR command_type::text "
    "= 'create_work_interest'::text AND "
    "entity_type::text = 'work_interest'::text "
    "AND event_type::text = "
    "'work_interest.created'::text AND "
    "result_version = 1 OR command_type::text = "
    "'revise_work_interest'::text AND "
    "entity_type::text = 'work_interest'::text "
    "AND event_type::text = "
    "'work_interest.revised'::text AND "
    "result_version >= 2 OR command_type::text "
    "= 'finalize_intake'::text AND "
    "entity_type::text = 'intake'::text AND "
    "event_type::text = "
    "'intake.finalized'::text AND "
    "result_version >= 3 OR command_type::text "
    "= 'link_intake'::text AND "
    "entity_type::text = 'intake'::text AND "
    "event_type::text = 'intake.linked'::text "
    "AND result_version >= 2 OR "
    "command_type::text = "
    "'finalize_intake'::text AND result_version "
    "= 1 AND (entity_type::text = "
    "'worker'::text AND event_type::text = "
    "'worker.created'::text OR "
    "entity_type::text = 'worker_contact'::text "
    "AND event_type::text = "
    "'worker_contact.created'::text OR "
    "entity_type::text = "
    "'worker_residence'::text AND "
    "event_type::text = "
    "'worker_residence.created'::text OR "
    "entity_type::text = "
    "'worker_preferences'::text AND "
    "event_type::text = "
    "'worker_preferences.created'::text OR "
    "entity_type::text = 'employer'::text AND "
    "event_type::text = "
    "'employer.created'::text OR "
    "entity_type::text = "
    "'employer_contact'::text AND "
    "event_type::text = "
    "'employer_contact.created'::text OR "
    "entity_type::text = "
    "'employer_contact_details'::text AND "
    "event_type::text = "
    "'employer_contact_details.created'::text "
    "OR entity_type::text = "
    "'employer_address'::text AND "
    "event_type::text = "
    "'employer_address.created'::text OR "
    "entity_type::text = 'worksite'::text AND "
    "event_type::text = "
    "'worksite.created'::text OR "
    "entity_type::text = "
    "'staffing_request'::text AND "
    "event_type::text = "
    "'staffing_request.created'::text) OR "
    "command_type::text = "
    "'correct_worker'::text AND "
    "entity_type::text = 'worker'::text AND "
    "event_type::text = "
    "'worker.corrected'::text AND "
    "result_version >= 2 OR command_type::text "
    "= 'correct_worker_contact'::text AND "
    "entity_type::text = 'worker_contact'::text "
    "AND event_type::text = "
    "'worker_contact.corrected'::text AND "
    "result_version >= 2 OR command_type::text "
    "= 'correct_worker_residence'::text AND "
    "entity_type::text = "
    "'worker_residence'::text AND "
    "event_type::text = "
    "'worker_residence.corrected'::text AND "
    "result_version >= 2 OR command_type::text "
    "= 'correct_worker_preferences'::text AND "
    "entity_type::text = "
    "'worker_preferences'::text AND "
    "event_type::text = "
    "'worker_preferences.corrected'::text AND "
    "result_version >= 2 OR command_type::text "
    "= 'correct_contact_details'::text AND "
    "entity_type::text = "
    "'employer_contact_details'::text AND "
    "event_type::text = "
    "'employer_contact_details.corrected'::text "
    "AND result_version >= 2 OR "
    "command_type::text = "
    "'correct_contact_address'::text AND "
    "entity_type::text = "
    "'employer_contact_details'::text AND "
    "event_type::text = "
    "'employer_contact_details.corrected'::text "
    "AND result_version >= 2 OR "
    "command_type::text = "
    "'correct_employer_address'::text AND "
    "entity_type::text = "
    "'employer_address'::text AND "
    "event_type::text = "
    "'employer_address.corrected'::text AND "
    "result_version >= 2 OR command_type::text "
    "= 'correct_worksite_address'::text AND "
    "entity_type::text = 'worksite'::text AND "
    "event_type::text = "
    "'worksite.corrected'::text AND "
    "result_version >= 2 OR command_type::text "
    "= 'correct_staffing_request'::text AND "
    "entity_type::text = "
    "'staffing_request'::text AND "
    "event_type::text = "
    "'staffing_request.corrected'::text AND "
    "result_version >= 2 OR command_type::text "
    "= 'review_canonical_outputs'::text AND "
    "entity_type::text = "
    "'canonical_output_review'::text AND "
    "event_type::text = "
    "'canonical_output_review.reviewed'::text "
    "AND result_version >= 1)",
    "command_results.ck_command_results_version_positive": "CHECK (result_version >= 1)",
    "command_results.command_results_pkey": "PRIMARY KEY (command_id, entity_type, entity_id)",
    "command_results.fk_command_results_entity_authority": "FOREIGN KEY (entity_type, entity_id) "
    "REFERENCES "
    "entity_authorities(entity_type, "
    "entity_id) DEFERRABLE INITIALLY DEFERRED",
    "command_results.fk_command_results_exact_audit": "FOREIGN KEY (command_id, entity_id, "
    "result_version, event_type, actor_id) "
    "REFERENCES audit_events(command_id, entity_id, "
    "new_record_version, event_type, actor_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "command_results.fk_command_results_receipt_actor_type": "FOREIGN KEY (command_id, actor_id, "
    "command_type) REFERENCES "
    "command_receipts(command_id, actor_id, "
    "command_type) DEFERRABLE INITIALLY "
    "DEFERRED",
    "command_results.fk_command_results_typed_audit": "FOREIGN KEY (command_id, entity_type, "
    "entity_id) REFERENCES audit_events(command_id, "
    "entity_type, entity_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "command_results.guard_finalization_results": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "command_results.uq_command_results_exact_authority": "UNIQUE (command_id, entity_type, "
    "entity_id, result_version, event_type, "
    "actor_id)",
    "employer_addresses.employer_addresses_check1": "CHECK (line1 IS NOT NULL AND btrim(line1::text) "
    "<> ''::text AND locality IS NOT NULL AND "
    "btrim(locality::text) <> ''::text AND country IS "
    "NOT NULL AND country::text ~ '^[A-Z]{2}$'::text "
    "AND (country::text <> 'US'::text OR region IS "
    "NOT NULL AND btrim(region::text) <> ''::text AND "
    "postal_code IS NOT NULL AND "
    "btrim(postal_code::text) <> ''::text))",
    "employer_addresses.employer_addresses_employer_id_employer_address_id_key": "UNIQUE "
    "(employer_id, "
    "employer_address_id)",
    "employer_addresses.employer_addresses_employer_id_fkey": "FOREIGN KEY (employer_id) REFERENCES "
    "employers(employer_id)",
    "employer_addresses.employer_addresses_pkey": "PRIMARY KEY (employer_address_id)",
    "employer_addresses.employer_addresses_purpose_check": "CHECK (purpose::text = 'business'::text)",
    "employer_addresses.employer_addresses_version_check": "CHECK (version >= 1)",
    "employer_addresses.guard_canonical_correction": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "employer_addresses.guard_employer_output": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "employer_contact_details.employer_contact_details_check1": "CHECK (line1 IS NOT NULL AND "
    "btrim(line1::text) <> ''::text AND "
    "locality IS NOT NULL AND "
    "btrim(locality::text) <> ''::text "
    "AND country IS NOT NULL AND "
    "country::text ~ '^[A-Z]{2}$'::text "
    "AND (country::text <> 'US'::text OR "
    "region IS NOT NULL AND "
    "btrim(region::text) <> ''::text AND "
    "postal_code IS NOT NULL AND "
    "btrim(postal_code::text) <> "
    "''::text) OR line1 IS NULL AND line2 "
    "IS NULL AND locality IS NULL AND "
    "region IS NULL AND postal_code IS "
    "NULL AND country IS NULL)",
    "employer_contact_details.employer_contact_details_employer_contact_id_key": "UNIQUE "
    "(employer_contact_id)",
    "employer_contact_details.employer_contact_details_employer_id_employer_contact_detai_key": "UNIQUE "
    "(employer_id, "
    "employer_contact_details_id)",
    "employer_contact_details.employer_contact_details_employer_id_employer_contact_id_fkey": "FOREIGN "
    "KEY "
    "(employer_id, "
    "employer_contact_id) "
    "REFERENCES "
    "employer_contacts(employer_id, "
    "employer_contact_id)",
    "employer_contact_details.employer_contact_details_phone_check": "CHECK (btrim(phone::text) <> "
    "''::text)",
    "employer_contact_details.employer_contact_details_pkey": "PRIMARY KEY "
    "(employer_contact_details_id)",
    "employer_contact_details.employer_contact_details_representative_name_check": "CHECK "
    "(btrim(representative_name::text) "
    "<> ''::text)",
    "employer_contact_details.employer_contact_details_version_check": "CHECK (version >= 1)",
    "employer_contact_details.guard_canonical_correction": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "employer_contact_details.guard_employer_output": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "employer_contact_details.uq_contact_details_link_parent": "UNIQUE (employer_id, "
    "employer_contact_id, "
    "employer_contact_details_id)",
    "employer_contacts.ck_employer_contacts_full_name_nonblank": "CHECK (btrim(full_name::text) <> "
    "''::text)",
    "employer_contacts.ck_employer_contacts_version_is_one": "CHECK (version = 1)",
    "employer_contacts.employer_contacts_pkey": "PRIMARY KEY (employer_contact_id)",
    "employer_contacts.fk_employer_contacts_employer": "FOREIGN KEY (employer_id) REFERENCES "
    "employers(employer_id)",
    "employer_contacts.guard_employer_output": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "employer_contacts.uq_employer_contacts_parent_scoped_identity": "UNIQUE (employer_id, "
    "employer_contact_id)",
    "employers.ck_employers_display_name_nonblank": "CHECK (btrim(display_name::text) <> ''::text)",
    "employers.ck_employers_lifecycle_status_draft": "CHECK (lifecycle_status::text = 'draft'::text)",
    "employers.ck_employers_source_channel_staff_entry": "CHECK (source_channel::text = "
    "'staff_entry'::text)",
    "employers.ck_employers_type": "CHECK (employer_type::text = ANY (ARRAY['household'::character "
    "varying, 'business'::character varying]::text[]))",
    "employers.ck_employers_version_positive": "CHECK (version >= 1)",
    "employers.employers_pkey": "PRIMARY KEY (employer_id)",
    "employers.guard_employer_output": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "entity_authorities.ck_entity_authorities_entity_type": "CHECK ((entity_type::text = ANY "
    "(ARRAY['employer'::character "
    "varying::text, "
    "'employer_contact'::character "
    "varying::text, 'intake'::character "
    "varying::text, "
    "'work_interest'::character "
    "varying::text, 'worker'::character "
    "varying::text, "
    "'worker_contact'::character "
    "varying::text, "
    "'worker_residence'::character "
    "varying::text, "
    "'worker_preferences'::character "
    "varying::text, "
    "'employer_contact_details'::character "
    "varying::text, "
    "'employer_address'::character "
    "varying::text, 'worksite'::character "
    "varying::text, "
    "'staffing_request'::character "
    "varying::text])) OR entity_type::text = "
    "'canonical_output_review'::text)",
    "entity_authorities.ck_entity_authorities_exactly_one_concrete_id": "CHECK ((entity_type::text = "
    "'employer'::text AND "
    "employer_id IS NOT NULL AND "
    "employer_id = entity_id AND "
    "employer_contact_id IS NULL "
    "AND intake_id IS NULL AND "
    "work_interest_id IS NULL AND "
    "worker_id IS NULL AND "
    "worker_contact_id IS NULL "
    "AND worker_residence_id IS "
    "NULL AND "
    "worker_preferences_id IS "
    "NULL AND "
    "employer_contact_details_id "
    "IS NULL AND "
    "employer_address_id IS NULL "
    "AND worksite_id IS NULL AND "
    "staffing_request_id IS NULL "
    "OR entity_type::text = "
    "'employer_contact'::text AND "
    "employer_contact_id IS NOT "
    "NULL AND employer_contact_id "
    "= entity_id AND employer_id "
    "IS NULL AND intake_id IS "
    "NULL AND work_interest_id IS "
    "NULL AND worker_id IS NULL "
    "AND worker_contact_id IS "
    "NULL AND worker_residence_id "
    "IS NULL AND "
    "worker_preferences_id IS "
    "NULL AND "
    "employer_contact_details_id "
    "IS NULL AND "
    "employer_address_id IS NULL "
    "AND worksite_id IS NULL AND "
    "staffing_request_id IS NULL "
    "OR entity_type::text = "
    "'intake'::text AND intake_id "
    "IS NOT NULL AND intake_id = "
    "entity_id AND employer_id IS "
    "NULL AND employer_contact_id "
    "IS NULL AND work_interest_id "
    "IS NULL AND worker_id IS "
    "NULL AND worker_contact_id "
    "IS NULL AND "
    "worker_residence_id IS NULL "
    "AND worker_preferences_id IS "
    "NULL AND "
    "employer_contact_details_id "
    "IS NULL AND "
    "employer_address_id IS NULL "
    "AND worksite_id IS NULL AND "
    "staffing_request_id IS NULL "
    "OR entity_type::text = "
    "'work_interest'::text AND "
    "work_interest_id IS NOT NULL "
    "AND work_interest_id = "
    "entity_id AND employer_id IS "
    "NULL AND employer_contact_id "
    "IS NULL AND intake_id IS "
    "NULL AND worker_id IS NULL "
    "AND worker_contact_id IS "
    "NULL AND worker_residence_id "
    "IS NULL AND "
    "worker_preferences_id IS "
    "NULL AND "
    "employer_contact_details_id "
    "IS NULL AND "
    "employer_address_id IS NULL "
    "AND worksite_id IS NULL AND "
    "staffing_request_id IS NULL "
    "OR entity_type::text = "
    "'worker'::text AND worker_id "
    "IS NOT NULL AND worker_id = "
    "entity_id AND employer_id IS "
    "NULL AND employer_contact_id "
    "IS NULL AND intake_id IS "
    "NULL AND work_interest_id IS "
    "NULL AND worker_contact_id "
    "IS NULL AND "
    "worker_residence_id IS NULL "
    "AND worker_preferences_id IS "
    "NULL AND "
    "employer_contact_details_id "
    "IS NULL AND "
    "employer_address_id IS NULL "
    "AND worksite_id IS NULL AND "
    "staffing_request_id IS NULL "
    "OR entity_type::text = "
    "'worker_contact'::text AND "
    "worker_contact_id IS NOT "
    "NULL AND worker_contact_id = "
    "entity_id AND employer_id IS "
    "NULL AND employer_contact_id "
    "IS NULL AND intake_id IS "
    "NULL AND work_interest_id IS "
    "NULL AND worker_id IS NULL "
    "AND worker_residence_id IS "
    "NULL AND "
    "worker_preferences_id IS "
    "NULL AND "
    "employer_contact_details_id "
    "IS NULL AND "
    "employer_address_id IS NULL "
    "AND worksite_id IS NULL AND "
    "staffing_request_id IS NULL "
    "OR entity_type::text = "
    "'worker_residence'::text AND "
    "worker_residence_id IS NOT "
    "NULL AND worker_residence_id "
    "= entity_id AND employer_id "
    "IS NULL AND "
    "employer_contact_id IS NULL "
    "AND intake_id IS NULL AND "
    "work_interest_id IS NULL AND "
    "worker_id IS NULL AND "
    "worker_contact_id IS NULL "
    "AND worker_preferences_id IS "
    "NULL AND "
    "employer_contact_details_id "
    "IS NULL AND "
    "employer_address_id IS NULL "
    "AND worksite_id IS NULL AND "
    "staffing_request_id IS NULL "
    "OR entity_type::text = "
    "'worker_preferences'::text "
    "AND worker_preferences_id IS "
    "NOT NULL AND "
    "worker_preferences_id = "
    "entity_id AND employer_id IS "
    "NULL AND employer_contact_id "
    "IS NULL AND intake_id IS "
    "NULL AND work_interest_id IS "
    "NULL AND worker_id IS NULL "
    "AND worker_contact_id IS "
    "NULL AND worker_residence_id "
    "IS NULL AND "
    "employer_contact_details_id "
    "IS NULL AND "
    "employer_address_id IS NULL "
    "AND worksite_id IS NULL AND "
    "staffing_request_id IS NULL "
    "OR entity_type::text = "
    "'employer_contact_details'::text "
    "AND "
    "employer_contact_details_id "
    "IS NOT NULL AND "
    "employer_contact_details_id "
    "= entity_id AND employer_id "
    "IS NULL AND "
    "employer_contact_id IS NULL "
    "AND intake_id IS NULL AND "
    "work_interest_id IS NULL AND "
    "worker_id IS NULL AND "
    "worker_contact_id IS NULL "
    "AND worker_residence_id IS "
    "NULL AND "
    "worker_preferences_id IS "
    "NULL AND employer_address_id "
    "IS NULL AND worksite_id IS "
    "NULL AND staffing_request_id "
    "IS NULL OR entity_type::text "
    "= 'employer_address'::text "
    "AND employer_address_id IS "
    "NOT NULL AND "
    "employer_address_id = "
    "entity_id AND employer_id IS "
    "NULL AND employer_contact_id "
    "IS NULL AND intake_id IS "
    "NULL AND work_interest_id IS "
    "NULL AND worker_id IS NULL "
    "AND worker_contact_id IS "
    "NULL AND worker_residence_id "
    "IS NULL AND "
    "worker_preferences_id IS "
    "NULL AND "
    "employer_contact_details_id "
    "IS NULL AND worksite_id IS "
    "NULL AND staffing_request_id "
    "IS NULL OR entity_type::text "
    "= 'worksite'::text AND "
    "worksite_id IS NOT NULL AND "
    "worksite_id = entity_id AND "
    "employer_id IS NULL AND "
    "employer_contact_id IS NULL "
    "AND intake_id IS NULL AND "
    "work_interest_id IS NULL AND "
    "worker_id IS NULL AND "
    "worker_contact_id IS NULL "
    "AND worker_residence_id IS "
    "NULL AND "
    "worker_preferences_id IS "
    "NULL AND "
    "employer_contact_details_id "
    "IS NULL AND "
    "employer_address_id IS NULL "
    "AND staffing_request_id IS "
    "NULL OR entity_type::text = "
    "'staffing_request'::text AND "
    "staffing_request_id IS NOT "
    "NULL AND staffing_request_id "
    "= entity_id AND employer_id "
    "IS NULL AND "
    "employer_contact_id IS NULL "
    "AND intake_id IS NULL AND "
    "work_interest_id IS NULL AND "
    "worker_id IS NULL AND "
    "worker_contact_id IS NULL "
    "AND worker_residence_id IS "
    "NULL AND "
    "worker_preferences_id IS "
    "NULL AND "
    "employer_contact_details_id "
    "IS NULL AND "
    "employer_address_id IS NULL "
    "AND worksite_id IS NULL) AND "
    "canonical_output_review_id "
    "IS NULL OR entity_type::text "
    "= "
    "'canonical_output_review'::text "
    "AND "
    "canonical_output_review_id = "
    "entity_id AND "
    "canonical_output_review_id "
    "IS NOT NULL AND employer_id "
    "IS NULL AND "
    "employer_contact_id IS NULL "
    "AND intake_id IS NULL AND "
    "work_interest_id IS NULL AND "
    "worker_id IS NULL AND "
    "worker_contact_id IS NULL "
    "AND worker_residence_id IS "
    "NULL AND "
    "worker_preferences_id IS "
    "NULL AND "
    "employer_contact_details_id "
    "IS NULL AND "
    "employer_address_id IS NULL "
    "AND worksite_id IS NULL AND "
    "staffing_request_id IS NULL)",
    "entity_authorities.entity_authorities_canonical_output_review_id_fkey": "FOREIGN KEY "
    "(canonical_output_review_id) "
    "REFERENCES "
    "canonical_review_heads(canonical_output_review_id) "
    "DEFERRABLE INITIALLY "
    "DEFERRED",
    "entity_authorities.entity_authorities_canonical_output_review_id_key": "UNIQUE "
    "(canonical_output_review_id)",
    "entity_authorities.entity_authorities_employer_address_id_fkey": "FOREIGN KEY "
    "(employer_address_id) "
    "REFERENCES "
    "employer_addresses(employer_address_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "entity_authorities.entity_authorities_employer_address_id_key": "UNIQUE (employer_address_id)",
    "entity_authorities.entity_authorities_employer_contact_details_id_fkey": "FOREIGN KEY "
    "(employer_contact_details_id) "
    "REFERENCES "
    "employer_contact_details(employer_contact_details_id) "
    "DEFERRABLE INITIALLY "
    "DEFERRED",
    "entity_authorities.entity_authorities_employer_contact_details_id_key": "UNIQUE "
    "(employer_contact_details_id)",
    "entity_authorities.entity_authorities_pkey": "PRIMARY KEY (entity_type, entity_id)",
    "entity_authorities.entity_authorities_staffing_request_id_fkey": "FOREIGN KEY "
    "(staffing_request_id) "
    "REFERENCES "
    "staffing_requests(staffing_request_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "entity_authorities.entity_authorities_staffing_request_id_key": "UNIQUE (staffing_request_id)",
    "entity_authorities.entity_authorities_work_interest_id_key": "UNIQUE (work_interest_id)",
    "entity_authorities.entity_authorities_worker_contact_id_key": "UNIQUE (worker_contact_id)",
    "entity_authorities.entity_authorities_worker_id_key": "UNIQUE (worker_id)",
    "entity_authorities.entity_authorities_worker_preferences_id_key": "UNIQUE "
    "(worker_preferences_id)",
    "entity_authorities.entity_authorities_worker_residence_id_key": "UNIQUE (worker_residence_id)",
    "entity_authorities.entity_authorities_worksite_id_fkey": "FOREIGN KEY (worksite_id) REFERENCES "
    "worksites(worksite_id) DEFERRABLE "
    "INITIALLY DEFERRED",
    "entity_authorities.entity_authorities_worksite_id_key": "UNIQUE (worksite_id)",
    "entity_authorities.fk_entity_authorities_employer": "FOREIGN KEY (employer_id) REFERENCES "
    "employers(employer_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "entity_authorities.fk_entity_authorities_employer_contact": "FOREIGN KEY (employer_contact_id) "
    "REFERENCES "
    "employer_contacts(employer_contact_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "entity_authorities.fk_entity_authorities_intake": "FOREIGN KEY (intake_id) REFERENCES "
    "intakes(intake_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "entity_authorities.fk_entity_authorities_work_interest": "FOREIGN KEY (work_interest_id) "
    "REFERENCES work_interests(interest_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "entity_authorities.fk_entity_authorities_worker": "FOREIGN KEY (worker_id) REFERENCES "
    "workers(worker_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "entity_authorities.fk_entity_authorities_worker_contact": "FOREIGN KEY (worker_contact_id) "
    "REFERENCES "
    "worker_contacts(worker_contact_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "entity_authorities.fk_entity_authorities_worker_preferences": "FOREIGN KEY "
    "(worker_preferences_id) "
    "REFERENCES "
    "worker_preferences(worker_preferences_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "entity_authorities.fk_entity_authorities_worker_residence": "FOREIGN KEY (worker_residence_id) "
    "REFERENCES "
    "worker_residences(worker_residence_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "entity_authorities.uq_entity_authorities_employer_contact_id": "UNIQUE (employer_contact_id)",
    "entity_authorities.uq_entity_authorities_employer_id": "UNIQUE (employer_id)",
    "entity_authorities.uq_entity_authorities_intake_id": "UNIQUE (intake_id)",
    "intake_addresses.ck_intake_addresses_country": "CHECK (country IS NULL OR country::text ~ "
    "'^[A-Z]{2}$'::text)",
    "intake_addresses.ck_intake_addresses_nonblank": "CHECK ((line1 IS NULL OR btrim(line1::text) <> "
    "''::text) AND (line2 IS NULL OR "
    "btrim(line2::text) <> ''::text) AND (locality "
    "IS NULL OR btrim(locality::text) <> ''::text) "
    "AND (region IS NULL OR btrim(region::text) <> "
    "''::text) AND (postal_code IS NULL OR "
    "btrim(postal_code::text) <> ''::text))",
    "intake_addresses.ck_intake_addresses_section": "CHECK (section::text = ANY "
    "(ARRAY['worker_residence'::character varying, "
    "'party_address'::character varying, "
    "'worksite_address'::character varying]::text[]))",
    "intake_addresses.fk_intake_addresses_intake": "FOREIGN KEY (intake_id) REFERENCES "
    "intakes(intake_id)",
    "intake_addresses.guard_intake_address_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "intake_addresses.intake_addresses_pkey": "PRIMARY KEY (intake_id, section)",
    "intake_finalizations.ck_finalization_reuse_shape": "CHECK (kind::text = 'worker'::text AND "
    "worker_disposition::text = "
    "worker_contact_disposition::text AND "
    "worker_disposition::text = "
    "worker_residence_disposition::text AND "
    "worker_disposition::text = "
    "worker_preferences_disposition::text OR "
    "kind::text = 'employer'::text AND "
    "staffing_request_disposition::text = "
    "'created'::text AND "
    "employer_contact_disposition::text = "
    "employer_contact_details_disposition::text "
    "AND (employer_disposition::text = "
    "'reused'::text OR "
    "employer_contact_disposition::text = "
    "'created'::text AND "
    "worksite_disposition::text = 'created'::text "
    "AND COALESCE(employer_address_disposition, "
    "'created'::character varying)::text = "
    "'created'::text))",
    "intake_finalizations.ck_intake_finalizations_kind_shape": "CHECK (kind::text = 'worker'::text "
    "AND worker_id IS NOT NULL AND "
    "worker_version IS NOT NULL AND "
    "worker_disposition IS NOT NULL AND "
    "worker_contact_id IS NOT NULL AND "
    "worker_contact_version IS NOT NULL "
    "AND worker_contact_disposition IS NOT "
    "NULL AND worker_residence_id IS NOT "
    "NULL AND worker_residence_version IS "
    "NOT NULL AND "
    "worker_residence_disposition IS NOT "
    "NULL AND worker_preferences_id IS NOT "
    "NULL AND worker_preferences_version "
    "IS NOT NULL AND "
    "worker_preferences_disposition IS NOT "
    "NULL AND employer_id IS NULL AND "
    "employer_version IS NULL AND "
    "employer_disposition IS NULL AND "
    "employer_contact_id IS NULL AND "
    "employer_contact_version IS NULL AND "
    "employer_contact_disposition IS NULL "
    "AND employer_contact_details_id IS "
    "NULL AND "
    "employer_contact_details_version IS "
    "NULL AND "
    "employer_contact_details_disposition "
    "IS NULL AND employer_address_id IS "
    "NULL AND employer_address_version IS "
    "NULL AND employer_address_disposition "
    "IS NULL AND worksite_id IS NULL AND "
    "worksite_version IS NULL AND "
    "worksite_disposition IS NULL AND "
    "staffing_request_id IS NULL AND "
    "staffing_request_version IS NULL AND "
    "staffing_request_disposition IS NULL "
    "OR kind::text = 'employer'::text AND "
    "employer_id IS NOT NULL AND "
    "employer_version IS NOT NULL AND "
    "employer_disposition IS NOT NULL AND "
    "employer_contact_id IS NOT NULL AND "
    "employer_contact_version IS NOT NULL "
    "AND employer_contact_disposition IS "
    "NOT NULL AND "
    "employer_contact_details_id IS NOT "
    "NULL AND "
    "employer_contact_details_version IS "
    "NOT NULL AND "
    "employer_contact_details_disposition "
    "IS NOT NULL AND worksite_id IS NOT "
    "NULL AND worksite_version IS NOT NULL "
    "AND worksite_disposition IS NOT NULL "
    "AND staffing_request_id IS NOT NULL "
    "AND staffing_request_version IS NOT "
    "NULL AND staffing_request_disposition "
    "IS NOT NULL AND worker_id IS NULL AND "
    "worker_version IS NULL AND "
    "worker_disposition IS NULL AND "
    "worker_contact_id IS NULL AND "
    "worker_contact_version IS NULL AND "
    "worker_contact_disposition IS NULL "
    "AND worker_residence_id IS NULL AND "
    "worker_residence_version IS NULL AND "
    "worker_residence_disposition IS NULL "
    "AND worker_preferences_id IS NULL AND "
    "worker_preferences_version IS NULL "
    "AND worker_preferences_disposition IS "
    "NULL AND (employer_address_id IS NULL "
    "AND employer_address_version IS NULL "
    "AND employer_address_disposition IS "
    "NULL OR employer_address_id IS NOT "
    "NULL AND employer_address_version IS "
    "NOT NULL AND "
    "employer_address_disposition IS NOT "
    "NULL))",
    "intake_finalizations.guard_finalization_results": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "intake_finalizations.intake_finalizations_command_id_fkey": "FOREIGN KEY (command_id) REFERENCES "
    "command_receipts(command_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_finalizations.intake_finalizations_command_id_key": "UNIQUE (command_id)",
    "intake_finalizations.intake_finalizations_content_version_check": "CHECK (content_version >= 1)",
    "intake_finalizations.intake_finalizations_employer_address_disposition_check": "CHECK "
    "(employer_address_disposition::text "
    "= ANY "
    "(ARRAY['created'::character "
    "varying, "
    "'reused'::character "
    "varying]::text[]))",
    "intake_finalizations.intake_finalizations_employer_address_version_check": "CHECK "
    "(employer_address_version "
    ">= 1 AND "
    "(employer_address_disposition::text "
    "<> 'created'::text "
    "OR "
    "employer_address_version "
    "= 1))",
    "intake_finalizations.intake_finalizations_employer_contact_details_disposition_check": "CHECK "
    "(employer_contact_details_disposition::text "
    "= ANY "
    "(ARRAY['created'::character "
    "varying, "
    "'reused'::character "
    "varying]::text[]))",
    "intake_finalizations.intake_finalizations_employer_contact_details_version_check": "CHECK "
    "(employer_contact_details_version "
    ">= 1 AND "
    "(employer_contact_details_disposition::text "
    "<> "
    "'created'::text "
    "OR "
    "employer_contact_details_version "
    "= 1))",
    "intake_finalizations.intake_finalizations_employer_contact_disposition_check": "CHECK "
    "(employer_contact_disposition::text "
    "= ANY "
    "(ARRAY['created'::character "
    "varying, "
    "'reused'::character "
    "varying]::text[]))",
    "intake_finalizations.intake_finalizations_employer_contact_version_check": "CHECK "
    "(employer_contact_version "
    ">= 1 AND "
    "(employer_contact_disposition::text "
    "<> 'created'::text "
    "OR "
    "employer_contact_version "
    "= 1))",
    "intake_finalizations.intake_finalizations_employer_disposition_check": "CHECK "
    "(employer_disposition::text "
    "= ANY "
    "(ARRAY['created'::character "
    "varying, "
    "'reused'::character "
    "varying]::text[]))",
    "intake_finalizations.intake_finalizations_employer_id_employer_address_id_fkey": "FOREIGN KEY "
    "(employer_id, "
    "employer_address_id) "
    "REFERENCES "
    "employer_addresses(employer_id, "
    "employer_address_id)",
    "intake_finalizations.intake_finalizations_employer_id_employer_contact_details__fkey": "FOREIGN "
    "KEY "
    "(employer_id, "
    "employer_contact_details_id) "
    "REFERENCES "
    "employer_contact_details(employer_id, "
    "employer_contact_details_id)",
    "intake_finalizations.intake_finalizations_employer_id_employer_contact_id_fkey": "FOREIGN KEY "
    "(employer_id, "
    "employer_contact_id) "
    "REFERENCES "
    "employer_contacts(employer_id, "
    "employer_contact_id)",
    "intake_finalizations.intake_finalizations_employer_id_fkey": "FOREIGN KEY (employer_id) "
    "REFERENCES employers(employer_id)",
    "intake_finalizations.intake_finalizations_employer_id_staffing_request_id_fkey": "FOREIGN KEY "
    "(employer_id, "
    "staffing_request_id) "
    "REFERENCES "
    "staffing_requests(employer_id, "
    "staffing_request_id)",
    "intake_finalizations.intake_finalizations_employer_id_worksite_id_fkey": "FOREIGN KEY "
    "(employer_id, "
    "worksite_id) "
    "REFERENCES "
    "worksites(employer_id, "
    "worksite_id)",
    "intake_finalizations.intake_finalizations_employer_version_check": "CHECK (employer_version >= 1 "
    "AND "
    "(employer_disposition::text "
    "<> 'created'::text OR "
    "employer_version = 1))",
    "intake_finalizations.intake_finalizations_intake_id_fkey": "FOREIGN KEY (intake_id) REFERENCES "
    "intakes(intake_id)",
    "intake_finalizations.intake_finalizations_intake_id_review_id_fkey": "FOREIGN KEY (intake_id, "
    "review_id) REFERENCES "
    "intake_reviews(intake_id, "
    "review_id)",
    "intake_finalizations.intake_finalizations_pkey": "PRIMARY KEY (intake_id)",
    "intake_finalizations.intake_finalizations_result_version_check": "CHECK (result_version >= 3)",
    "intake_finalizations.intake_finalizations_staffing_request_disposition_check": "CHECK "
    "(staffing_request_disposition::text "
    "= "
    "'created'::text)",
    "intake_finalizations.intake_finalizations_staffing_request_id_key": "UNIQUE "
    "(staffing_request_id)",
    "intake_finalizations.intake_finalizations_staffing_request_version_check": "CHECK "
    "(staffing_request_version "
    "= 1)",
    "intake_finalizations.intake_finalizations_worker_contact_disposition_check": "CHECK "
    "(worker_contact_disposition::text "
    "= ANY "
    "(ARRAY['created'::character "
    "varying, "
    "'reused'::character "
    "varying]::text[]))",
    "intake_finalizations.intake_finalizations_worker_contact_version_check": "CHECK "
    "(worker_contact_version "
    ">= 1 AND "
    "(worker_contact_disposition::text "
    "<> 'created'::text OR "
    "worker_contact_version "
    "= 1))",
    "intake_finalizations.intake_finalizations_worker_disposition_check": "CHECK "
    "(worker_disposition::text "
    "= ANY "
    "(ARRAY['created'::character "
    "varying, "
    "'reused'::character "
    "varying]::text[]))",
    "intake_finalizations.intake_finalizations_worker_id_fkey": "FOREIGN KEY (worker_id) REFERENCES "
    "workers(worker_id)",
    "intake_finalizations.intake_finalizations_worker_id_worker_contact_id_fkey": "FOREIGN KEY "
    "(worker_id, "
    "worker_contact_id) "
    "REFERENCES "
    "worker_contacts(worker_id, "
    "worker_contact_id)",
    "intake_finalizations.intake_finalizations_worker_id_worker_preferences_id_fkey": "FOREIGN KEY "
    "(worker_id, "
    "worker_preferences_id) "
    "REFERENCES "
    "worker_preferences(worker_id, "
    "worker_preferences_id)",
    "intake_finalizations.intake_finalizations_worker_id_worker_residence_id_fkey": "FOREIGN KEY "
    "(worker_id, "
    "worker_residence_id) "
    "REFERENCES "
    "worker_residences(worker_id, "
    "worker_residence_id)",
    "intake_finalizations.intake_finalizations_worker_preferences_disposition_check": "CHECK "
    "(worker_preferences_disposition::text "
    "= ANY "
    "(ARRAY['created'::character "
    "varying, "
    "'reused'::character "
    "varying]::text[]))",
    "intake_finalizations.intake_finalizations_worker_preferences_version_check": "CHECK "
    "(worker_preferences_version "
    ">= 1 AND "
    "(worker_preferences_disposition::text "
    "<> 'created'::text "
    "OR "
    "worker_preferences_version "
    "= 1))",
    "intake_finalizations.intake_finalizations_worker_residence_disposition_check": "CHECK "
    "(worker_residence_disposition::text "
    "= ANY "
    "(ARRAY['created'::character "
    "varying, "
    "'reused'::character "
    "varying]::text[]))",
    "intake_finalizations.intake_finalizations_worker_residence_version_check": "CHECK "
    "(worker_residence_version "
    ">= 1 AND "
    "(worker_residence_disposition::text "
    "<> 'created'::text "
    "OR "
    "worker_residence_version "
    "= 1))",
    "intake_finalizations.intake_finalizations_worker_version_check": "CHECK (worker_version >= 1 AND "
    "(worker_disposition::text <> "
    "'created'::text OR "
    "worker_version = 1))",
    "intake_finalizations.intake_finalizations_worksite_disposition_check": "CHECK "
    "(worksite_disposition::text "
    "= ANY "
    "(ARRAY['created'::character "
    "varying, "
    "'reused'::character "
    "varying]::text[]))",
    "intake_finalizations.intake_finalizations_worksite_version_check": "CHECK (worksite_version >= 1 "
    "AND "
    "(worksite_disposition::text "
    "<> 'created'::text OR "
    "worksite_version = 1))",
    "intake_follow_up_events.ck_intake_follow_up_shape": "CHECK (action::text = "
    "'needs_follow_up'::text AND review_id IS "
    "NOT NULL AND reason_code IS NOT NULL AND "
    "(reason_code::text = ANY "
    "(ARRAY['missing_information'::character "
    "varying, 'clarification'::character "
    "varying, 'other'::character "
    "varying]::text[])) AND method IS NULL AND "
    "outcome IS NULL OR (action::text = ANY "
    "(ARRAY['reschedule'::character varying, "
    "'reassign'::character varying]::text[])) "
    "AND review_id IS NULL AND reason_code IS "
    "NULL AND method IS NULL AND outcome IS NULL "
    "OR action::text = 'attempt'::text AND "
    "review_id IS NULL AND reason_code IS NULL "
    "AND method IS NOT NULL AND (method::text = "
    "ANY (ARRAY['phone'::character varying, "
    "'email'::character varying, "
    "'in_person'::character varying, "
    "'other'::character varying]::text[])) AND "
    "outcome IS NOT NULL AND (outcome::text = "
    "ANY (ARRAY['no_answer'::character varying, "
    "'voicemail_left'::character varying, "
    "'callback_requested'::character varying, "
    "'contact_reached_information_pending'::character "
    "varying, "
    "'invalid_contact_information'::character "
    "varying, 'information_received'::character "
    "varying, 'other'::character "
    "varying]::text[])))",
    "intake_follow_up_events.fk_intake_follow_up_required_payload": "FOREIGN KEY (event_id) "
    "REFERENCES "
    "intake_history_payloads(event_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_follow_up_events.guard_intake_workflow_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "intake_follow_up_events.intake_follow_up_events_action_check": "CHECK (action::text = ANY "
    "(ARRAY['needs_follow_up'::character "
    "varying, 'reschedule'::character "
    "varying, 'reassign'::character "
    "varying, 'attempt'::character "
    "varying]::text[]))",
    "intake_follow_up_events.intake_follow_up_events_actor_display_name_check": "CHECK "
    "(btrim(actor_display_name::text) "
    "<> ''::text)",
    "intake_follow_up_events.intake_follow_up_events_check": "CHECK (content_version >= 1 AND "
    "content_version < version)",
    "intake_follow_up_events.intake_follow_up_events_command_id_fkey": "FOREIGN KEY (command_id) "
    "REFERENCES "
    "command_receipts(command_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_follow_up_events.intake_follow_up_events_command_id_key": "UNIQUE (command_id)",
    "intake_follow_up_events.intake_follow_up_events_event_id_fkey": "FOREIGN KEY (event_id) "
    "REFERENCES "
    "audit_events(audit_event_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_follow_up_events.intake_follow_up_events_intake_id_fkey": "FOREIGN KEY (intake_id) "
    "REFERENCES intakes(intake_id)",
    "intake_follow_up_events.intake_follow_up_events_intake_id_review_id_fkey": "FOREIGN KEY "
    "(intake_id, "
    "review_id) "
    "REFERENCES "
    "intake_reviews(intake_id, "
    "review_id) "
    "DEFERRABLE INITIALLY "
    "DEFERRED",
    "intake_follow_up_events.intake_follow_up_events_intake_id_version_key": "UNIQUE (intake_id, "
    "version)",
    "intake_follow_up_events.intake_follow_up_events_pkey": "PRIMARY KEY (event_id)",
    "intake_follow_up_events.intake_follow_up_events_time_zone_check": "CHECK (btrim(time_zone::text) "
    "<> ''::text)",
    "intake_follow_up_events.intake_follow_up_events_version_check": "CHECK (version >= 2)",
    "intake_history_payloads.guard_intake_workflow_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "intake_history_payloads.intake_history_payloads_event_id_fkey": "FOREIGN KEY (event_id) "
    "REFERENCES "
    "intake_follow_up_events(event_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_history_payloads.intake_history_payloads_note_check": "CHECK (note IS NULL OR "
    "btrim(note::text) <> ''::text)",
    "intake_history_payloads.intake_history_payloads_pkey": "PRIMARY KEY (event_id)",
    "intake_history_payloads.intake_history_payloads_reason_text_check": "CHECK "
    "(btrim(reason_text::text) "
    "<> ''::text)",
    "intake_links.ck_intake_links_contact_pair": "CHECK (employer_contact_id IS NULL AND "
    "employer_contact_details_id IS NULL OR "
    "employer_contact_id IS NOT NULL AND "
    "employer_contact_details_id IS NOT NULL)",
    "intake_links.ck_intake_links_employer_address_reference": "CHECK (employer_address_id IS NULL "
    "AND employer_address_version IS NULL "
    "OR employer_address_id IS NOT NULL "
    "AND employer_address_version IS NOT "
    "NULL AND employer_address_version >= "
    "1)",
    "intake_links.ck_intake_links_employer_contact_details_reference": "CHECK "
    "(employer_contact_details_id "
    "IS NULL AND "
    "employer_contact_details_version "
    "IS NULL OR "
    "employer_contact_details_id "
    "IS NOT NULL AND "
    "employer_contact_details_version "
    "IS NOT NULL AND "
    "employer_contact_details_version "
    ">= 1)",
    "intake_links.ck_intake_links_employer_contact_reference": "CHECK (employer_contact_id IS NULL "
    "AND employer_contact_version IS NULL "
    "OR employer_contact_id IS NOT NULL "
    "AND employer_contact_version IS NOT "
    "NULL AND employer_contact_version >= "
    "1)",
    "intake_links.ck_intake_links_parent_shape": "CHECK (worker_id IS NOT NULL AND employer_id IS "
    "NULL AND worker_contact_id IS NOT NULL AND "
    "worker_residence_id IS NOT NULL AND "
    "worker_preferences_id IS NOT NULL AND "
    "employer_contact_id IS NULL AND "
    "employer_contact_details_id IS NULL AND "
    "employer_address_id IS NULL AND worksite_id IS NULL "
    "OR employer_id IS NOT NULL AND worker_id IS NULL "
    "AND worker_contact_id IS NULL AND "
    "worker_residence_id IS NULL AND "
    "worker_preferences_id IS NULL OR worker_id IS NULL "
    "AND employer_id IS NULL AND worker_contact_id IS "
    "NULL AND worker_residence_id IS NULL AND "
    "worker_preferences_id IS NULL AND "
    "employer_contact_id IS NULL AND "
    "employer_contact_details_id IS NULL AND "
    "employer_address_id IS NULL AND worksite_id IS "
    "NULL)",
    "intake_links.ck_intake_links_worker_contact_reference": "CHECK (worker_contact_id IS NULL AND "
    "worker_contact_version IS NULL OR "
    "worker_contact_id IS NOT NULL AND "
    "worker_contact_version IS NOT NULL AND "
    "worker_contact_version >= 1)",
    "intake_links.ck_intake_links_worker_preferences_reference": "CHECK (worker_preferences_id IS "
    "NULL AND worker_preferences_version "
    "IS NULL OR worker_preferences_id IS "
    "NOT NULL AND "
    "worker_preferences_version IS NOT "
    "NULL AND worker_preferences_version "
    ">= 1)",
    "intake_links.ck_intake_links_worker_residence_reference": "CHECK (worker_residence_id IS NULL "
    "AND worker_residence_version IS NULL "
    "OR worker_residence_id IS NOT NULL "
    "AND worker_residence_version IS NOT "
    "NULL AND worker_residence_version >= "
    "1)",
    "intake_links.ck_intake_links_worksite_reference": "CHECK (worksite_id IS NULL AND "
    "worksite_version IS NULL OR worksite_id IS "
    "NOT NULL AND worksite_version IS NOT NULL AND "
    "worksite_version >= 1)",
    "intake_links.fk_intake_links_employer_address": "FOREIGN KEY (employer_id, employer_address_id) "
    "REFERENCES employer_addresses(employer_id, "
    "employer_address_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "intake_links.fk_intake_links_employer_contact": "FOREIGN KEY (employer_id, employer_contact_id) "
    "REFERENCES employer_contacts(employer_id, "
    "employer_contact_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "intake_links.fk_intake_links_employer_contact_details": "FOREIGN KEY (employer_id, "
    "employer_contact_id, "
    "employer_contact_details_id) REFERENCES "
    "employer_contact_details(employer_id, "
    "employer_contact_id, "
    "employer_contact_details_id) DEFERRABLE "
    "INITIALLY DEFERRED",
    "intake_links.fk_intake_links_employer_parent": "FOREIGN KEY (intake_id, employer_id) REFERENCES "
    "intakes(intake_id, employer_id) DEFERRABLE "
    "INITIALLY DEFERRED",
    "intake_links.fk_intake_links_intake": "FOREIGN KEY (intake_id) REFERENCES intakes(intake_id)",
    "intake_links.fk_intake_links_worker_contact": "FOREIGN KEY (worker_id, worker_contact_id) "
    "REFERENCES worker_contacts(worker_id, "
    "worker_contact_id) DEFERRABLE INITIALLY DEFERRED",
    "intake_links.fk_intake_links_worker_parent": "FOREIGN KEY (intake_id, worker_id) REFERENCES "
    "intakes(intake_id, worker_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "intake_links.fk_intake_links_worker_preferences": "FOREIGN KEY (worker_id, "
    "worker_preferences_id) REFERENCES "
    "worker_preferences(worker_id, "
    "worker_preferences_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "intake_links.fk_intake_links_worker_residence": "FOREIGN KEY (worker_id, worker_residence_id) "
    "REFERENCES worker_residences(worker_id, "
    "worker_residence_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "intake_links.fk_intake_links_worksite": "FOREIGN KEY (employer_id, worksite_id) REFERENCES "
    "worksites(employer_id, worksite_id) DEFERRABLE "
    "INITIALLY DEFERRED",
    "intake_links.guard_intake_links": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "intake_links.intake_links_pkey": "PRIMARY KEY (intake_id)",
    "intake_review_payloads.guard_intake_workflow_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "intake_review_payloads.intake_review_payloads_dependency_refs_check": "CHECK "
    "(jsonb_typeof(dependency_refs) "
    "= 'object'::text)",
    "intake_review_payloads.intake_review_payloads_note_check": "CHECK (note IS NULL OR "
    "btrim(note::text) <> ''::text)",
    "intake_review_payloads.intake_review_payloads_pkey": "PRIMARY KEY (review_id)",
    "intake_review_payloads.intake_review_payloads_review_id_fkey": "FOREIGN KEY (review_id) "
    "REFERENCES "
    "intake_reviews(review_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_review_payloads.intake_review_payloads_reviewed_content_check": "CHECK "
    "(jsonb_typeof(reviewed_content) "
    "= 'object'::text)",
    "intake_reviews.fk_intake_reviews_required_payload": "FOREIGN KEY (review_id) REFERENCES "
    "intake_review_payloads(review_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "intake_reviews.guard_intake_workflow_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "intake_reviews.intake_reviews_actor_display_name_check": "CHECK (btrim(actor_display_name::text) "
    "<> ''::text)",
    "intake_reviews.intake_reviews_check": "CHECK (reviewed_content_version >= 1 AND "
    "reviewed_content_version <= reviewed_record_version)",
    "intake_reviews.intake_reviews_check1": "CHECK (result_version = (reviewed_record_version + 1))",
    "intake_reviews.intake_reviews_command_id_fkey": "FOREIGN KEY (command_id) REFERENCES "
    "command_receipts(command_id) DEFERRABLE "
    "INITIALLY DEFERRED",
    "intake_reviews.intake_reviews_command_id_key": "UNIQUE (command_id)",
    "intake_reviews.intake_reviews_event_id_fkey": "FOREIGN KEY (event_id) REFERENCES "
    "audit_events(audit_event_id) DEFERRABLE INITIALLY "
    "DEFERRED",
    "intake_reviews.intake_reviews_event_id_key": "UNIQUE (event_id)",
    "intake_reviews.intake_reviews_intake_id_fkey": "FOREIGN KEY (intake_id) REFERENCES "
    "intakes(intake_id)",
    "intake_reviews.intake_reviews_intake_id_result_version_key": "UNIQUE (intake_id, result_version)",
    "intake_reviews.intake_reviews_intake_id_review_id_key": "UNIQUE (intake_id, review_id)",
    "intake_reviews.intake_reviews_outcome_check": "CHECK (outcome::text = ANY "
    "(ARRAY['intake_reviewed'::character varying, "
    "'needs_follow_up'::character varying]::text[]))",
    "intake_reviews.intake_reviews_pkey": "PRIMARY KEY (review_id)",
    "intake_reviews.intake_reviews_reviewed_record_version_check": "CHECK (reviewed_record_version >= "
    "1)",
    "intakes.ck_intakes_content_kind": "CHECK (kind::text = 'worker'::text AND (content - "
    "ARRAY['full_name'::text, 'phone'::text, 'interests'::text, "
    "'availability'::text]) = '{}'::jsonb OR kind::text = "
    "'employer'::text AND (content - ARRAY['employer_type'::text, "
    "'display_name'::text, 'representative_name'::text, "
    "'phone'::text, 'role_title'::text, 'duties_summary'::text, "
    "'worker_count'::text, 'schedule'::text, 'offer'::text]) = "
    "'{}'::jsonb)",
    "intakes.ck_intakes_content_object": "CHECK (jsonb_typeof(content) = 'object'::text)",
    "intakes.ck_intakes_content_size": "CHECK (octet_length(content::text) <= 32768)",
    "intakes.ck_intakes_content_version": "CHECK (content_version >= 1 AND content_version <= "
    "version)",
    "intakes.ck_intakes_employer_reference": "CHECK (employer_id IS NULL AND employer_version IS NULL "
    "OR employer_id IS NOT NULL AND employer_version IS NOT "
    "NULL AND employer_version >= 1)",
    "intakes.ck_intakes_kind": "CHECK (kind::text = ANY (ARRAY['worker'::character varying, "
    "'employer'::character varying]::text[]))",
    "intakes.ck_intakes_lifecycle_draft": "CHECK (lifecycle_status::text = ANY "
    "(ARRAY['draft'::character varying, 'finalized'::character "
    "varying]::text[]))",
    "intakes.ck_intakes_link_kind": "CHECK (kind::text = 'worker'::text AND employer_id IS NULL OR "
    "kind::text = 'employer'::text AND worker_id IS NULL)",
    "intakes.ck_intakes_schema_version": "CHECK (schema_version = 1)",
    "intakes.ck_intakes_version_positive": "CHECK (version >= 1)",
    "intakes.ck_intakes_worker_reference": "CHECK (worker_id IS NULL AND worker_version IS NULL OR "
    "worker_id IS NOT NULL AND worker_version IS NOT NULL AND "
    "worker_version >= 1)",
    "intakes.fk_intakes_employer": "FOREIGN KEY (employer_id) REFERENCES employers(employer_id)",
    "intakes.fk_intakes_worker": "FOREIGN KEY (worker_id) REFERENCES workers(worker_id)",
    "intakes.guard_intake_links": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "intakes.guard_intake_write_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "intakes.intakes_pkey": "PRIMARY KEY (intake_id)",
    "intakes.uq_intakes_employer_link": "UNIQUE (intake_id, employer_id)",
    "intakes.uq_intakes_id_kind": "UNIQUE (intake_id, kind)",
    "intakes.uq_intakes_worker_link": "UNIQUE (intake_id, worker_id)",
    "staffing_requests.guard_canonical_correction": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "staffing_requests.guard_employer_output": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "staffing_requests.staffing_requests_check1": "CHECK (received_at = created_at)",
    "staffing_requests.staffing_requests_check2": "CHECK ((request_type::text = 'household'::text) = "
    "(employer_address_id IS NULL))",
    "staffing_requests.staffing_requests_duties_summary_check": "CHECK (btrim(duties_summary::text) "
    "<> ''::text)",
    "staffing_requests.staffing_requests_employer_id_employer_address_id_fkey": "FOREIGN KEY "
    "(employer_id, "
    "employer_address_id) "
    "REFERENCES "
    "employer_addresses(employer_id, "
    "employer_address_id)",
    "staffing_requests.staffing_requests_employer_id_employer_contact_id_fkey": "FOREIGN KEY "
    "(employer_id, "
    "employer_contact_id) "
    "REFERENCES "
    "employer_contacts(employer_id, "
    "employer_contact_id)",
    "staffing_requests.staffing_requests_employer_id_fkey": "FOREIGN KEY (employer_id) REFERENCES "
    "employers(employer_id)",
    "staffing_requests.staffing_requests_employer_id_staffing_request_id_key": "UNIQUE (employer_id, "
    "staffing_request_id)",
    "staffing_requests.staffing_requests_employer_id_worksite_id_fkey": "FOREIGN KEY (employer_id, "
    "worksite_id) REFERENCES "
    "worksites(employer_id, "
    "worksite_id)",
    "staffing_requests.staffing_requests_offer_check": "CHECK (jsonb_typeof(offer) = 'object'::text "
    "AND octet_length(offer::text) <= 32768)",
    "staffing_requests.staffing_requests_offer_check1": "CHECK ((offer ?& ARRAY['minimum'::text, "
    "'currency'::text, 'basis'::text, "
    "'per_worker'::text] AND (offer ->> "
    "'minimum'::text) IS NOT NULL AND (offer ->> "
    "'currency'::text) IS NOT NULL AND (offer ->> "
    "'basis'::text) IS NOT NULL AND (offer -> "
    "'per_worker'::text) = 'true'::jsonb) IS "
    "TRUE)",
    "staffing_requests.staffing_requests_pkey": "PRIMARY KEY (staffing_request_id)",
    "staffing_requests.staffing_requests_request_status_check": "CHECK (request_status::text = "
    "ANY (ARRAY['draft'::character varying, "
    "'pending_review'::character varying]::text[]))",
    "staffing_requests.staffing_requests_request_type_check": "CHECK (request_type::text = ANY "
    "(ARRAY['household'::character varying, "
    "'general_labor'::character "
    "varying]::text[]))",
    "staffing_requests.staffing_requests_role_title_check": "CHECK (btrim(role_title::text) <> "
    "''::text)",
    "staffing_requests.staffing_requests_schedule_check": "CHECK (jsonb_typeof(schedule) = "
    "'object'::text AND "
    "octet_length(schedule::text) <= 32768)",
    "staffing_requests.staffing_requests_schedule_check1": "CHECK (((schedule ->> 'mode'::text) = ANY "
    "(ARRAY['to_be_discussed'::text, "
    "'specified'::text])) IS TRUE)",
    "staffing_requests.staffing_requests_source_channel_check": "CHECK (source_channel::text = "
    "'staff_entry'::text)",
    "staffing_requests.staffing_requests_version_check": "CHECK (version >= 1)",
    "staffing_requests.staffing_requests_worker_count_check": "CHECK (worker_count >= 1 AND "
    "worker_count <= 1000)",
    "work_interest_versions.guard_work_interest_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "work_interest_versions.work_interest_versions_command_id_fkey": "FOREIGN KEY (command_id) "
    "REFERENCES "
    "command_receipts(command_id) "
    "DEFERRABLE INITIALLY DEFERRED",
    "work_interest_versions.work_interest_versions_command_id_key": "UNIQUE (command_id)",
    "work_interest_versions.work_interest_versions_interest_id_fkey": "FOREIGN KEY (interest_id) "
    "REFERENCES "
    "work_interests(interest_id)",
    "work_interest_versions.work_interest_versions_label_en_check": "CHECK (btrim(label_en::text) <> "
    "''::text)",
    "work_interest_versions.work_interest_versions_label_es_check": "CHECK (btrim(label_es::text) <> "
    "''::text)",
    "work_interest_versions.work_interest_versions_pkey": "PRIMARY KEY (interest_id, version)",
    "work_interest_versions.work_interest_versions_version_check": "CHECK (version >= 1)",
    "work_interests.ck_work_interests_code": "CHECK (code::text ~ '^[a-z0-9_]{1,64}$'::text)",
    "work_interests.guard_work_interest_authority": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "work_interests.work_interests_code_key": "UNIQUE (code)",
    "work_interests.work_interests_label_en_check": "CHECK (btrim(label_en::text) <> ''::text)",
    "work_interests.work_interests_label_es_check": "CHECK (btrim(label_es::text) <> ''::text)",
    "work_interests.work_interests_pkey": "PRIMARY KEY (interest_id)",
    "work_interests.work_interests_version_check": "CHECK (version >= 1)",
    "worker_contacts.guard_canonical_correction": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "worker_contacts.guard_worker_output": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "worker_contacts.worker_contacts_phone_check": "CHECK (btrim(phone::text) <> ''::text)",
    "worker_contacts.worker_contacts_pkey": "PRIMARY KEY (worker_contact_id)",
    "worker_contacts.worker_contacts_version_check": "CHECK (version >= 1)",
    "worker_contacts.worker_contacts_worker_id_fkey": "FOREIGN KEY (worker_id) REFERENCES "
    "workers(worker_id)",
    "worker_contacts.worker_contacts_worker_id_key": "UNIQUE (worker_id)",
    "worker_contacts.worker_contacts_worker_id_worker_contact_id_key": "UNIQUE (worker_id, "
    "worker_contact_id)",
    "worker_interest_selections.guard_worker_selection": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "worker_interest_selections.worker_interest_selections_interest_id_catalog_version_fkey": "FOREIGN "
    "KEY "
    "(interest_id, "
    "catalog_version) "
    "REFERENCES "
    "work_interest_versions(interest_id, "
    "version)",
    "worker_interest_selections.worker_interest_selections_pkey": "PRIMARY KEY "
    "(worker_preferences_id, "
    "interest_id)",
    "worker_interest_selections.worker_interest_selections_worker_preferences_id_fkey": "FOREIGN KEY "
    "(worker_preferences_id) "
    "REFERENCES "
    "worker_preferences(worker_preferences_id)",
    "worker_preferences.guard_canonical_correction": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "worker_preferences.guard_worker_output": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "worker_preferences.worker_preferences_availability_check": "CHECK (jsonb_typeof(availability) = "
    "'object'::text)",
    "worker_preferences.worker_preferences_availability_check1": "CHECK ((availability ? 'mode'::text "
    "AND ((availability ->> "
    "'mode'::text) = ANY "
    "(ARRAY['flexible'::text, "
    "'weekly'::text]))) IS TRUE)",
    "worker_preferences.worker_preferences_check1": "CHECK (octet_length(interests::text) <= 32768 "
    "AND octet_length(availability::text) <= 32768)",
    "worker_preferences.worker_preferences_interests_check": "CHECK (jsonb_typeof(interests) = "
    "'object'::text)",
    "worker_preferences.worker_preferences_interests_check1": "CHECK (((interests ->> "
    "'other_description'::text) IS NOT NULL "
    "AND btrim(interests ->> "
    "'other_description'::text) <> ''::text "
    "OR jsonb_typeof(interests -> "
    "'selections'::text) = 'array'::text "
    "AND jsonb_array_length(interests -> "
    "'selections'::text) >= 1 AND "
    "jsonb_array_length(interests -> "
    "'selections'::text) <= 20) IS TRUE)",
    "worker_preferences.worker_preferences_pkey": "PRIMARY KEY (worker_preferences_id)",
    "worker_preferences.worker_preferences_self_reported_check": "CHECK (self_reported)",
    "worker_preferences.worker_preferences_version_check": "CHECK (version >= 1)",
    "worker_preferences.worker_preferences_worker_id_fkey": "FOREIGN KEY (worker_id) REFERENCES "
    "workers(worker_id)",
    "worker_preferences.worker_preferences_worker_id_key": "UNIQUE (worker_id)",
    "worker_preferences.worker_preferences_worker_id_worker_preferences_id_key": "UNIQUE (worker_id, "
    "worker_preferences_id)",
    "worker_residences.guard_canonical_correction": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "worker_residences.guard_worker_output": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "worker_residences.worker_residences_check1": "CHECK (country::text <> 'US'::text OR region IS "
    "NOT NULL AND btrim(region::text) <> ''::text AND "
    "postal_code IS NOT NULL AND "
    "btrim(postal_code::text) <> ''::text)",
    "worker_residences.worker_residences_country_check": "CHECK (country::text ~ '^[A-Z]{2}$'::text)",
    "worker_residences.worker_residences_line1_check": "CHECK (btrim(line1::text) <> ''::text)",
    "worker_residences.worker_residences_locality_check": "CHECK (btrim(locality::text) <> ''::text)",
    "worker_residences.worker_residences_pkey": "PRIMARY KEY (worker_residence_id)",
    "worker_residences.worker_residences_version_check": "CHECK (version >= 1)",
    "worker_residences.worker_residences_worker_id_fkey": "FOREIGN KEY (worker_id) REFERENCES "
    "workers(worker_id)",
    "worker_residences.worker_residences_worker_id_key": "UNIQUE (worker_id)",
    "worker_residences.worker_residences_worker_id_worker_residence_id_key": "UNIQUE (worker_id, "
    "worker_residence_id)",
    "workers.guard_canonical_correction": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "workers.guard_worker_output": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "workers.workers_full_name_check": "CHECK (btrim(full_name::text) <> ''::text)",
    "workers.workers_pkey": "PRIMARY KEY (worker_id)",
    "workers.workers_version_check": "CHECK (version >= 1)",
    "worksites.guard_canonical_correction": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "worksites.guard_employer_output": "TRIGGER DEFERRABLE INITIALLY DEFERRED",
    "worksites.worksites_check1": "CHECK (line1 IS NOT NULL AND btrim(line1::text) <> ''::text AND "
    "locality IS NOT NULL AND btrim(locality::text) <> ''::text AND "
    "country IS NOT NULL AND country::text ~ '^[A-Z]{2}$'::text AND "
    "(country::text <> 'US'::text OR region IS NOT NULL AND "
    "btrim(region::text) <> ''::text AND postal_code IS NOT NULL AND "
    "btrim(postal_code::text) <> ''::text))",
    "worksites.worksites_employer_id_fkey": "FOREIGN KEY (employer_id) REFERENCES "
    "employers(employer_id)",
    "worksites.worksites_employer_id_worksite_id_key": "UNIQUE (employer_id, worksite_id)",
    "worksites.worksites_location_verification_status_check": "CHECK "
    "(location_verification_status::text = "
    "'supplied'::text)",
    "worksites.worksites_map_area_status_check": "CHECK (map_area_status::text = 'pending'::text)",
    "worksites.worksites_pkey": "PRIMARY KEY (worksite_id)",
    "worksites.worksites_service_area_status_check": "CHECK (service_area_status::text = "
    "'unassigned'::text)",
    "worksites.worksites_version_check": "CHECK (version >= 1)",
}

EXPECTED_INTAKE_TRIGGERS = {
    "audit_events.audit_events_no_delete": ("deny_mutation_on_append_only_tables", False),
    "audit_events.audit_events_no_update": ("deny_mutation_on_append_only_tables", False),
    "audit_events.guard_intake_link_event": ("guard_intake_link_event", True),
    "audit_events.guard_intake_workflow_authority": ("guard_intake_workflow_authority", True),
    "audit_events.guard_work_interest_authority": ("guard_work_interest_authority", True),
    "canonical_correction_payloads.deny_mutation_canonical_correction_payloads": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "canonical_correction_payloads.guard_correction_evidence": ("guard_correction_evidence", True),
    "canonical_corrections.deny_mutation_canonical_corrections": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "canonical_corrections.guard_correction_evidence": ("guard_correction_evidence", True),
    "canonical_output_review_payloads.deny_mutation_canonical_output_review_payloads": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "canonical_output_review_payloads.guard_canonical_review": ("guard_canonical_review", True),
    "canonical_output_reviews.deny_mutation_canonical_output_reviews": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "canonical_output_reviews.guard_canonical_review": ("guard_canonical_review", True),
    "canonical_review_heads.deny_mutation_canonical_review_heads": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "canonical_review_heads.guard_canonical_review": ("guard_canonical_review", True),
    "canonical_review_heads.guard_canonical_review_identity": (
        "guard_canonical_review_identity",
        False,
    ),
    "command_receipts.command_receipts_no_delete": ("deny_mutation_on_append_only_tables", False),
    "command_receipts.command_receipts_no_update": ("deny_mutation_on_append_only_tables", False),
    "command_receipts.command_receipts_revision_compatibility_defaults": (
        "populate_command_receipt_revision_compatibility_fields",
        False,
    ),
    "command_receipts.guard_canonical_review": ("guard_canonical_review", True),
    "command_receipts.guard_correction_evidence": ("guard_correction_evidence", True),
    "command_receipts.guard_finalization_results": ("guard_finalization_results", True),
    "command_receipts.populate_legacy_command_result": ("populate_legacy_command_result", False),
    "command_results.deny_mutation_command_results": ("deny_mutation_on_append_only_tables", False),
    "command_results.guard_finalization_results": ("guard_finalization_results", True),
    "employer_addresses.deny_mutation_employer_addresses": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "employer_addresses.guard_canonical_correction": ("guard_canonical_correction", True),
    "employer_addresses.guard_canonical_identity": ("guard_canonical_identity", False),
    "employer_addresses.guard_employer_output": ("guard_employer_output", True),
    "employer_contact_details.deny_mutation_employer_contact_details": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "employer_contact_details.guard_canonical_correction": ("guard_canonical_correction", True),
    "employer_contact_details.guard_canonical_identity": ("guard_canonical_identity", False),
    "employer_contact_details.guard_employer_output": ("guard_employer_output", True),
    "employer_contacts.guard_employer_output": ("guard_employer_output", True),
    "employers.employers_revision_compatibility_defaults": (
        "populate_employer_revision_compatibility_fields",
        False,
    ),
    "employers.guard_employer_output": ("guard_employer_output", True),
    "intake_addresses.deny_mutation_intake_addresses": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "intake_addresses.guard_intake_address_authority": ("guard_intake_address_authority", True),
    "intake_addresses.guard_intake_address_identity": ("guard_intake_identity", False),
    "intake_finalizations.deny_mutation_intake_finalizations": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "intake_finalizations.guard_finalization_results": ("guard_finalization_results", True),
    "intake_follow_up_events.deny_mutation_intake_follow_up_events": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "intake_follow_up_events.guard_intake_workflow_authority": (
        "guard_intake_workflow_authority",
        True,
    ),
    "intake_history_payloads.deny_mutation_intake_history_payloads": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "intake_history_payloads.guard_intake_workflow_authority": (
        "guard_intake_workflow_authority",
        True,
    ),
    "intake_links.deny_mutation_intake_links": ("deny_mutation_on_append_only_tables", False),
    "intake_links.guard_intake_link_once": ("guard_intake_link_once", False),
    "intake_links.guard_intake_links": ("guard_intake_links", True),
    "intake_review_payloads.deny_mutation_intake_review_payloads": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "intake_review_payloads.guard_intake_workflow_authority": (
        "guard_intake_workflow_authority",
        True,
    ),
    "intake_reviews.deny_mutation_intake_reviews": ("deny_mutation_on_append_only_tables", False),
    "intake_reviews.guard_intake_workflow_authority": ("guard_intake_workflow_authority", True),
    "intakes.deny_mutation_intakes": ("deny_mutation_on_append_only_tables", False),
    "intakes.guard_intake_identity": ("guard_intake_identity", False),
    "intakes.guard_intake_links": ("guard_intake_links", True),
    "intakes.guard_intake_write_authority": ("guard_intake_write_authority", True),
    "staffing_requests.deny_mutation_staffing_requests": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "staffing_requests.guard_canonical_correction": ("guard_canonical_correction", True),
    "staffing_requests.guard_canonical_identity": ("guard_canonical_identity", False),
    "staffing_requests.guard_employer_output": ("guard_employer_output", True),
    "work_interest_versions.deny_mutation_work_interest_versions": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "work_interest_versions.guard_work_interest_authority": ("guard_work_interest_authority", True),
    "work_interests.deny_mutation_work_interests": ("deny_mutation_on_append_only_tables", False),
    "work_interests.guard_work_interest_authority": ("guard_work_interest_authority", True),
    "work_interests.guard_work_interest_identity": ("guard_work_interest_identity", False),
    "worker_contacts.deny_mutation_worker_contacts": ("deny_mutation_on_append_only_tables", False),
    "worker_contacts.guard_canonical_correction": ("guard_canonical_correction", True),
    "worker_contacts.guard_canonical_identity": ("guard_canonical_identity", False),
    "worker_contacts.guard_worker_output": ("guard_worker_output", True),
    "worker_interest_selections.deny_mutation_worker_interest_selections": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "worker_interest_selections.guard_worker_selection": ("guard_worker_selection", True),
    "worker_preferences.deny_mutation_worker_preferences": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "worker_preferences.guard_canonical_correction": ("guard_canonical_correction", True),
    "worker_preferences.guard_canonical_identity": ("guard_canonical_identity", False),
    "worker_preferences.guard_worker_output": ("guard_worker_output", True),
    "worker_residences.deny_mutation_worker_residences": (
        "deny_mutation_on_append_only_tables",
        False,
    ),
    "worker_residences.guard_canonical_correction": ("guard_canonical_correction", True),
    "worker_residences.guard_canonical_identity": ("guard_canonical_identity", False),
    "worker_residences.guard_worker_output": ("guard_worker_output", True),
    "workers.deny_mutation_workers": ("deny_mutation_on_append_only_tables", False),
    "workers.guard_canonical_correction": ("guard_canonical_correction", True),
    "workers.guard_canonical_identity": ("guard_canonical_identity", False),
    "workers.guard_worker_output": ("guard_worker_output", True),
    "worksites.deny_mutation_worksites": ("deny_mutation_on_append_only_tables", False),
    "worksites.guard_canonical_correction": ("guard_canonical_correction", True),
    "worksites.guard_canonical_identity": ("guard_canonical_identity", False),
    "worksites.guard_employer_output": ("guard_employer_output", True),
}

EXPECTED_FUNCTION_HASHES = {
    "canonical_correction_section(text, jsonb)": "979959c10181080d46247451413bfac49ccd6e99346902fbff3bfe784e7bc31e",
    "canonical_current_facts(uuid)": "ceaac29b900a833a456a640342236c65f8dcd548c1ffb7f52a21a5378825bca8",
    "canonical_details_complete(text, jsonb)": "8bc001e1f5274d3eaef5bbd94ff4ace6db4273e087417cb034f712b20beccb3a",
    "deny_mutation_on_append_only_tables()": "9fcd9dd2284343c0077c314e8b8749be31a66413591df02ea9487fdb3c9732ba",
    "guard_canonical_correction()": "7832b059628865d42bd3acc0b2a2b97d29530087ef2f554da1b3e4cb625c2b88",
    "guard_canonical_identity()": "b392b9406a029abf618a1a1dec104068862f329a6d0bab06fdebc8946a1aabec",
    "guard_canonical_review()": "368b981d3edd1d14d5f5637bfa0a4bff4ce9703d87c9a0308f6ec0439ec6618e",
    "guard_canonical_review_identity()": "c5e2e5278346fc2d0123c0a1b7bf3a5d5e2ef63984439dad768fd098589897f6",
    "guard_correction_evidence()": "2f234a59e00db11c15355c84ff8da43b7cbdde75c9f468940efc7dc379718ac1",
    "guard_employer_output()": "7a7cf9b344a37250e28029a07a9129486ebe0f53407a665c21467d4b88f2b6f3",
    "guard_finalization_results()": "9d47698402a27977b18499a0dc97e953488c4b89db87fec3a62b598e43169375",
    "guard_intake_address_authority()": "47e030480919160c7a63fb7d159c0adec69e497ffb36bf04b4fdb840fa73a9c0",
    "guard_intake_identity()": "0fd1221d4d55acaca292163c903191776acc530528a088f086b9670da95410c6",
    "guard_intake_link_event()": "74ccc0538d9d4ef762cbc181c440e2679ddb466e6373c8d87c380b160c786011",
    "guard_intake_link_once()": "aee89d395953850380c017a082baf657d724c9e92137dbeac44c907294427284",
    "guard_intake_links()": "37816690ee3ba88ae514352767aa964714bb81102f4298cbe92e222335440466",
    "guard_intake_workflow_authority()": "cbcba7fceba6b749ba3974c91430713c57c90147310ce9b05d6fa10f178a6a35",
    "guard_intake_write_authority()": "26f547b0c18f3db97ed3a4e43a4a271857ae8602cb7600972953c8a46394bf0f",
    "guard_work_interest_authority()": "de664918f8177bcc7213334c97d99743e159ac24e85a36f0438b4ae56b35c355",
    "guard_work_interest_identity()": "649cfbb47d70d1b22a944219996dfce183dfd5e1643186b378d1cc4a64357590",
    "guard_worker_output()": "3d025f918dc182d9dd84c8962de75ca452dc2e695154e5d99326eac203881edc",
    "guard_worker_selection()": "33a379e2d9676e1e4c52582596b832efb70965b0118b1f9e8bbb2f86195ee86a",
    "intake_canonical_record(text, uuid)": "d9f5b2bc60e835ec63dc0f4fe120770de49c273e0696693db120c366f7b1934d",
    "intake_effective_snapshot(uuid)": "8fb41ff7e57951108b8bd6928e9e698355ea116962774246458754e6e76102ef",
    "intake_link_refs(uuid)": "d27438e2ee115ba40ebd46c2abcbed31755c99f6e6bca5bacc28f3c9961475c0",
    "populate_command_receipt_revision_compatibility_fields()": "7a6e9a3a156344ecc76103331d2e6c7844edb9a8f8600ebb415ae4b547adbded",
    "populate_employer_revision_compatibility_fields()": "b0b862c8bb628e3f487c7e16702041299e8ba4bd9d0a32d23e276e56a1635e95",
    "populate_legacy_command_result()": "b457a7d46f8eb29006f720592dafdd5c85cd9150071634f69f37833cc0d3337d",
}

EXPECTED_TRIGGER_DEFINITIONS = {
    "audit_events.audit_events_no_delete": "CREATE TRIGGER audit_events_no_delete BEFORE DELETE ON "
    "audit_events FOR EACH ROW EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "audit_events.audit_events_no_update": "CREATE TRIGGER audit_events_no_update BEFORE UPDATE ON "
    "audit_events FOR EACH ROW EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "audit_events.guard_intake_link_event": "CREATE CONSTRAINT TRIGGER guard_intake_link_event AFTER "
    "INSERT ON audit_events DEFERRABLE INITIALLY DEFERRED FOR "
    "EACH ROW EXECUTE FUNCTION guard_intake_link_event()",
    "audit_events.guard_intake_workflow_authority": "CREATE CONSTRAINT TRIGGER "
    "guard_intake_workflow_authority AFTER INSERT ON "
    "audit_events DEFERRABLE INITIALLY DEFERRED FOR "
    "EACH ROW EXECUTE FUNCTION "
    "guard_intake_workflow_authority()",
    "audit_events.guard_work_interest_authority": "CREATE CONSTRAINT TRIGGER "
    "guard_work_interest_authority AFTER INSERT ON "
    "audit_events DEFERRABLE INITIALLY DEFERRED FOR "
    "EACH ROW EXECUTE FUNCTION "
    "guard_work_interest_authority()",
    "canonical_correction_payloads.deny_mutation_canonical_correction_payloads": "CREATE TRIGGER "
    "deny_mutation_canonical_correction_payloads "
    "BEFORE DELETE OR "
    "UPDATE OR TRUNCATE "
    "ON "
    "canonical_correction_payloads "
    "FOR EACH STATEMENT "
    "EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "canonical_correction_payloads.guard_correction_evidence": "CREATE CONSTRAINT TRIGGER "
    "guard_correction_evidence AFTER "
    "INSERT ON "
    "canonical_correction_payloads "
    "DEFERRABLE INITIALLY DEFERRED FOR "
    "EACH ROW EXECUTE FUNCTION "
    "guard_correction_evidence()",
    "canonical_corrections.deny_mutation_canonical_corrections": "CREATE TRIGGER "
    "deny_mutation_canonical_corrections "
    "BEFORE DELETE OR UPDATE OR TRUNCATE "
    "ON canonical_corrections FOR EACH "
    "STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "canonical_corrections.guard_correction_evidence": "CREATE CONSTRAINT TRIGGER "
    "guard_correction_evidence AFTER INSERT ON "
    "canonical_corrections DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_correction_evidence()",
    "canonical_output_review_payloads.deny_mutation_canonical_output_review_payloads": "CREATE "
    "TRIGGER "
    "deny_mutation_canonical_output_review_payloads "
    "BEFORE DELETE "
    "OR UPDATE OR "
    "TRUNCATE ON "
    "canonical_output_review_payloads "
    "FOR EACH "
    "STATEMENT "
    "EXECUTE "
    "FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "canonical_output_review_payloads.guard_canonical_review": "CREATE CONSTRAINT TRIGGER "
    "guard_canonical_review AFTER INSERT "
    "ON canonical_output_review_payloads "
    "DEFERRABLE INITIALLY DEFERRED FOR "
    "EACH ROW EXECUTE FUNCTION "
    "guard_canonical_review()",
    "canonical_output_reviews.deny_mutation_canonical_output_reviews": "CREATE TRIGGER "
    "deny_mutation_canonical_output_reviews "
    "BEFORE DELETE OR UPDATE OR "
    "TRUNCATE ON "
    "canonical_output_reviews FOR "
    "EACH STATEMENT EXECUTE "
    "FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "canonical_output_reviews.guard_canonical_review": "CREATE CONSTRAINT TRIGGER "
    "guard_canonical_review AFTER INSERT ON "
    "canonical_output_reviews DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_canonical_review()",
    "canonical_review_heads.deny_mutation_canonical_review_heads": "CREATE TRIGGER "
    "deny_mutation_canonical_review_heads "
    "BEFORE DELETE OR TRUNCATE ON "
    "canonical_review_heads FOR EACH "
    "STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "canonical_review_heads.guard_canonical_review": "CREATE CONSTRAINT TRIGGER "
    "guard_canonical_review AFTER UPDATE ON "
    "canonical_review_heads DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_canonical_review()",
    "canonical_review_heads.guard_canonical_review_identity": "CREATE TRIGGER "
    "guard_canonical_review_identity BEFORE "
    "INSERT OR UPDATE ON "
    "canonical_review_heads FOR EACH ROW "
    "EXECUTE FUNCTION "
    "guard_canonical_review_identity()",
    "command_receipts.command_receipts_no_delete": "CREATE TRIGGER command_receipts_no_delete BEFORE "
    "DELETE ON command_receipts FOR EACH ROW EXECUTE "
    "FUNCTION deny_mutation_on_append_only_tables()",
    "command_receipts.command_receipts_no_update": "CREATE TRIGGER command_receipts_no_update BEFORE "
    "UPDATE ON command_receipts FOR EACH ROW EXECUTE "
    "FUNCTION deny_mutation_on_append_only_tables()",
    "command_receipts.command_receipts_revision_compatibility_defaults": "CREATE TRIGGER "
    "command_receipts_revision_compatibility_defaults "
    "BEFORE INSERT ON "
    "command_receipts FOR EACH "
    "ROW EXECUTE FUNCTION "
    "populate_command_receipt_revision_compatibility_fields()",
    "command_receipts.guard_canonical_review": "CREATE CONSTRAINT TRIGGER guard_canonical_review "
    "AFTER INSERT ON command_receipts DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_canonical_review()",
    "command_receipts.guard_correction_evidence": "CREATE CONSTRAINT TRIGGER "
    "guard_correction_evidence AFTER INSERT ON "
    "command_receipts DEFERRABLE INITIALLY DEFERRED FOR "
    "EACH ROW EXECUTE FUNCTION "
    "guard_correction_evidence()",
    "command_receipts.guard_finalization_results": "CREATE CONSTRAINT TRIGGER "
    "guard_finalization_results AFTER INSERT ON "
    "command_receipts DEFERRABLE INITIALLY DEFERRED "
    "FOR EACH ROW EXECUTE FUNCTION "
    "guard_finalization_results()",
    "command_receipts.populate_legacy_command_result": "CREATE TRIGGER populate_legacy_command_result "
    "AFTER INSERT ON command_receipts FOR EACH ROW "
    "EXECUTE FUNCTION "
    "populate_legacy_command_result()",
    "command_results.deny_mutation_command_results": "CREATE TRIGGER deny_mutation_command_results "
    "BEFORE DELETE OR UPDATE OR TRUNCATE ON "
    "command_results FOR EACH STATEMENT EXECUTE "
    "FUNCTION deny_mutation_on_append_only_tables()",
    "command_results.guard_finalization_results": "CREATE CONSTRAINT TRIGGER "
    "guard_finalization_results AFTER INSERT ON "
    "command_results DEFERRABLE INITIALLY DEFERRED FOR "
    "EACH ROW EXECUTE FUNCTION "
    "guard_finalization_results()",
    "employer_addresses.deny_mutation_employer_addresses": "CREATE TRIGGER "
    "deny_mutation_employer_addresses BEFORE "
    "DELETE OR TRUNCATE ON employer_addresses "
    "FOR EACH STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "employer_addresses.guard_canonical_correction": "CREATE CONSTRAINT TRIGGER "
    "guard_canonical_correction AFTER UPDATE ON "
    "employer_addresses DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_canonical_correction('employer_address')",
    "employer_addresses.guard_canonical_identity": "CREATE TRIGGER guard_canonical_identity BEFORE "
    "INSERT OR UPDATE ON employer_addresses FOR EACH "
    "ROW EXECUTE FUNCTION "
    "guard_canonical_identity('employer_address')",
    "employer_addresses.guard_employer_output": "CREATE CONSTRAINT TRIGGER guard_employer_output "
    "AFTER INSERT ON employer_addresses DEFERRABLE "
    "INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_employer_output('employer_address')",
    "employer_contact_details.deny_mutation_employer_contact_details": "CREATE TRIGGER "
    "deny_mutation_employer_contact_details "
    "BEFORE DELETE OR TRUNCATE ON "
    "employer_contact_details FOR "
    "EACH STATEMENT EXECUTE "
    "FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "employer_contact_details.guard_canonical_correction": "CREATE CONSTRAINT TRIGGER "
    "guard_canonical_correction AFTER UPDATE "
    "ON employer_contact_details DEFERRABLE "
    "INITIALLY DEFERRED FOR EACH ROW EXECUTE "
    "FUNCTION "
    "guard_canonical_correction('employer_contact_details')",
    "employer_contact_details.guard_canonical_identity": "CREATE TRIGGER guard_canonical_identity "
    "BEFORE INSERT OR UPDATE ON "
    "employer_contact_details FOR EACH ROW "
    "EXECUTE FUNCTION "
    "guard_canonical_identity('employer_contact_details')",
    "employer_contact_details.guard_employer_output": "CREATE CONSTRAINT TRIGGER "
    "guard_employer_output AFTER INSERT ON "
    "employer_contact_details DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_employer_output('employer_contact_details')",
    "employer_contacts.guard_employer_output": "CREATE CONSTRAINT TRIGGER guard_employer_output AFTER "
    "INSERT ON employer_contacts DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_employer_output('employer_contact')",
    "employers.employers_revision_compatibility_defaults": "CREATE TRIGGER "
    "employers_revision_compatibility_defaults "
    "BEFORE INSERT ON employers FOR EACH ROW "
    "EXECUTE FUNCTION "
    "populate_employer_revision_compatibility_fields()",
    "employers.guard_employer_output": "CREATE CONSTRAINT TRIGGER guard_employer_output AFTER INSERT "
    "ON employers DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
    "EXECUTE FUNCTION guard_employer_output('employer')",
    "intake_addresses.deny_mutation_intake_addresses": "CREATE TRIGGER deny_mutation_intake_addresses "
    "BEFORE DELETE OR TRUNCATE ON intake_addresses "
    "FOR EACH STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "intake_addresses.guard_intake_address_authority": "CREATE CONSTRAINT TRIGGER "
    "guard_intake_address_authority AFTER INSERT "
    "OR UPDATE ON intake_addresses DEFERRABLE "
    "INITIALLY DEFERRED FOR EACH ROW EXECUTE "
    "FUNCTION guard_intake_address_authority()",
    "intake_addresses.guard_intake_address_identity": "CREATE TRIGGER guard_intake_address_identity "
    "BEFORE UPDATE ON intake_addresses FOR EACH ROW "
    "EXECUTE FUNCTION guard_intake_identity()",
    "intake_finalizations.deny_mutation_intake_finalizations": "CREATE TRIGGER "
    "deny_mutation_intake_finalizations "
    "BEFORE DELETE OR UPDATE OR TRUNCATE "
    "ON intake_finalizations FOR EACH "
    "STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "intake_finalizations.guard_finalization_results": "CREATE CONSTRAINT TRIGGER "
    "guard_finalization_results AFTER INSERT ON "
    "intake_finalizations DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_finalization_results()",
    "intake_follow_up_events.deny_mutation_intake_follow_up_events": "CREATE TRIGGER "
    "deny_mutation_intake_follow_up_events "
    "BEFORE DELETE OR UPDATE OR "
    "TRUNCATE ON "
    "intake_follow_up_events FOR "
    "EACH STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "intake_follow_up_events.guard_intake_workflow_authority": "CREATE CONSTRAINT TRIGGER "
    "guard_intake_workflow_authority AFTER "
    "INSERT ON intake_follow_up_events "
    "DEFERRABLE INITIALLY DEFERRED FOR "
    "EACH ROW EXECUTE FUNCTION "
    "guard_intake_workflow_authority()",
    "intake_history_payloads.deny_mutation_intake_history_payloads": "CREATE TRIGGER "
    "deny_mutation_intake_history_payloads "
    "BEFORE DELETE OR UPDATE OR "
    "TRUNCATE ON "
    "intake_history_payloads FOR "
    "EACH STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "intake_history_payloads.guard_intake_workflow_authority": "CREATE CONSTRAINT TRIGGER "
    "guard_intake_workflow_authority AFTER "
    "INSERT ON intake_history_payloads "
    "DEFERRABLE INITIALLY DEFERRED FOR "
    "EACH ROW EXECUTE FUNCTION "
    "guard_intake_workflow_authority()",
    "intake_links.deny_mutation_intake_links": "CREATE TRIGGER deny_mutation_intake_links BEFORE "
    "DELETE OR TRUNCATE ON intake_links FOR EACH STATEMENT "
    "EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "intake_links.guard_intake_link_once": "CREATE TRIGGER guard_intake_link_once BEFORE UPDATE ON "
    "intake_links FOR EACH ROW EXECUTE FUNCTION "
    "guard_intake_link_once()",
    "intake_links.guard_intake_links": "CREATE CONSTRAINT TRIGGER guard_intake_links AFTER INSERT OR "
    "UPDATE ON intake_links DEFERRABLE INITIALLY DEFERRED FOR EACH "
    "ROW EXECUTE FUNCTION guard_intake_links()",
    "intake_review_payloads.deny_mutation_intake_review_payloads": "CREATE TRIGGER "
    "deny_mutation_intake_review_payloads "
    "BEFORE DELETE OR UPDATE OR "
    "TRUNCATE ON "
    "intake_review_payloads FOR EACH "
    "STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "intake_review_payloads.guard_intake_workflow_authority": "CREATE CONSTRAINT TRIGGER "
    "guard_intake_workflow_authority AFTER "
    "INSERT ON intake_review_payloads "
    "DEFERRABLE INITIALLY DEFERRED FOR EACH "
    "ROW EXECUTE FUNCTION "
    "guard_intake_workflow_authority()",
    "intake_reviews.deny_mutation_intake_reviews": "CREATE TRIGGER deny_mutation_intake_reviews "
    "BEFORE DELETE OR UPDATE OR TRUNCATE ON "
    "intake_reviews FOR EACH STATEMENT EXECUTE "
    "FUNCTION deny_mutation_on_append_only_tables()",
    "intake_reviews.guard_intake_workflow_authority": "CREATE CONSTRAINT TRIGGER "
    "guard_intake_workflow_authority AFTER INSERT "
    "ON intake_reviews DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_intake_workflow_authority()",
    "intakes.deny_mutation_intakes": "CREATE TRIGGER deny_mutation_intakes BEFORE DELETE OR TRUNCATE "
    "ON intakes FOR EACH STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "intakes.guard_intake_identity": "CREATE TRIGGER guard_intake_identity BEFORE INSERT OR UPDATE ON "
    "intakes FOR EACH ROW EXECUTE FUNCTION guard_intake_identity()",
    "intakes.guard_intake_links": "CREATE CONSTRAINT TRIGGER guard_intake_links AFTER INSERT OR "
    "UPDATE ON intakes DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
    "EXECUTE FUNCTION guard_intake_links()",
    "intakes.guard_intake_write_authority": "CREATE CONSTRAINT TRIGGER guard_intake_write_authority "
    "AFTER INSERT OR UPDATE ON intakes DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_intake_write_authority()",
    "staffing_requests.deny_mutation_staffing_requests": "CREATE TRIGGER "
    "deny_mutation_staffing_requests BEFORE "
    "DELETE OR TRUNCATE ON staffing_requests FOR "
    "EACH STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "staffing_requests.guard_canonical_correction": "CREATE CONSTRAINT TRIGGER "
    "guard_canonical_correction AFTER UPDATE ON "
    "staffing_requests DEFERRABLE INITIALLY DEFERRED "
    "FOR EACH ROW EXECUTE FUNCTION "
    "guard_canonical_correction('staffing_request')",
    "staffing_requests.guard_canonical_identity": "CREATE TRIGGER guard_canonical_identity BEFORE "
    "INSERT OR UPDATE ON staffing_requests FOR EACH ROW "
    "EXECUTE FUNCTION "
    "guard_canonical_identity('staffing_request')",
    "staffing_requests.guard_employer_output": "CREATE CONSTRAINT TRIGGER guard_employer_output AFTER "
    "INSERT ON staffing_requests DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_employer_output('staffing_request')",
    "work_interest_versions.deny_mutation_work_interest_versions": "CREATE TRIGGER "
    "deny_mutation_work_interest_versions "
    "BEFORE DELETE OR UPDATE OR "
    "TRUNCATE ON "
    "work_interest_versions FOR EACH "
    "STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "work_interest_versions.guard_work_interest_authority": "CREATE CONSTRAINT TRIGGER "
    "guard_work_interest_authority AFTER "
    "INSERT ON work_interest_versions "
    "DEFERRABLE INITIALLY DEFERRED FOR EACH "
    "ROW EXECUTE FUNCTION "
    "guard_work_interest_authority()",
    "work_interests.deny_mutation_work_interests": "CREATE TRIGGER deny_mutation_work_interests "
    "BEFORE DELETE OR TRUNCATE ON work_interests FOR "
    "EACH STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "work_interests.guard_work_interest_authority": "CREATE CONSTRAINT TRIGGER "
    "guard_work_interest_authority AFTER INSERT OR "
    "UPDATE ON work_interests DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_work_interest_authority()",
    "work_interests.guard_work_interest_identity": "CREATE TRIGGER guard_work_interest_identity "
    "BEFORE INSERT OR UPDATE ON work_interests FOR "
    "EACH ROW EXECUTE FUNCTION "
    "guard_work_interest_identity()",
    "worker_contacts.deny_mutation_worker_contacts": "CREATE TRIGGER deny_mutation_worker_contacts "
    "BEFORE DELETE OR TRUNCATE ON worker_contacts "
    "FOR EACH STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "worker_contacts.guard_canonical_correction": "CREATE CONSTRAINT TRIGGER "
    "guard_canonical_correction AFTER UPDATE ON "
    "worker_contacts DEFERRABLE INITIALLY DEFERRED FOR "
    "EACH ROW EXECUTE FUNCTION "
    "guard_canonical_correction('worker_contact')",
    "worker_contacts.guard_canonical_identity": "CREATE TRIGGER guard_canonical_identity BEFORE "
    "INSERT OR UPDATE ON worker_contacts FOR EACH ROW "
    "EXECUTE FUNCTION "
    "guard_canonical_identity('worker_contact')",
    "worker_contacts.guard_worker_output": "CREATE CONSTRAINT TRIGGER guard_worker_output AFTER "
    "INSERT ON worker_contacts DEFERRABLE INITIALLY DEFERRED "
    "FOR EACH ROW EXECUTE FUNCTION "
    "guard_worker_output('worker_contact')",
    "worker_interest_selections.deny_mutation_worker_interest_selections": "CREATE TRIGGER "
    "deny_mutation_worker_interest_selections "
    "BEFORE UPDATE OR TRUNCATE "
    "ON "
    "worker_interest_selections "
    "FOR EACH STATEMENT "
    "EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "worker_interest_selections.guard_worker_selection": "CREATE CONSTRAINT TRIGGER "
    "guard_worker_selection AFTER INSERT OR "
    "DELETE ON worker_interest_selections "
    "DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
    "EXECUTE FUNCTION guard_worker_selection()",
    "worker_preferences.deny_mutation_worker_preferences": "CREATE TRIGGER "
    "deny_mutation_worker_preferences BEFORE "
    "DELETE OR TRUNCATE ON worker_preferences "
    "FOR EACH STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "worker_preferences.guard_canonical_correction": "CREATE CONSTRAINT TRIGGER "
    "guard_canonical_correction AFTER UPDATE ON "
    "worker_preferences DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_canonical_correction('worker_preferences')",
    "worker_preferences.guard_canonical_identity": "CREATE TRIGGER guard_canonical_identity BEFORE "
    "INSERT OR UPDATE ON worker_preferences FOR EACH "
    "ROW EXECUTE FUNCTION "
    "guard_canonical_identity('worker_preferences')",
    "worker_preferences.guard_worker_output": "CREATE CONSTRAINT TRIGGER guard_worker_output AFTER "
    "INSERT ON worker_preferences DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_worker_output('worker_preferences')",
    "worker_residences.deny_mutation_worker_residences": "CREATE TRIGGER "
    "deny_mutation_worker_residences BEFORE "
    "DELETE OR TRUNCATE ON worker_residences FOR "
    "EACH STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "worker_residences.guard_canonical_correction": "CREATE CONSTRAINT TRIGGER "
    "guard_canonical_correction AFTER UPDATE ON "
    "worker_residences DEFERRABLE INITIALLY DEFERRED "
    "FOR EACH ROW EXECUTE FUNCTION "
    "guard_canonical_correction('worker_residence')",
    "worker_residences.guard_canonical_identity": "CREATE TRIGGER guard_canonical_identity BEFORE "
    "INSERT OR UPDATE ON worker_residences FOR EACH ROW "
    "EXECUTE FUNCTION "
    "guard_canonical_identity('worker_residence')",
    "worker_residences.guard_worker_output": "CREATE CONSTRAINT TRIGGER guard_worker_output AFTER "
    "INSERT ON worker_residences DEFERRABLE INITIALLY "
    "DEFERRED FOR EACH ROW EXECUTE FUNCTION "
    "guard_worker_output('worker_residence')",
    "workers.deny_mutation_workers": "CREATE TRIGGER deny_mutation_workers BEFORE DELETE OR TRUNCATE "
    "ON workers FOR EACH STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "workers.guard_canonical_correction": "CREATE CONSTRAINT TRIGGER guard_canonical_correction AFTER "
    "UPDATE ON workers DEFERRABLE INITIALLY DEFERRED FOR EACH "
    "ROW EXECUTE FUNCTION guard_canonical_correction('worker')",
    "workers.guard_canonical_identity": "CREATE TRIGGER guard_canonical_identity BEFORE INSERT OR "
    "UPDATE ON workers FOR EACH ROW EXECUTE FUNCTION "
    "guard_canonical_identity('worker')",
    "workers.guard_worker_output": "CREATE CONSTRAINT TRIGGER guard_worker_output AFTER INSERT ON "
    "workers DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE "
    "FUNCTION guard_worker_output('worker')",
    "worksites.deny_mutation_worksites": "CREATE TRIGGER deny_mutation_worksites BEFORE DELETE OR "
    "TRUNCATE ON worksites FOR EACH STATEMENT EXECUTE FUNCTION "
    "deny_mutation_on_append_only_tables()",
    "worksites.guard_canonical_correction": "CREATE CONSTRAINT TRIGGER guard_canonical_correction "
    "AFTER UPDATE ON worksites DEFERRABLE INITIALLY DEFERRED "
    "FOR EACH ROW EXECUTE FUNCTION "
    "guard_canonical_correction('worksite')",
    "worksites.guard_canonical_identity": "CREATE TRIGGER guard_canonical_identity BEFORE INSERT OR "
    "UPDATE ON worksites FOR EACH ROW EXECUTE FUNCTION "
    "guard_canonical_identity('worksite')",
    "worksites.guard_employer_output": "CREATE CONSTRAINT TRIGGER guard_employer_output AFTER INSERT "
    "ON worksites DEFERRABLE INITIALLY DEFERRED FOR EACH ROW "
    "EXECUTE FUNCTION guard_employer_output('worksite')",
}

EXPECTED_UNIQUE_INDEXES = {
    "alembic_version_pkc": "CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING "
    "btree (version_num)",
    "audit_events_pkey": "CREATE UNIQUE INDEX audit_events_pkey ON public.audit_events USING btree "
    "(audit_event_id)",
    "canonical_correction_payloads_pkey": "CREATE UNIQUE INDEX canonical_correction_payloads_pkey ON "
    "public.canonical_correction_payloads USING btree "
    "(event_id)",
    "canonical_corrections_command_id_key": "CREATE UNIQUE INDEX canonical_corrections_command_id_key "
    "ON public.canonical_corrections USING btree (command_id)",
    "canonical_corrections_entity_type_entity_id_result_version_key": "CREATE UNIQUE INDEX "
    "canonical_corrections_entity_type_entity_id_result_version_key "
    "ON "
    "public.canonical_corrections "
    "USING btree (entity_type, "
    "entity_id, result_version)",
    "canonical_corrections_event_id_entity_type_entity_id_key": "CREATE UNIQUE INDEX "
    "canonical_corrections_event_id_entity_type_entity_id_key "
    "ON public.canonical_corrections "
    "USING btree (event_id, entity_type, "
    "entity_id)",
    "canonical_corrections_pkey": "CREATE UNIQUE INDEX canonical_corrections_pkey ON "
    "public.canonical_corrections USING btree (event_id)",
    "canonical_output_review_payloads_pkey": "CREATE UNIQUE INDEX "
    "canonical_output_review_payloads_pkey ON "
    "public.canonical_output_review_payloads USING btree "
    "(review_id)",
    "canonical_output_reviews_command_id_key": "CREATE UNIQUE INDEX "
    "canonical_output_reviews_command_id_key ON "
    "public.canonical_output_reviews USING btree "
    "(command_id)",
    "canonical_output_reviews_event_id_key": "CREATE UNIQUE INDEX "
    "canonical_output_reviews_event_id_key ON "
    "public.canonical_output_reviews USING btree (event_id)",
    "canonical_output_reviews_intake_id_result_version_key": "CREATE UNIQUE INDEX "
    "canonical_output_reviews_intake_id_result_version_key "
    "ON public.canonical_output_reviews "
    "USING btree (intake_id, result_version)",
    "canonical_output_reviews_intake_id_review_id_key": "CREATE UNIQUE INDEX "
    "canonical_output_reviews_intake_id_review_id_key "
    "ON public.canonical_output_reviews USING "
    "btree (intake_id, review_id)",
    "canonical_output_reviews_pkey": "CREATE UNIQUE INDEX canonical_output_reviews_pkey ON "
    "public.canonical_output_reviews USING btree (review_id)",
    "canonical_review_heads_intake_id_key": "CREATE UNIQUE INDEX canonical_review_heads_intake_id_key "
    "ON public.canonical_review_heads USING btree (intake_id)",
    "canonical_review_heads_pkey": "CREATE UNIQUE INDEX canonical_review_heads_pkey ON "
    "public.canonical_review_heads USING btree "
    "(canonical_output_review_id)",
    "command_receipts_pkey": "CREATE UNIQUE INDEX command_receipts_pkey ON public.command_receipts "
    "USING btree (command_id)",
    "command_results_pkey": "CREATE UNIQUE INDEX command_results_pkey ON public.command_results USING "
    "btree (command_id, entity_type, entity_id)",
    "employer_addresses_employer_id_employer_address_id_key": "CREATE UNIQUE INDEX "
    "employer_addresses_employer_id_employer_address_id_key "
    "ON public.employer_addresses USING "
    "btree (employer_id, "
    "employer_address_id)",
    "employer_addresses_pkey": "CREATE UNIQUE INDEX employer_addresses_pkey ON "
    "public.employer_addresses USING btree (employer_address_id)",
    "employer_contact_details_employer_contact_id_key": "CREATE UNIQUE INDEX "
    "employer_contact_details_employer_contact_id_key "
    "ON public.employer_contact_details USING "
    "btree (employer_contact_id)",
    "employer_contact_details_employer_id_employer_contact_detai_key": "CREATE UNIQUE INDEX "
    "employer_contact_details_employer_id_employer_contact_detai_key "
    "ON "
    "public.employer_contact_details "
    "USING btree (employer_id, "
    "employer_contact_details_id)",
    "employer_contact_details_pkey": "CREATE UNIQUE INDEX employer_contact_details_pkey ON "
    "public.employer_contact_details USING btree "
    "(employer_contact_details_id)",
    "employer_contacts_pkey": "CREATE UNIQUE INDEX employer_contacts_pkey ON public.employer_contacts "
    "USING btree (employer_contact_id)",
    "employers_pkey": "CREATE UNIQUE INDEX employers_pkey ON public.employers USING btree "
    "(employer_id)",
    "entity_authorities_canonical_output_review_id_key": "CREATE UNIQUE INDEX "
    "entity_authorities_canonical_output_review_id_key "
    "ON public.entity_authorities USING btree "
    "(canonical_output_review_id)",
    "entity_authorities_employer_address_id_key": "CREATE UNIQUE INDEX "
    "entity_authorities_employer_address_id_key ON "
    "public.entity_authorities USING btree "
    "(employer_address_id)",
    "entity_authorities_employer_contact_details_id_key": "CREATE UNIQUE INDEX "
    "entity_authorities_employer_contact_details_id_key "
    "ON public.entity_authorities USING btree "
    "(employer_contact_details_id)",
    "entity_authorities_pkey": "CREATE UNIQUE INDEX entity_authorities_pkey ON "
    "public.entity_authorities USING btree (entity_type, entity_id)",
    "entity_authorities_staffing_request_id_key": "CREATE UNIQUE INDEX "
    "entity_authorities_staffing_request_id_key ON "
    "public.entity_authorities USING btree "
    "(staffing_request_id)",
    "entity_authorities_work_interest_id_key": "CREATE UNIQUE INDEX "
    "entity_authorities_work_interest_id_key ON "
    "public.entity_authorities USING btree "
    "(work_interest_id)",
    "entity_authorities_worker_contact_id_key": "CREATE UNIQUE INDEX "
    "entity_authorities_worker_contact_id_key ON "
    "public.entity_authorities USING btree "
    "(worker_contact_id)",
    "entity_authorities_worker_id_key": "CREATE UNIQUE INDEX entity_authorities_worker_id_key ON "
    "public.entity_authorities USING btree (worker_id)",
    "entity_authorities_worker_preferences_id_key": "CREATE UNIQUE INDEX "
    "entity_authorities_worker_preferences_id_key ON "
    "public.entity_authorities USING btree "
    "(worker_preferences_id)",
    "entity_authorities_worker_residence_id_key": "CREATE UNIQUE INDEX "
    "entity_authorities_worker_residence_id_key ON "
    "public.entity_authorities USING btree "
    "(worker_residence_id)",
    "entity_authorities_worksite_id_key": "CREATE UNIQUE INDEX entity_authorities_worksite_id_key ON "
    "public.entity_authorities USING btree (worksite_id)",
    "intake_addresses_pkey": "CREATE UNIQUE INDEX intake_addresses_pkey ON public.intake_addresses "
    "USING btree (intake_id, section)",
    "intake_finalizations_command_id_key": "CREATE UNIQUE INDEX intake_finalizations_command_id_key "
    "ON public.intake_finalizations USING btree (command_id)",
    "intake_finalizations_pkey": "CREATE UNIQUE INDEX intake_finalizations_pkey ON "
    "public.intake_finalizations USING btree (intake_id)",
    "intake_finalizations_staffing_request_id_key": "CREATE UNIQUE INDEX "
    "intake_finalizations_staffing_request_id_key ON "
    "public.intake_finalizations USING btree "
    "(staffing_request_id)",
    "intake_follow_up_events_command_id_key": "CREATE UNIQUE INDEX "
    "intake_follow_up_events_command_id_key ON "
    "public.intake_follow_up_events USING btree "
    "(command_id)",
    "intake_follow_up_events_intake_id_version_key": "CREATE UNIQUE INDEX "
    "intake_follow_up_events_intake_id_version_key "
    "ON public.intake_follow_up_events USING btree "
    "(intake_id, version)",
    "intake_follow_up_events_pkey": "CREATE UNIQUE INDEX intake_follow_up_events_pkey ON "
    "public.intake_follow_up_events USING btree (event_id)",
    "intake_history_payloads_pkey": "CREATE UNIQUE INDEX intake_history_payloads_pkey ON "
    "public.intake_history_payloads USING btree (event_id)",
    "intake_links_pkey": "CREATE UNIQUE INDEX intake_links_pkey ON public.intake_links USING btree "
    "(intake_id)",
    "intake_review_payloads_pkey": "CREATE UNIQUE INDEX intake_review_payloads_pkey ON "
    "public.intake_review_payloads USING btree (review_id)",
    "intake_reviews_command_id_key": "CREATE UNIQUE INDEX intake_reviews_command_id_key ON "
    "public.intake_reviews USING btree (command_id)",
    "intake_reviews_event_id_key": "CREATE UNIQUE INDEX intake_reviews_event_id_key ON "
    "public.intake_reviews USING btree (event_id)",
    "intake_reviews_intake_id_result_version_key": "CREATE UNIQUE INDEX "
    "intake_reviews_intake_id_result_version_key ON "
    "public.intake_reviews USING btree (intake_id, "
    "result_version)",
    "intake_reviews_intake_id_review_id_key": "CREATE UNIQUE INDEX "
    "intake_reviews_intake_id_review_id_key ON "
    "public.intake_reviews USING btree (intake_id, "
    "review_id)",
    "intake_reviews_pkey": "CREATE UNIQUE INDEX intake_reviews_pkey ON public.intake_reviews USING "
    "btree (review_id)",
    "intakes_pkey": "CREATE UNIQUE INDEX intakes_pkey ON public.intakes USING btree (intake_id)",
    "staffing_requests_employer_id_staffing_request_id_key": "CREATE UNIQUE INDEX "
    "staffing_requests_employer_id_staffing_request_id_key "
    "ON public.staffing_requests USING btree "
    "(employer_id, staffing_request_id)",
    "staffing_requests_pkey": "CREATE UNIQUE INDEX staffing_requests_pkey ON public.staffing_requests "
    "USING btree (staffing_request_id)",
    "uq_audit_events_command_entity": "CREATE UNIQUE INDEX uq_audit_events_command_entity ON "
    "public.audit_events USING btree (command_id, entity_type, "
    "entity_id)",
    "uq_audit_events_command_event_type": "CREATE UNIQUE INDEX uq_audit_events_command_event_type ON "
    "public.audit_events USING btree (command_id, event_type)",
    "uq_audit_events_entity_sequence": "CREATE UNIQUE INDEX uq_audit_events_entity_sequence ON "
    "public.audit_events USING btree (entity_type, entity_id, "
    "entity_sequence)",
    "uq_audit_events_result_authority": "CREATE UNIQUE INDEX uq_audit_events_result_authority ON "
    "public.audit_events USING btree (command_id, entity_id, "
    "new_record_version, event_type, actor_id)",
    "uq_command_receipts_actor_command": "CREATE UNIQUE INDEX uq_command_receipts_actor_command ON "
    "public.command_receipts USING btree (command_id, actor_id, "
    "command_type)",
    "uq_command_receipts_command_result": "CREATE UNIQUE INDEX uq_command_receipts_command_result ON "
    "public.command_receipts USING btree (command_id, "
    "result_entity_id)",
    "uq_command_receipts_command_result_entity": "CREATE UNIQUE INDEX "
    "uq_command_receipts_command_result_entity ON "
    "public.command_receipts USING btree (command_id, "
    "result_entity_type, result_entity_id)",
    "uq_command_receipts_result_authority": "CREATE UNIQUE INDEX uq_command_receipts_result_authority "
    "ON public.command_receipts USING btree (command_id, "
    "result_entity_type, result_entity_id, "
    "result_record_version, result_event_type, actor_id)",
    "uq_command_results_exact_authority": "CREATE UNIQUE INDEX uq_command_results_exact_authority ON "
    "public.command_results USING btree (command_id, "
    "entity_type, entity_id, result_version, event_type, "
    "actor_id)",
    "uq_contact_details_link_parent": "CREATE UNIQUE INDEX uq_contact_details_link_parent ON "
    "public.employer_contact_details USING btree (employer_id, "
    "employer_contact_id, employer_contact_details_id)",
    "uq_employer_contacts_parent_scoped_identity": "CREATE UNIQUE INDEX "
    "uq_employer_contacts_parent_scoped_identity ON "
    "public.employer_contacts USING btree "
    "(employer_id, employer_contact_id)",
    "uq_entity_authorities_employer_contact_id": "CREATE UNIQUE INDEX "
    "uq_entity_authorities_employer_contact_id ON "
    "public.entity_authorities USING btree "
    "(employer_contact_id)",
    "uq_entity_authorities_employer_id": "CREATE UNIQUE INDEX uq_entity_authorities_employer_id ON "
    "public.entity_authorities USING btree (employer_id)",
    "uq_entity_authorities_intake_id": "CREATE UNIQUE INDEX uq_entity_authorities_intake_id ON "
    "public.entity_authorities USING btree (intake_id)",
    "uq_finalization_created_employer": "CREATE UNIQUE INDEX uq_finalization_created_employer ON "
    "public.intake_finalizations USING btree (employer_id) WHERE "
    "((employer_disposition)::text = 'created'::text)",
    "uq_finalization_created_employer_address": "CREATE UNIQUE INDEX "
    "uq_finalization_created_employer_address ON "
    "public.intake_finalizations USING btree "
    "(employer_address_id) WHERE "
    "((employer_address_disposition)::text = "
    "'created'::text)",
    "uq_finalization_created_employer_contact": "CREATE UNIQUE INDEX "
    "uq_finalization_created_employer_contact ON "
    "public.intake_finalizations USING btree "
    "(employer_contact_id) WHERE "
    "((employer_contact_disposition)::text = "
    "'created'::text)",
    "uq_finalization_created_employer_contact_details": "CREATE UNIQUE INDEX "
    "uq_finalization_created_employer_contact_details "
    "ON public.intake_finalizations USING btree "
    "(employer_contact_details_id) WHERE "
    "((employer_contact_details_disposition)::text "
    "= 'created'::text)",
    "uq_finalization_created_worker": "CREATE UNIQUE INDEX uq_finalization_created_worker ON "
    "public.intake_finalizations USING btree (worker_id) WHERE "
    "((worker_disposition)::text = 'created'::text)",
    "uq_finalization_created_worker_contact": "CREATE UNIQUE INDEX "
    "uq_finalization_created_worker_contact ON "
    "public.intake_finalizations USING btree "
    "(worker_contact_id) WHERE "
    "((worker_contact_disposition)::text = 'created'::text)",
    "uq_finalization_created_worker_preferences": "CREATE UNIQUE INDEX "
    "uq_finalization_created_worker_preferences ON "
    "public.intake_finalizations USING btree "
    "(worker_preferences_id) WHERE "
    "((worker_preferences_disposition)::text = "
    "'created'::text)",
    "uq_finalization_created_worker_residence": "CREATE UNIQUE INDEX "
    "uq_finalization_created_worker_residence ON "
    "public.intake_finalizations USING btree "
    "(worker_residence_id) WHERE "
    "((worker_residence_disposition)::text = "
    "'created'::text)",
    "uq_finalization_created_worksite": "CREATE UNIQUE INDEX uq_finalization_created_worksite ON "
    "public.intake_finalizations USING btree (worksite_id) WHERE "
    "((worksite_disposition)::text = 'created'::text)",
    "uq_intakes_employer_link": "CREATE UNIQUE INDEX uq_intakes_employer_link ON public.intakes USING "
    "btree (intake_id, employer_id)",
    "uq_intakes_id_kind": "CREATE UNIQUE INDEX uq_intakes_id_kind ON public.intakes USING btree "
    "(intake_id, kind)",
    "uq_intakes_worker_link": "CREATE UNIQUE INDEX uq_intakes_worker_link ON public.intakes USING "
    "btree (intake_id, worker_id)",
    "work_interest_versions_command_id_key": "CREATE UNIQUE INDEX "
    "work_interest_versions_command_id_key ON "
    "public.work_interest_versions USING btree (command_id)",
    "work_interest_versions_pkey": "CREATE UNIQUE INDEX work_interest_versions_pkey ON "
    "public.work_interest_versions USING btree (interest_id, version)",
    "work_interests_code_key": "CREATE UNIQUE INDEX work_interests_code_key ON public.work_interests "
    "USING btree (code)",
    "work_interests_pkey": "CREATE UNIQUE INDEX work_interests_pkey ON public.work_interests USING "
    "btree (interest_id)",
    "worker_contacts_pkey": "CREATE UNIQUE INDEX worker_contacts_pkey ON public.worker_contacts USING "
    "btree (worker_contact_id)",
    "worker_contacts_worker_id_key": "CREATE UNIQUE INDEX worker_contacts_worker_id_key ON "
    "public.worker_contacts USING btree (worker_id)",
    "worker_contacts_worker_id_worker_contact_id_key": "CREATE UNIQUE INDEX "
    "worker_contacts_worker_id_worker_contact_id_key "
    "ON public.worker_contacts USING btree "
    "(worker_id, worker_contact_id)",
    "worker_interest_selections_pkey": "CREATE UNIQUE INDEX worker_interest_selections_pkey ON "
    "public.worker_interest_selections USING btree "
    "(worker_preferences_id, interest_id)",
    "worker_preferences_pkey": "CREATE UNIQUE INDEX worker_preferences_pkey ON "
    "public.worker_preferences USING btree (worker_preferences_id)",
    "worker_preferences_worker_id_key": "CREATE UNIQUE INDEX worker_preferences_worker_id_key ON "
    "public.worker_preferences USING btree (worker_id)",
    "worker_preferences_worker_id_worker_preferences_id_key": "CREATE UNIQUE INDEX "
    "worker_preferences_worker_id_worker_preferences_id_key "
    "ON public.worker_preferences USING "
    "btree (worker_id, "
    "worker_preferences_id)",
    "worker_residences_pkey": "CREATE UNIQUE INDEX worker_residences_pkey ON public.worker_residences "
    "USING btree (worker_residence_id)",
    "worker_residences_worker_id_key": "CREATE UNIQUE INDEX worker_residences_worker_id_key ON "
    "public.worker_residences USING btree (worker_id)",
    "worker_residences_worker_id_worker_residence_id_key": "CREATE UNIQUE INDEX "
    "worker_residences_worker_id_worker_residence_id_key "
    "ON public.worker_residences USING btree "
    "(worker_id, worker_residence_id)",
    "workers_pkey": "CREATE UNIQUE INDEX workers_pkey ON public.workers USING btree (worker_id)",
    "worksites_employer_id_worksite_id_key": "CREATE UNIQUE INDEX "
    "worksites_employer_id_worksite_id_key ON "
    "public.worksites USING btree (employer_id, worksite_id)",
    "worksites_pkey": "CREATE UNIQUE INDEX worksites_pkey ON public.worksites USING btree "
    "(worksite_id)",
}
