locals {
  standard_labels = {
    environment   = "develop"
    data_boundary = "fictional-synthetic-only"
    managed_by    = "terraform"
    service       = "staff-tracer"
    cost_center   = "develop"
    owner         = "technical-owner"
    teardown      = "intentional-runbook-only"
  }
}
