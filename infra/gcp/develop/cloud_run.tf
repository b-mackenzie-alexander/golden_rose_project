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
        value = var.runtime_profile == "controlled_live_data_staff_pilot" ? "production" : "develop"
      }

      env {
        name  = "GOLDEN_ROSE_AUTH_MODE"
        value = var.runtime_profile == "controlled_live_data_staff_pilot" ? "staff_oidc" : "synthetic"
      }

      env {
        name  = "GOLDEN_ROSE_DEPLOYMENT_TARGET"
        value = var.runtime_profile == "controlled_live_data_staff_pilot" ? "controlled-live-data-staff-pilot" : "gcp-develop-private-synthetic"
      }

      env {
        name  = "GOLDEN_ROSE_PUBLIC_ENVIRONMENT_LABEL"
        value = var.runtime_profile == "controlled_live_data_staff_pilot" ? "Controlled live-data staff pilot" : var.golden_rose_public_environment_label
      }

      env {
        name  = "GOLDEN_ROSE_DEPLOYED_IMAGE_DIGEST"
        value = var.container_image_digest
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

      dynamic "env" {
        for_each = var.runtime_profile == "synthetic_develop_demo" ? {
          GOLDEN_ROSE_DEMO_ACCESS_ENABLED            = "true"
          GOLDEN_ROSE_DEMO_ACCESS_EXPIRES_AT         = var.demo_access_expires_at
          GOLDEN_ROSE_PRESENTATION_DEMO_SEED_ENABLED = "true"
        } : {}

        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.runtime_profile == "synthetic_develop_demo" ? {
          demo_access_password = {
            name   = "GOLDEN_ROSE_DEMO_ACCESS_PASSWORD"
            secret = "demo-access-password"
          }
          synthetic_staff_id = {
            name   = "GOLDEN_ROSE_SYNTHETIC_STAFF_ID"
            secret = "synthetic-staff-id"
          }
        } : {}

        content {
          name = env.value.name
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = var.runtime_profile == "controlled_live_data_staff_pilot" ? {
          GOLDEN_ROSE_DEMO_ACCESS_ENABLED            = "false"
          GOLDEN_ROSE_PRESENTATION_DEMO_SEED_ENABLED = "false"
        } : {}

        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.runtime_profile == "controlled_live_data_staff_pilot" ? {
          GOLDEN_ROSE_STAFF_OIDC_ISSUER = {
            secret  = "staff-oidc-issuer"
            version = var.staff_oidc_issuer_secret_version
          }
          GOLDEN_ROSE_STAFF_OIDC_AUDIENCE = {
            secret  = "staff-oidc-audience"
            version = var.staff_oidc_audience_secret_version
          }
          GOLDEN_ROSE_STAFF_OIDC_JWKS_URL = {
            secret  = "staff-oidc-jwks-url"
            version = var.staff_oidc_jwks_url_secret_version
          }
        } : {}

        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = env.value.version
            }
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
    google_secret_manager_secret_iam_member.runtime_staff_oidc_issuer_secret_access,
    google_secret_manager_secret_iam_member.runtime_staff_oidc_audience_secret_access,
    google_secret_manager_secret_iam_member.runtime_staff_oidc_jwks_url_secret_access,
  ]
}
