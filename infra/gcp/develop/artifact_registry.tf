resource "google_artifact_registry_repository" "application_images" {
  project       = var.project_id
  location      = var.region
  repository_id = "staff-tracer-images"
  description   = "Private Docker images for the develop staff tracer."
  format        = "DOCKER"
  labels        = local.standard_labels

  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "delete-untagged-older-than-fourteen-days"
    action = "DELETE"

    condition {
      tag_state  = "UNTAGGED"
      older_than = "1209600s"
    }
  }

  cleanup_policies {
    id     = "keep-latest-tagged-release-candidates"
    action = "KEEP"

    most_recent_versions {
      keep_count = 10
    }
  }

  depends_on = [google_project_service.approved["artifactregistry.googleapis.com"]]
}
