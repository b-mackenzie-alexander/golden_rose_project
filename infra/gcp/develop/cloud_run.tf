resource "google_cloud_run_v2_service" "staff_tracer" {
  count = var.deployment_stage == "service" ? 1 : 0

  project             = var.project_id
  name                = "staff-tracer"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = true
  labels              = local.standard_labels

  template {
    service_account                  = google_service_account.runtime.email
    timeout                          = "60s"
    max_instance_request_concurrency = 10

    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    vpc_access {
      egress = "PRIVATE_RANGES_ONLY"

      network_interfaces {
        network    = google_compute_network.develop[0].id
        subnetwork = google_compute_subnetwork.direct_vpc[0].id
      }
    }

    containers {
      image = local.managed_container_image

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

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
        name  = "GOLDEN_ROSE_DEMO_ACCESS_ENABLED"
        value = "true"
      }

      env {
        name  = "GOLDEN_ROSE_DEMO_ACCESS_EXPIRES_AT"
        value = var.demo_access_expires_at
      }

      env {
        name = "GOLDEN_ROSE_DEMO_ACCESS_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = "demo-access-password"
            version = "latest"
          }
        }
      }

      env {
        name = "GOLDEN_ROSE_DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = "runtime-database-url"
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

  depends_on = [
    google_project_service.approved["run.googleapis.com"],
    google_billing_budget.develop,
    google_monitoring_alert_policy.health_failures,
    google_monitoring_alert_policy.service_error_events,
    google_logging_project_bucket_config.default,
    google_secret_manager_secret_iam_member.runtime_demo_access_secret_access,
  ]
}
