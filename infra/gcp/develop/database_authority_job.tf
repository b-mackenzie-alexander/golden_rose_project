resource "google_cloud_run_v2_job" "database_authority" {
  count = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0

  project  = var.project_id
  name     = "verify-database-authority"
  location = var.region
  labels   = local.standard_labels

  template {
    template {
      service_account = google_service_account.database_verifier.email
      max_retries     = 0
      timeout         = "600s"

      vpc_access {
        egress = "PRIVATE_RANGES_ONLY"

        network_interfaces {
          network    = google_compute_network.develop[0].id
          subnetwork = google_compute_subnetwork.direct_vpc[0].id
        }
      }

      containers {
        image   = local.managed_container_image
        command = ["python", "/app/scripts/verify_database_authority.py"]

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
          name = "GOLDEN_ROSE_MIGRATION_DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = "migration-database-url"
              version = "latest"
            }
          }
        }

        env {
          name = "GOLDEN_ROSE_RUNTIME_DATABASE_URL"
          value_source {
            secret_key_ref {
              secret  = "runtime-database-url"
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
    google_secret_manager_secret_iam_member.database_verifier_migration_secret_access,
    google_secret_manager_secret_iam_member.database_verifier_runtime_secret_access,
  ]
}
