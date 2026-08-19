resource "google_service_account" "provisioner" {
  project      = var.state_project_id
  account_id   = "golden-rose-provisioner"
  display_name = "Golden Rose provisioner"
  description  = "Provisioning identity that will later own reviewed infrastructure changes through exact GitHub OIDC trust."
}

resource "google_service_account" "image_publisher" {
  project      = var.state_project_id
  account_id   = "golden-rose-image-publisher"
  display_name = "Golden Rose image publisher"
  description  = "Image publishing identity kept separate from infrastructure and deployment authority."
}

resource "google_service_account" "deployer" {
  project      = var.state_project_id
  account_id   = "golden-rose-deployer"
  display_name = "Golden Rose deployer"
  description  = "Deployment identity kept separate from provisioning and image publication authority."
}

resource "google_service_account_iam_member" "provisioner_wif" {
  service_account_id = google_service_account.provisioner.name
  role               = "roles/iam.workloadIdentityUser"
  member             = local.github_principal_set
}

resource "google_service_account_iam_member" "provisioner_token_creator" {
  service_account_id = google_service_account.provisioner.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = local.github_principal_set
}

resource "google_service_account_iam_member" "image_publisher_wif" {
  service_account_id = google_service_account.image_publisher.name
  role               = "roles/iam.workloadIdentityUser"
  member             = local.github_principal_set
}

resource "google_service_account_iam_member" "image_publisher_token_creator" {
  service_account_id = google_service_account.image_publisher.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = local.github_principal_set
}

resource "google_service_account_iam_member" "deployer_wif" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = local.github_principal_set
}

resource "google_service_account_iam_member" "deployer_token_creator" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = local.github_principal_set
}

resource "google_storage_bucket_iam_member" "state_authority_object_admin" {
  bucket = google_storage_bucket.terraform_state.name
  role   = "roles/storage.objectAdmin"
  member = var.state_authority_principal
}

resource "google_storage_bucket_iam_member" "recovery_authority_object_admin" {
  bucket = google_storage_bucket.terraform_state.name
  role   = "roles/storage.objectAdmin"
  member = var.recovery_authority_principal
}

resource "google_storage_bucket_iam_member" "bootstrap_operator_object_admin" {
  count  = var.bootstrap_operator_status == "bootstrap-active" ? 1 : 0
  bucket = google_storage_bucket.terraform_state.name
  role   = "roles/storage.objectAdmin"
  member = var.bootstrap_operator_principal
}
