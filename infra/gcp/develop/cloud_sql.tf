resource "google_sql_database_instance" "develop" {
  project             = var.project_id
  name                = "develop-postgres"
  region              = var.region
  database_version    = "POSTGRES_16"
  deletion_protection = true

  settings {
    tier      = "db-f1-micro"
    disk_size = 10
    disk_type = "PD_SSD"

    backup_configuration {
      enabled                        = var.cloud_sql_backup_enabled
      start_time                     = var.cloud_sql_backup_start_time
      point_in_time_recovery_enabled = var.cloud_sql_point_in_time_recovery_enabled
      transaction_log_retention_days = var.cloud_sql_transaction_log_retention_days

      backup_retention_settings {
        retained_backups = var.cloud_sql_retained_backups
        retention_unit   = "COUNT"
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.develop.id
    }

    user_labels = merge(
      local.standard_labels,
      {
        recovery_policy_review_status = var.cloud_sql_recovery_policy_review_status
      }
    )
  }

  depends_on = [
    google_project_service.approved["sqladmin.googleapis.com"],
    google_service_networking_connection.private_service_access,
  ]
}

resource "google_sql_database" "application" {
  project  = var.project_id
  name     = var.cloud_sql_database_name
  instance = google_sql_database_instance.develop.name
}
