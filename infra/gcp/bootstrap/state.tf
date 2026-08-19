resource "google_storage_bucket" "terraform_state" {
  project                     = var.state_project_id
  name                        = var.state_bucket_name
  location                    = var.state_bucket_location
  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  versioning {
    enabled = true
  }

  retention_policy {
    retention_period = 604800
    is_locked        = false
  }

  lifecycle {
    prevent_destroy = true
  }
}
