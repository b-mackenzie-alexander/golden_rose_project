locals {
  metadata_only_secret_ids = toset([
    "database-url",
    "synthetic-staff-id",
    "deployment-posture",
  ])
}

resource "google_secret_manager_secret" "metadata_only" {
  for_each = local.metadata_only_secret_ids

  project   = var.project_id
  secret_id = each.value
  labels    = local.standard_labels

  replication {
    auto {}
  }
}
