resource "google_compute_network" "develop" {
  project                         = var.project_id
  name                            = "develop-vpc"
  auto_create_subnetworks         = false
  delete_default_routes_on_create = true

  depends_on = [google_project_service.approved["compute.googleapis.com"]]
}

resource "google_compute_subnetwork" "direct_vpc" {
  project       = var.project_id
  name          = "develop-direct-vpc"
  region        = var.region
  ip_cidr_range = var.direct_vpc_subnet_cidr
  network       = google_compute_network.develop.id

  depends_on = [google_project_service.approved["compute.googleapis.com"]]
}

resource "google_compute_global_address" "private_service_access" {
  project       = var.project_id
  name          = "develop-private-service-access"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.develop.id

  depends_on = [google_project_service.approved["compute.googleapis.com"]]
}

resource "google_service_networking_connection" "private_service_access" {
  network                 = google_compute_network.develop.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_service_access.name]

  depends_on = [google_project_service.approved["servicenetworking.googleapis.com"]]
}
