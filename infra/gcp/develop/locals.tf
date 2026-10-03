locals {
  standard_labels = {
    environment   = "develop"
    data_boundary = var.runtime_profile == "controlled_live_data_staff_pilot" ? "controlled-live-data-staff-pilot" : "fictional-synthetic-only"
    managed_by    = "terraform"
    service       = "staff-tracer"
    cost_center   = "develop"
    owner         = "technical-owner"
    teardown      = "intentional-runbook-only"
  }

  managed_container_image = var.container_image_digest == null ? null : "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.application_images.repository_id}/staff-tracer@${var.container_image_digest}"
}
