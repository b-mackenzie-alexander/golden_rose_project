output "database_contract" {
  description = "Sensitive minimal database metadata and reviewed role identifiers for the private synthetic develop environment."
  value = var.deployment_stage == "foundation" ? null : {
    instance_name      = google_sql_database_instance.develop[0].name
    database_name      = google_sql_database.application[0].name
    schema_owner_role  = var.cloud_sql_schema_owner_role
    migrator_role      = var.cloud_sql_migrator_role
    runtime_role       = var.cloud_sql_runtime_role
    database_version   = google_sql_database_instance.develop[0].database_version
    deletion_protected = google_sql_database_instance.develop[0].deletion_protection
  }
  sensitive = true
}

output "database_recovery_contract" {
  description = "Sensitive reviewed recovery-input contract for the private synthetic develop environment pending later gate approval."
  value = var.deployment_stage == "foundation" ? null : {
    backup_enabled                 = var.cloud_sql_backup_enabled
    backup_start_time              = var.cloud_sql_backup_start_time
    point_in_time_recovery_enabled = var.cloud_sql_point_in_time_recovery_enabled
    transaction_log_retention_days = var.cloud_sql_transaction_log_retention_days
    retained_backups               = var.cloud_sql_retained_backups
    recovery_policy_review_status  = var.cloud_sql_recovery_policy_review_status
  }
  sensitive = true
}

output "cost_guardrail_contract" {
  description = "Value-safe reviewed cost-guardrail contract for the private synthetic develop environment."
  value = {
    budget_thresholds_usd = [50, 75, 100]
    hard_cap_enforced     = false
    startup_dependency    = true
    routing_mode          = "operator-held-notification-channel"
  }
}

output "observability_contract" {
  description = "Value-safe reviewed observability contract for the private synthetic develop environment."
  value = {
    log_retention_days                = var.log_retention_days
    request_log_posture               = var.cloud_run_request_log_posture
    startup_dependency                = true
    broad_export_sink_modeled         = false
    authenticated_readiness_uptime    = var.deployment_stage == "service"
    readiness_alert_is_review_trigger = true
    approved_service_level_commitment = false
  }
}

output "human_visible_develop_contract" {
  description = "Value-safe runtime access and cost-bound markers for the selected develop profile."
  value = var.deployment_stage == "service" ? {
    access_mode    = var.runtime_profile == "controlled_live_data_staff_pilot" ? "named-staff-oidc" : "expiring-http-basic"
    public_invoker = true
    min_instances  = 0
    max_instances  = 1
    data_boundary  = var.runtime_profile == "controlled_live_data_staff_pilot" ? "controlled-live-data-staff-pilot" : "fictional-synthetic-only"
  } : null
}
