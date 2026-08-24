data "google_project" "current" {
  project_id = var.project_id
}

locals {
  request_log_posture             = var.cloud_run_request_log_posture
  monitoring_service_agent_member = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-monitoring-notification.iam.gserviceaccount.com"
  readiness_uptime_host           = replace(google_cloud_run_v2_service.staff_tracer[0].uri, "https://", "")
}

resource "google_monitoring_notification_channel" "alerts" {
  project      = var.project_id
  display_name = "Develop private synthetic alert route"
  type         = "email"
  enabled      = true

  labels = {
    email_address = var.alert_notification_email_address
  }

  depends_on = [google_project_service.approved["monitoring.googleapis.com"]]
}

resource "google_logging_project_bucket_config" "default" {
  project        = var.project_id
  location       = "global"
  bucket_id      = "_Default"
  retention_days = var.log_retention_days

  depends_on = [google_project_service.approved["logging.googleapis.com"]]
}

resource "google_logging_project_exclusion" "uuid_bearing_staff_paths" {
  project     = var.project_id
  name        = "develop-exclude-uuid-bearing-staff-paths"
  description = "Exclude routine Cloud Run request logs for UUID-bearing staff API paths so read-side identifiers are not retained in routine request logs."
  filter      = "resource.type=\"cloud_run_revision\" AND httpRequest.requestUrl=~\"/api/staff/v1/employers/[0-9a-fA-F-]{36}(/contacts(/[0-9a-fA-F-]{36})?)?$\""

  depends_on = [google_project_service.approved["logging.googleapis.com"]]
}

resource "google_project_iam_member" "observability_log_viewer" {
  project = var.project_id
  role    = "roles/logging.viewer"
  member  = var.observability_viewer_principal
}

resource "google_project_iam_member" "observability_monitoring_viewer" {
  project = var.project_id
  role    = "roles/monitoring.viewer"
  member  = var.observability_viewer_principal
}

resource "google_cloud_run_v2_service_iam_member" "monitoring_readiness_invoker" {
  count    = var.deployment_stage == "service" ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.staff_tracer[0].name
  role     = "roles/run.invoker"
  member   = local.monitoring_service_agent_member
}

resource "google_monitoring_uptime_check_config" "readiness" {
  count        = var.deployment_stage == "service" ? 1 : 0
  project      = var.project_id
  display_name = "Develop private synthetic authenticated readiness"
  period       = "300s"
  timeout      = "10s"

  selected_regions = ["USA"]

  monitored_resource {
    type = "uptime_url"
    labels = {
      host       = local.readiness_uptime_host
      project_id = var.project_id
    }
  }

  http_check {
    request_method = "GET"
    path           = "/readiness"
    port           = 443
    use_ssl        = true
    validate_ssl   = true

    service_agent_authentication {
      type = "OIDC_TOKEN"
    }
  }

  depends_on = [
    google_project_service.approved["monitoring.googleapis.com"],
  ]
}

resource "google_logging_metric" "health_failure_count" {
  project     = var.project_id
  name        = "develop-health-failure-count"
  description = "Counts health endpoint request failures for the private synthetic develop service."
  filter      = "resource.type=\"cloud_run_revision\" AND httpRequest.requestUrl=~\"/health$\" AND httpRequest.status>=500"
}

resource "google_logging_metric" "service_error_count" {
  project     = var.project_id
  name        = "develop-service-error-count"
  description = "Counts non-health request failures for the private synthetic develop service without logging request bodies or SQL values."
  filter      = "resource.type=\"cloud_run_revision\" AND httpRequest.status>=500 AND NOT httpRequest.requestUrl=~\"/(health|readiness)$\""
}

resource "google_monitoring_alert_policy" "health_failures" {
  project               = var.project_id
  display_name          = "Develop private synthetic health failures"
  combiner              = "OR"
  enabled               = true
  notification_channels = [google_monitoring_notification_channel.alerts.name]

  documentation {
    content   = "Health endpoint failures for the private synthetic develop service. Alerts route to the reviewed operator-held notification channel, remain provisional develop review triggers, and follow the represented request-log posture ${local.request_log_posture}."
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Health failure count"

    condition_threshold {
      filter          = "resource.type=\"global\" AND metric.type=\"logging.googleapis.com/user/develop-health-failure-count\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }

      trigger {
        count = 1
      }
    }
  }
}

resource "google_monitoring_alert_policy" "readiness_failures" {
  count                 = var.deployment_stage == "service" ? 1 : 0
  project               = var.project_id
  display_name          = "Develop private synthetic readiness failures"
  combiner              = "OR"
  enabled               = true
  notification_channels = [google_monitoring_notification_channel.alerts.name]

  documentation {
    content   = "Authenticated readiness uptime failures for the private synthetic develop service. Alerts route to the reviewed operator-held notification channel and remain provisional develop review triggers rather than service-level objective or recovery-time commitments."
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Authenticated readiness uptime failure"

    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\" AND metric.label.check_id=\"${google_monitoring_uptime_check_config.readiness[0].uptime_check_id}\""
      duration        = "300s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_NEXT_OLDER"
      }

      trigger {
        count = 1
      }
    }
  }
}

resource "google_monitoring_alert_policy" "service_error_events" {
  project               = var.project_id
  display_name          = "Develop private synthetic service error events"
  combiner              = "OR"
  enabled               = true
  notification_channels = [google_monitoring_notification_channel.alerts.name]

  documentation {
    content   = "Non-health service error events for the private synthetic develop service. Request-body and SQL-value logging remain out of scope; access is restricted to the reviewed observability principal and no broad export sink is modeled."
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Service error event count"

    condition_threshold {
      filter          = "resource.type=\"global\" AND metric.type=\"logging.googleapis.com/user/develop-service-error-count\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }

      trigger {
        count = 1
      }
    }
  }
}
