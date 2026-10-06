resource "google_service_account" "runtime" {
  project      = var.project_id
  account_id   = "staff-tracer-runtime"
  display_name = "Develop staff tracer runtime"
  description  = "Runtime identity for the private synthetic develop Cloud Run service."

  depends_on = [google_project_service.approved["iam.googleapis.com"]]
}

resource "google_service_account" "migration" {
  project      = var.project_id
  account_id   = "staff-tracer-migration"
  display_name = "Develop staff tracer migration job"
  description  = "Migration job identity for private synthetic develop database changes."

  depends_on = [google_project_service.approved["iam.googleapis.com"]]
}

resource "google_service_account" "database_verifier" {
  project      = var.project_id
  account_id   = "staff-tracer-database-verifier"
  display_name = "Develop database authority verifier"
  description  = "One-task verifier identity with only private database probe and bounded log authority."

  depends_on = [google_project_service.approved["iam.googleapis.com"]]
}

resource "google_service_account" "staff_bootstrap" {
  project      = var.project_id
  account_id   = "staff-tracer-staff-bootstrap"
  display_name = "Develop first staff account bootstrap"
  description  = "One-task bootstrap identity for the first named staff pilot account through private Cloud SQL."

  depends_on = [google_project_service.approved["iam.googleapis.com"]]
}
