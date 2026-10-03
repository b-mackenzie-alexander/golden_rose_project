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

resource "google_project_iam_member" "database_verifier_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.database_verifier.email}"
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

resource "google_cloud_run_v2_job_iam_member" "deployer_database_authority_job_executor" {
  count    = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.database_authority[0].name
  role     = "roles/run.jobsExecutor"
  member   = "serviceAccount:golden-rose-deployer@${var.control_plane_project_id}.iam.gserviceaccount.com"
}

resource "google_cloud_run_v2_job_iam_member" "deployer_database_authority_job_viewer" {
  count    = var.deployment_stage == "migration" || var.deployment_stage == "service" ? 1 : 0
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.database_authority[0].name
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

resource "google_secret_manager_secret_iam_member" "database_verifier_migration_secret_access" {
  project   = var.project_id
  secret_id = "migration-database-url"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.database_verifier.email}"
}

resource "google_secret_manager_secret_iam_member" "database_verifier_runtime_secret_access" {
  project   = var.project_id
  secret_id = "runtime-database-url"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.database_verifier.email}"
}

resource "google_secret_manager_secret_iam_member" "runtime_synthetic_staff_secret_access" {
  count = var.deployment_stage == "service" && var.runtime_profile == "synthetic_develop_demo" ? 1 : 0

  project   = var.project_id
  secret_id = "synthetic-staff-id"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "runtime_demo_access_secret_access" {
  count = var.deployment_stage == "service" && var.runtime_profile == "synthetic_develop_demo" ? 1 : 0

  project   = var.project_id
  secret_id = "demo-access-password"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"

  depends_on = [google_secret_manager_secret.metadata_only["demo-access-password"]]
}

resource "google_secret_manager_secret_iam_member" "runtime_staff_oidc_issuer_secret_access" {
  count = var.deployment_stage == "service" && var.runtime_profile == "controlled_live_data_staff_pilot" ? 1 : 0

  project   = var.project_id
  secret_id = "staff-oidc-issuer"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"

  depends_on = [data.google_secret_manager_secret.staff_oidc_issuer]
}

resource "google_secret_manager_secret_iam_member" "runtime_staff_oidc_audience_secret_access" {
  count = var.deployment_stage == "service" && var.runtime_profile == "controlled_live_data_staff_pilot" ? 1 : 0

  project   = var.project_id
  secret_id = "staff-oidc-audience"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"

  depends_on = [data.google_secret_manager_secret.staff_oidc_audience]
}

resource "google_secret_manager_secret_iam_member" "runtime_staff_oidc_jwks_url_secret_access" {
  count = var.deployment_stage == "service" && var.runtime_profile == "controlled_live_data_staff_pilot" ? 1 : 0

  project   = var.project_id
  secret_id = "staff-oidc-jwks-url"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"

  depends_on = [data.google_secret_manager_secret.staff_oidc_jwks_url]
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
