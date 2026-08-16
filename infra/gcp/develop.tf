module "develop" {
  source = "./develop"

  project_id             = var.project_id
  region                 = var.region
  container_image_digest = var.container_image_digest
  direct_vpc_subnet_cidr = var.direct_vpc_subnet_cidr
}
