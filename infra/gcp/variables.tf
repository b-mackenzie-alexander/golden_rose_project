variable "project_id" {
  description = "GCP project identifier supplied out of band for local validation or approved provisioning."
  type        = string
  nullable    = false
}

variable "control_plane_project_id" {
  description = "GCP project identifier for reviewed control-plane identities such as the image publisher."
  type        = string
  nullable    = false
}

variable "region" {
  description = "Approved GCP region for the private synthetic develop environment."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["us-east4"], var.region)
    error_message = "The develop environment is currently approved only for us-east4."
  }
}

variable "container_image_digest" {
  description = "Immutable sha256 digest supplied out of band for the managed Artifact Registry staff-tracer image. Nullable so the foundation stage may omit it; required for migration and service stages."
  type        = string
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "foundation" ? var.container_image_digest == null : var.container_image_digest != null && can(regex("sha256:[0-9a-f]{64}$", var.container_image_digest))
    error_message = "Foundation requires no image digest; migration and service require only an immutable sha256 digest."
  }
}

variable "deployment_stage" {
  description = "Staged deployment authority: foundation creates no executable workload, migration adds the configured migration job, and service adds the configured staff service."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["foundation", "migration", "service"], var.deployment_stage)
    error_message = "The deployment stage must be one of: foundation, migration, service."
  }
}

variable "runtime_profile" {
  description = "Reviewed runtime profile for the develop package: historical synthetic demo or controlled named-staff live-data pilot."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["synthetic_develop_demo", "controlled_live_data_staff_pilot"], var.runtime_profile)
    error_message = "The runtime profile must be synthetic_develop_demo or controlled_live_data_staff_pilot."
  }
}

variable "direct_vpc_subnet_cidr" {
  description = "RFC1918 /26-or-broader subnet CIDR reserved out of band for Direct VPC egress and private service access validation."
  type        = string
  nullable    = true
  default     = null

  validation {
    condition = var.deployment_stage == "foundation" ? var.direct_vpc_subnet_cidr == null : var.direct_vpc_subnet_cidr != null && can(cidrnetmask(var.direct_vpc_subnet_cidr)) && can(regex(
      "^(10\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])/(8|9|1[0-9]|2[0-6])|172\\.(1[6-9]|2[0-9]|3[0-1])\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])/(1[2-9]|2[0-6])|192\\.168\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])/(1[6-9]|2[0-6]))$",
      var.direct_vpc_subnet_cidr
    )) && cidrhost(var.direct_vpc_subnet_cidr, 0) == split("/", var.direct_vpc_subnet_cidr)[0]
    error_message = "The Direct VPC subnet CIDR must be an RFC1918 /26-or-broader range supplied out of band."
  }
}


variable "demo_access_expires_at" {
  description = "Sensitive strict UTC RFC 3339 expiry for the temporary service-stage shared demo access gate; required only for the synthetic demo runtime profile."
  type        = string
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "service" && var.runtime_profile == "synthetic_develop_demo" ? var.demo_access_expires_at != null && can(regex("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$", var.demo_access_expires_at)) : var.demo_access_expires_at == null
    error_message = "The synthetic demo service profile requires one strict UTC RFC 3339 demo-access expiry; every other stage/profile requires null."
  }

  sensitive = true
}

variable "staff_oidc_issuer_secret_version" {
  description = "Operator-held enabled Secret Manager version number for staff-oidc-issuer; required only for the controlled staff-pilot service profile so corrected values create a new Cloud Run revision."
  type        = string
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "service" && var.runtime_profile == "controlled_live_data_staff_pilot" ? var.staff_oidc_issuer_secret_version != null && can(regex("^[1-9][0-9]*$", var.staff_oidc_issuer_secret_version)) : var.staff_oidc_issuer_secret_version == null
    error_message = "The controlled staff-pilot service profile requires an explicit numeric staff OIDC issuer secret version; every other stage/profile requires null."
  }
}

variable "staff_oidc_audience_secret_version" {
  description = "Operator-held enabled Secret Manager version number for staff-oidc-audience; required only for the controlled staff-pilot service profile so corrected values create a new Cloud Run revision."
  type        = string
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "service" && var.runtime_profile == "controlled_live_data_staff_pilot" ? var.staff_oidc_audience_secret_version != null && can(regex("^[1-9][0-9]*$", var.staff_oidc_audience_secret_version)) : var.staff_oidc_audience_secret_version == null
    error_message = "The controlled staff-pilot service profile requires an explicit numeric staff OIDC audience secret version; every other stage/profile requires null."
  }
}

variable "staff_oidc_jwks_url_secret_version" {
  description = "Operator-held enabled Secret Manager version number for staff-oidc-jwks-url; required only for the controlled staff-pilot service profile so corrected values create a new Cloud Run revision."
  type        = string
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "service" && var.runtime_profile == "controlled_live_data_staff_pilot" ? var.staff_oidc_jwks_url_secret_version != null && can(regex("^[1-9][0-9]*$", var.staff_oidc_jwks_url_secret_version)) : var.staff_oidc_jwks_url_secret_version == null
    error_message = "The controlled staff-pilot service profile requires an explicit numeric staff OIDC JWKS URL secret version; every other stage/profile requires null."
  }
}


variable "billing_account_id" {
  description = "Operator-supplied billing account identifier for reviewed develop budget routing."
  type        = string
  nullable    = false
}

variable "alert_notification_email_address" {
  description = "Operator-supplied alert-routing email address for reviewed develop budget and monitoring notifications."
  type        = string
  nullable    = false
}

variable "observability_viewer_principal" {
  description = "Operator-supplied principal allowed to read reviewed develop logging and monitoring evidence."
  type        = string
  nullable    = false
}

variable "log_retention_days" {
  description = "Explicit reviewed retention bound for develop platform logs."
  type        = number
  nullable    = false

  validation {
    condition     = floor(var.log_retention_days) == var.log_retention_days && var.log_retention_days >= 1 && var.log_retention_days <= 365
    error_message = "The develop log retention bound must be a whole number of 1-365 days supplied out of band."
  }
}

variable "cloud_run_request_log_posture" {
  description = "Value-safe marker for the reviewed Cloud Run request-log minimization posture enforced by exclusion plus restricted access/no export."
  type        = string
  nullable    = false

  validation {
    condition     = var.cloud_run_request_log_posture == "exclude-uuid-bearing-staff-paths-and-restrict-access-no-export"
    error_message = "The Cloud Run request-log posture must remain the reviewed exclusion-backed minimization posture."
  }
}

variable "cloud_sql_backup_enabled" {
  description = "Explicit backup enablement input for the reviewed develop Cloud SQL contract; no approved production value is implied until the later recovery gate accepts it."
  type        = bool
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "foundation" ? var.cloud_sql_backup_enabled == null : var.cloud_sql_backup_enabled != null
    error_message = "Foundation requires no Cloud SQL backup-enable input; migration and service require an explicit Cloud SQL backup-enable input."
  }
}

variable "cloud_sql_backup_start_time" {
  description = "Explicit UTC backup window start time for the reviewed develop Cloud SQL contract; operator-held until the later recovery gate accepts it."
  type        = string
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "foundation" ? var.cloud_sql_backup_start_time == null : var.cloud_sql_backup_start_time != null && can(regex("^([01][0-9]|2[0-3]):[0-5][0-9]$", var.cloud_sql_backup_start_time))
    error_message = "The Cloud SQL backup start time must be an exact HH:MM UTC value supplied out of band."
  }
}

variable "cloud_sql_point_in_time_recovery_enabled" {
  description = "Explicit PITR enablement input for the reviewed develop Cloud SQL contract; no approved production recovery posture is implied until the later gate accepts it."
  type        = bool
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "foundation" ? var.cloud_sql_point_in_time_recovery_enabled == null : var.cloud_sql_point_in_time_recovery_enabled != null
    error_message = "Foundation requires no Cloud SQL PITR input; migration and service require an explicit Cloud SQL PITR input."
  }
}

variable "cloud_sql_transaction_log_retention_days" {
  description = "Explicit transaction-log retention input for the reviewed develop Cloud SQL contract; operator-held until recovery evidence is accepted."
  type        = number
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "foundation" ? var.cloud_sql_transaction_log_retention_days == null : var.cloud_sql_transaction_log_retention_days != null && floor(var.cloud_sql_transaction_log_retention_days) == var.cloud_sql_transaction_log_retention_days && var.cloud_sql_transaction_log_retention_days >= 1 && var.cloud_sql_transaction_log_retention_days <= 7
    error_message = "The Cloud SQL transaction log retention input must be a whole number between 1 and 7 days."
  }
}

variable "cloud_sql_retained_backups" {
  description = "Explicit retained-backup count for the reviewed develop Cloud SQL contract; operator-held until recovery evidence is accepted."
  type        = number
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "foundation" ? var.cloud_sql_retained_backups == null : var.cloud_sql_retained_backups != null && floor(var.cloud_sql_retained_backups) == var.cloud_sql_retained_backups && var.cloud_sql_retained_backups >= 1 && var.cloud_sql_retained_backups <= 365
    error_message = "The Cloud SQL retained backup count must be a whole number between 1 and 365 backups."
  }
}

variable "cloud_sql_database_name" {
  description = "Non-secret reviewed application database identifier for the private synthetic develop environment."
  type        = string
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "foundation" ? var.cloud_sql_database_name == null : var.cloud_sql_database_name != null && can(regex("^[a-z][a-z0-9_]{2,62}$", var.cloud_sql_database_name))
    error_message = "The Cloud SQL database name must be a lowercase PostgreSQL-safe identifier supplied out of band."
  }
}

variable "cloud_sql_schema_owner_role" {
  description = "Non-secret reviewed schema-owner role identifier for the private synthetic develop environment."
  type        = string
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "foundation" ? var.cloud_sql_schema_owner_role == null : var.cloud_sql_schema_owner_role == "golden_rose_schema_owner"
    error_message = "Migration and service stages require the exact golden_rose_schema_owner role."
  }
}

variable "cloud_sql_migrator_role" {
  description = "Non-secret reviewed migration role identifier for the private synthetic develop environment."
  type        = string
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "foundation" ? var.cloud_sql_migrator_role == null : var.cloud_sql_migrator_role == "golden_rose_migrator"
    error_message = "Migration and service stages require the exact golden_rose_migrator role."
  }
}

variable "cloud_sql_runtime_role" {
  description = "Non-secret reviewed runtime role identifier for the private synthetic develop environment."
  type        = string
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "foundation" ? var.cloud_sql_runtime_role == null : var.cloud_sql_runtime_role == "golden_rose_runtime"
    error_message = "Migration and service stages require the exact golden_rose_runtime role."
  }
}

variable "cloud_sql_recovery_policy_review_status" {
  description = "Explicit marker showing Cloud SQL backup, PITR, retention, and restore values remain pending the later recovery-evidence gate."
  type        = string
  nullable    = true
  default     = null

  validation {
    condition     = var.deployment_stage == "foundation" ? var.cloud_sql_recovery_policy_review_status == null : var.cloud_sql_recovery_policy_review_status != null && var.cloud_sql_recovery_policy_review_status == "gate-2-evidence-required"
    error_message = "The Cloud SQL recovery-policy marker must remain gate-2-evidence-required until later recovery evidence is accepted."
  }
}

variable "golden_rose_public_environment_label" {
  description = "Operator-held reviewed non-secret public environment label for the develop migration/demo runtime containing 'non-production' and 'synthetic'."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("non-production", var.golden_rose_public_environment_label)) && can(regex("synthetic", var.golden_rose_public_environment_label))
    error_message = "The public environment label must contain 'non-production' and 'synthetic'."
  }
}
