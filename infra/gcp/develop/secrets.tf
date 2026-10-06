locals {
  metadata_only_secret_ids = toset([
    "runtime-database-url",
    "migration-database-url",
    "synthetic-staff-id",
    "demo-access-password",
    "deployment-posture",
    "staff-bootstrap-provider-subject",
    "staff-bootstrap-display-name",
  ])

  staff_oidc_secret_lookup_enabled = var.deployment_stage == "service" && var.runtime_profile == "controlled_live_data_staff_pilot"
}

resource "google_secret_manager_secret" "metadata_only" {
  for_each = local.metadata_only_secret_ids

  project   = local.canonical_workload_project_number
  secret_id = each.value
  labels    = local.standard_labels

  replication {
    auto {}
  }

  depends_on = [google_project_service.approved["secretmanager.googleapis.com"]]
}

data "google_secret_manager_secret" "staff_oidc_issuer" {
  count = local.staff_oidc_secret_lookup_enabled ? 1 : 0

  project   = local.canonical_workload_project_number
  secret_id = "staff-oidc-issuer"

  depends_on = [google_project_service.approved["secretmanager.googleapis.com"]]
}

data "google_secret_manager_secret" "staff_oidc_audience" {
  count = local.staff_oidc_secret_lookup_enabled ? 1 : 0

  project   = local.canonical_workload_project_number
  secret_id = "staff-oidc-audience"

  depends_on = [google_project_service.approved["secretmanager.googleapis.com"]]
}

data "google_secret_manager_secret" "staff_oidc_jwks_url" {
  count = local.staff_oidc_secret_lookup_enabled ? 1 : 0

  project   = local.canonical_workload_project_number
  secret_id = "staff-oidc-jwks-url"

  depends_on = [google_project_service.approved["secretmanager.googleapis.com"]]
}
