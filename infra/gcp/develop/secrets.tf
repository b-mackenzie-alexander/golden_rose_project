locals {
  metadata_only_secret_ids = toset([
    "runtime-database-url",
    "migration-database-url",
    "synthetic-staff-id",
    "demo-access-password",
    "staff-oidc-issuer",
    "staff-oidc-audience",
    "staff-oidc-jwks-url",
    "deployment-posture",
  ])
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
