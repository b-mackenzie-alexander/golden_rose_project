resource "google_cloud_run_v2_service" "staff_tracer" {
  project             = var.project_id
  name                = "staff-tracer"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  deletion_protection = true
  labels              = local.standard_labels

  template {
    service_account = google_service_account.runtime.email

    containers {
      image = var.container_image_digest
    }
  }
}
