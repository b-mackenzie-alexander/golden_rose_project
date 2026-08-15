resource "google_cloud_run_v2_service" "staff_tracer" {
  project             = var.project_id
  name                = "staff-tracer"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  deletion_protection = true
  labels              = local.standard_labels

  template {
    service_account = google_service_account.runtime.email

    vpc_access {
      egress = "PRIVATE_RANGES_ONLY"

      network_interfaces {
        network    = google_compute_network.develop.id
        subnetwork = google_compute_subnetwork.direct_vpc.id
      }
    }

    containers {
      image = local.managed_container_image
    }
  }

  depends_on = [google_project_service.approved["run.googleapis.com"]]
}
