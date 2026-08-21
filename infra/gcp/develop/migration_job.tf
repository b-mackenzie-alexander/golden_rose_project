resource "google_cloud_run_v2_job" "migration" {
  count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0

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

        env {
          name  = "GOLDEN_ROSE_ENVIRONMENT"
          value = "develop"
        }

        env {
          name  = "GOLDEN_ROSE_AUTH_MODE"
          value = "synthetic"
        }

        env {
          name  = "GOLDEN_ROSE_DEPLOYMENT_TARGET"
          value = "gcp-develop-private-synthetic"
        }

        env {
          name  = "GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL"
          value = var.golden_rose_public_environment_label
        }

        env {
          name  = "GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST"
          value = var.container_image_digest
        }

        env {
          name  = "GOLDEN_ROSE_MIGRATION_ASSUMED_ROLE"
          value = "golden_rose_schema_owner"
        }

        env {
          name = "GOLDEN_ROSE_DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = "migration-database-url"
              version = "latest"
            }
          }
        }

        env {
          name = "GOLDEN_ROSE_SYNTHETIC_STAFF_ID"
          value_source {
            secret_key_ref {
              secret  = "synthetic-staff-id"
              version = "latest"
            }
          }
        }
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
