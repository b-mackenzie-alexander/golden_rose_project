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

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.develop.id
    }

    user_labels = local.standard_labels
  }

  depends_on = [google_service_networking_connection.private_service_access]
}
