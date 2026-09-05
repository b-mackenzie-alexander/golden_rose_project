resource "google_service_account" "provisioner" {
  project      = var.state_project_id
  account_id   = "golden-rose-provisioner"
  display_name = "Golden Rose provisioner"
  description  = "Provisioning identity that will later own reviewed infrastructure changes through exact GitHub OIDC trust."
}

resource "google_service_account_iam_member" "provisioner_operator_token_creator" {
  service_account_id = google_service_account.provisioner.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = var.provisioner_operator_principal
}

resource "google_service_account" "image_publisher" {
  project      = var.state_project_id
  account_id   = "golden-rose-image-publisher"
  display_name = "Golden Rose image publisher"
  description  = "Image publishing identity kept separate from infrastructure and deployment authority."
}

resource "google_service_account" "artifact_verifier" {
  project      = var.state_project_id
  account_id   = "golden-rose-artifact-verifier"
  display_name = "Golden Rose artifact verifier"
  description  = "Artifact verification identity separate from image publication and deployment authority."
}

resource "google_service_account" "deployer" {
  project      = var.state_project_id
  account_id   = "golden-rose-deployer"
  display_name = "Golden Rose deployer"
  description  = "Deployment identity kept separate from provisioning and image publication authority."
}

resource "google_service_account_iam_member" "image_publisher_wif" {
  service_account_id = google_service_account.image_publisher.name
  role               = "roles/iam.workloadIdentityUser"
  member             = local.build_image_workflow_principal_set
}

resource "google_service_account_iam_member" "artifact_verifier_wif" {
  service_account_id = google_service_account.artifact_verifier.name
  role               = "roles/iam.workloadIdentityUser"
  member             = local.deploy_develop_workflow_principal_set
}

resource "google_service_account_iam_member" "deployer_wif" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = local.deploy_develop_workflow_principal_set
}

locals {
  active_state_bucket_object_admin_principals = concat(
    [
      var.state_authority_principal,
      var.recovery_authority_principal,
    ],
    var.bootstrap_operator_status == "bootstrap-active" ? [var.bootstrap_operator_principal] : [],
  )
}

resource "google_storage_bucket_iam_member" "object_admin" {
  for_each = toset(local.active_state_bucket_object_admin_principals)

  bucket = google_storage_bucket.terraform_state.name
  role   = "roles/storage.objectAdmin"
  member = each.value
}
