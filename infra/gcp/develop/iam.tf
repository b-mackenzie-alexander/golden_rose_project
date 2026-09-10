resource "google_project_iam_custom_role" "provisioner_quota_user" {
  project     = var.project_id
  role_id     = "goldenRoseProvisionerQuotaUser"
  title       = "Golden Rose Provisioner Quota User"
  description = "Permits only workload-project quota attribution for the provisioner."
  permissions = ["serviceusage.services.use"]
  stage       = "GA"
}

resource "google_project_iam_member" "provisioner_quota_user" {
  project = var.project_id
  role    = google_project_iam_custom_role.provisioner_quota_user.name
  member  = "serviceAccount:golden-rose-provisioner@${var.control_plane_project_id}.iam.gserviceaccount.com"
}

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

resource "google_secret_manager_secret_iam_member" "runtime_demo_access_secret_access" {
  project   = var.project_id
  secret_id = "demo-access-password"
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

resource "google_artifact_registry_repository_iam_member" "artifact_verifier_reader" {
  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.application_images.repository_id
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:golden-rose-artifact-verifier@${var.control_plane_project_id}.iam.gserviceaccount.com"
}

resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  count    = var.deployment_stage == "service" ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.staff_tracer[0].name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
