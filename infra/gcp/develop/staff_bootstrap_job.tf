resource "google_cloud_run_v2_job" "staff_bootstrap" {
  count = var.deployment_stage == "service" && var.runtime_profile == "controlled_live_data_staff_pilot" ? 1 : 0

  project  = var.project_id
  name     = "bootstrap-first-staff-account"
  location = var.region
  labels   = local.standard_labels

  template {
    template {
      service_account = google_service_account.staff_bootstrap.email
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
        command = ["golden-rose-bootstrap-first-staff-account"]

        env {
          name  = "GOLDEN_ROSE_ENVIRONMENT"
          value = "production"
        }

        env {
          name  = "GOLDEN_ROSE_AUTH_MODE"
          value = "staff_oidc"
        }

        env {
          name  = "GOLDEN_ROSE_DEPLOYMENT_TARGET"
          value = "controlled-live-data-staff-pilot"
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
          name = "GOLDEN_ROSE_BOOTSTRAP_PROVIDER_SUBJECT"
          value_source {
            secret_key_ref {
              secret  = "staff-bootstrap-provider-subject"
              version = var.staff_bootstrap_provider_subject_secret_version
            }
          }
        }

        env {
          name = "GOLDEN_ROSE_BOOTSTRAP_DISPLAY_NAME"
          value_source {
            secret_key_ref {
              secret  = "staff-bootstrap-display-name"
              version = var.staff_bootstrap_display_name_secret_version
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
    google_secret_manager_secret_iam_member.staff_bootstrap_database_secret_access,
    google_secret_manager_secret_iam_member.staff_bootstrap_provider_subject_secret_access,
    google_secret_manager_secret_iam_member.staff_bootstrap_display_name_secret_access,
  ]
}
