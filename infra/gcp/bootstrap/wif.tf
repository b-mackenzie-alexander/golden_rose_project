locals {
  github_repository_owner               = "b-mackenzie-alexander"
  github_repository_name                = "golden_rose_project"
  github_repository                     = "${local.github_repository_owner}/${local.github_repository_name}"
  github_protected_ref                  = "refs/heads/develop"
  github_deployment_environment         = "develop"
  build_image_workflow_ref              = "${local.github_repository}/.github/workflows/build-image.yml@${local.github_protected_ref}"
  deploy_develop_workflow_ref           = "${local.github_repository}/.github/workflows/deploy-develop.yml@${local.github_protected_ref}"
  build_image_workflow_principal_set    = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.workflow_ref/${local.build_image_workflow_ref}"
  deploy_develop_workflow_principal_set = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.workflow_ref/${local.deploy_develop_workflow_ref}"
}

resource "google_iam_workload_identity_pool" "github" {
  project                   = var.state_project_id
  workload_identity_pool_id = "golden-rose-github"
  display_name              = "Golden Rose GitHub OIDC"
  description               = "Exact GitHub OIDC trust for reviewed develop-environment automation."
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.state_project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "golden-rose-github-provider"
  display_name                       = "Golden Rose GitHub provider"
  description                        = "Rejects pull requests and requires exact repository, ref, and environment claims."

  attribute_mapping = {
    "google.subject"             = "assertion.sub"
    "attribute.repository"       = "assertion.repository"
    "attribute.repository_owner" = "assertion.repository_owner"
    "attribute.ref"              = "assertion.ref"
    "attribute.environment"      = "assertion.environment"
    "attribute.event_name"       = "assertion.event_name"
    "attribute.workflow_ref"     = "assertion.workflow_ref"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }

  attribute_condition = <<-EOT
  attribute.repository == "b-mackenzie-alexander/golden_rose_project" &&
  attribute.repository_owner == "b-mackenzie-alexander" &&
  attribute.ref == "refs/heads/develop" &&
  attribute.environment == "develop" &&
  attribute.event_name == "workflow_dispatch" &&
  (
    attribute.workflow_ref == "b-mackenzie-alexander/golden_rose_project/.github/workflows/build-image.yml@refs/heads/develop" ||
    attribute.workflow_ref == "b-mackenzie-alexander/golden_rose_project/.github/workflows/deploy-develop.yml@refs/heads/develop"
  )
  EOT
}
