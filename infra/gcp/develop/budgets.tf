resource "google_billing_budget" "develop" {
  billing_account = var.billing_account_id
  display_name    = "Develop private synthetic workload monthly cost guardrail"

  # Budget alerts are not hard spending caps.

  # The Budget API returns project numbers; using IDs causes a perpetual update.
  budget_filter {
    projects = ["projects/${local.canonical_workload_project_number}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = "100"
    }
  }

  threshold_rules {
    threshold_percent = 0.5
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 0.75
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "CURRENT_SPEND"
  }

  all_updates_rule {
    monitoring_notification_channels = [google_monitoring_notification_channel.alerts.name]
    disable_default_iam_recipients   = true
    schema_version                   = "1.0"
  }

  depends_on = [
    google_project_service.approved["billingbudgets.googleapis.com"],
    google_monitoring_notification_channel.alerts,
  ]
}
