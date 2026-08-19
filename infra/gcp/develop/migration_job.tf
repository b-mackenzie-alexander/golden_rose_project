resource "google_cloud_run_v2_job" "migration" {
  project  = var.project_id
  name     = "run-migrations"
  location = var.region
  labels   = local.standard_labels

  template {
    template {
      service_account = google_service_account.migration.email
      max_retries     = 0
      timeout         = "1800s"

      vpc_access {
        egress = "PRIVATE_RANGES_ONLY"

        network_interfaces {
          network    = google_compute_network.develop.id
          subnetwork = google_compute_subnetwork.direct_vpc.id
        }
      }

      containers {
        image = local.managed_container_image

        command = ["golden-rose-migrate"]
      }
    }

    task_count  = 1
    parallelism = 1
  }

  depends_on = [
    google_project_service.approved["run.googleapis.com"],
    google_billing_budget.develop,
    google_monitoring_alert_policy.health_failures,
    google_monitoring_alert_policy.readiness_failures,
    google_monitoring_alert_policy.service_error_events,
    google_logging_project_bucket_config.default,
  ]
}
