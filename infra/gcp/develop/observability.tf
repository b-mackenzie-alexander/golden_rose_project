locals {
  request_log_posture = var.cloud_run_request_log_posture
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

resource "google_logging_metric" "health_failure_count" {
  project     = var.project_id
  name        = "develop-health-failure-count"
  description = "Counts health endpoint request failures for the private synthetic develop service."
  filter      = "resource.type=\"cloud_run_revision\" AND httpRequest.requestUrl=~\"/health$\" AND httpRequest.status>=500"
}

resource "google_logging_metric" "readiness_failure_count" {
  project     = var.project_id
  name        = "develop-readiness-failure-count"
  description = "Counts readiness endpoint request failures for the private synthetic develop service."
  filter      = "resource.type=\"cloud_run_revision\" AND httpRequest.requestUrl=~\"/readiness$\" AND httpRequest.status>=500"
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
    content   = "Health endpoint failures for the private synthetic develop service. Alerts route to the reviewed operator-held notification channel, are not spending caps, and follow the represented request-log posture ${local.request_log_posture}."
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
  project               = var.project_id
  display_name          = "Develop private synthetic readiness failures"
  combiner              = "OR"
  enabled               = true
  notification_channels = [google_monitoring_notification_channel.alerts.name]

  documentation {
    content   = "Readiness endpoint failures for the private synthetic develop service. Alerts route to the reviewed operator-held notification channel and preserve value-safe observability posture ${local.request_log_posture}."
    mime_type = "text/markdown"
  }

  conditions {
    display_name = "Readiness failure count"

    condition_threshold {
      filter          = "resource.type=\"global\" AND metric.type=\"logging.googleapis.com/user/develop-readiness-failure-count\""
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
