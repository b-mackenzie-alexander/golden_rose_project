locals {
  standard_labels = {
    environment   = "develop"
    data_boundary = var.runtime_profile == "controlled_live_data_staff_pilot" ? "controlled-live-data-staff-pilot" : "fictional-synthetic-only"
    managed_by    = "terraform"
    service       = "staff-tracer"
    cost_center   = "develop"
    owner         = "technical-owner"
    teardown      = "intentional-runbook-only"
  }
}
