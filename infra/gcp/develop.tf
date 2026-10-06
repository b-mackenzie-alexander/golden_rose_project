module "develop" {
  source = "./develop"

  project_id               = var.project_id
  control_plane_project_id = var.control_plane_project_id
  region                   = var.region
  container_image_digest   = var.container_image_digest
  deployment_stage         = var.deployment_stage
  runtime_profile          = var.runtime_profile
  direct_vpc_subnet_cidr   = var.direct_vpc_subnet_cidr

  demo_access_expires_at                          = var.demo_access_expires_at
  staff_oidc_issuer_secret_version                = var.staff_oidc_issuer_secret_version
  staff_oidc_audience_secret_version              = var.staff_oidc_audience_secret_version
  staff_oidc_jwks_url_secret_version              = var.staff_oidc_jwks_url_secret_version
  staff_bootstrap_provider_subject_secret_version = var.staff_bootstrap_provider_subject_secret_version
  staff_bootstrap_display_name_secret_version     = var.staff_bootstrap_display_name_secret_version
  billing_account_id                              = var.billing_account_id
  alert_notification_email_address                = var.alert_notification_email_address
  observability_viewer_principal                  = var.observability_viewer_principal
  log_retention_days                              = var.log_retention_days
  cloud_run_request_log_posture                   = var.cloud_run_request_log_posture
  cloud_sql_backup_enabled                        = var.cloud_sql_backup_enabled
  cloud_sql_backup_start_time                     = var.cloud_sql_backup_start_time
  cloud_sql_point_in_time_recovery_enabled        = var.cloud_sql_point_in_time_recovery_enabled
  cloud_sql_transaction_log_retention_days        = var.cloud_sql_transaction_log_retention_days
  cloud_sql_retained_backups                      = var.cloud_sql_retained_backups
  cloud_sql_database_name                         = var.cloud_sql_database_name
  cloud_sql_schema_owner_role                     = var.cloud_sql_schema_owner_role
  cloud_sql_migrator_role                         = var.cloud_sql_migrator_role
  cloud_sql_runtime_role                          = var.cloud_sql_runtime_role
  cloud_sql_recovery_policy_review_status         = var.cloud_sql_recovery_policy_review_status
  golden_rose_public_environment_label            = var.golden_rose_public_environment_label
}
