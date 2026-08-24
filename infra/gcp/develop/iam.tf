resource "google_project_iam_member" "runtime_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_project_iam_member" "runtime_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_project_iam_member" "runtime_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_project_iam_member" "migration_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.migration.email}"
}

resource "google_project_iam_member" "migration_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.migration.email}"
}

resource "google_project_iam_member" "migration_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.migration.email}"
}

resource "google_cloud_run_v2_job_iam_member" "deployer_jobs_executor" {
  count    = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.migration[0].name
  role     = "roles/run.jobsExecutor"
  member   = "serviceAccount:golden-rose-deployer@${var.control_plane_project_id}.iam.gserviceaccount.com"
}

resource "google_cloud_run_v2_job_iam_member" "deployer_migration_job_viewer" {
  count    = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.migration[0].name
  role     = "roles/run.viewer"
  member   = "serviceAccount:golden-rose-deployer@${var.control_plane_project_id}.iam.gserviceaccount.com"
}

resource "google_cloud_run_v2_service_iam_member" "deployer_staff_service_viewer" {
  count    = var.deployment_stage == "service" ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.staff_tracer[0].name
  role     = "roles/run.viewer"
  member   = "serviceAccount:golden-rose-deployer@${var.control_plane_project_id}.iam.gserviceaccount.com"
}

resource "google_secret_manager_secret_iam_member" "runtime_database_secret_access" {
  project   = var.project_id
  secret_id = "runtime-database-url"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "migration_database_secret_access" {
  project   = var.project_id
  secret_id = "migration-database-url"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.migration.email}"
}

resource "google_secret_manager_secret_iam_member" "runtime_synthetic_staff_secret_access" {
  project   = var.project_id
  secret_id = "synthetic-staff-id"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "migration_synthetic_staff_secret_access" {
  project   = var.project_id
  secret_id = "synthetic-staff-id"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.migration.email}"
}

resource "google_artifact_registry_repository_iam_member" "image_publisher_writer" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.application_images.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:golden-rose-image-publisher@${var.control_plane_project_id}.iam.gserviceaccount.com"
}

data "external" "tester_authority" {
  count   = var.deployment_stage == "service" ? 1 : 0
  program = ["python3", "${path.root}/../../scripts/verify_tester_authority_receipt.py", "--external"]

  query = {
    receipt              = var.tester_authority_receipt_path
    bundle               = var.tester_authority_bundle_path
    certificate_identity = var.tester_authority_certificate_identity
    project_id           = var.project_id
    region               = var.region
    service              = "staff-tracer"
  }
}

resource "google_cloud_run_v2_service_iam_member" "private_invoker" {
  count    = var.deployment_stage == "service" ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.staff_tracer[0].name
  role     = "roles/run.invoker"
  member   = data.external.tester_authority[0].result.private_invoker_principal

  lifecycle {
    precondition {
      condition     = can(regex("^[0-9a-f]{64}$", data.external.tester_authority[0].result.tester_authority_receipt_sha256))
      error_message = "The named tester invoker must be bound to a verified tester-authority receipt SHA-256."
    }
  }
}
