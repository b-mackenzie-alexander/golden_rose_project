resource "google_service_account" "runtime" {
  project      = var.project_id
  account_id   = "staff-tracer-runtime"
  display_name = "Develop staff tracer runtime"
  description  = "Runtime identity for the private synthetic develop Cloud Run service."
}

resource "google_service_account" "migration" {
  project      = var.project_id
  account_id   = "staff-tracer-migration"
  display_name = "Develop staff tracer migration job"
  description  = "Migration job identity for private synthetic develop database changes."
}
