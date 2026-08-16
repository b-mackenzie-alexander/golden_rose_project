variable "project_id" {
  description = "GCP project identifier supplied out of band for local validation or approved provisioning."
  type        = string
  nullable    = false
}

variable "region" {
  description = "Approved GCP region for the private synthetic develop environment."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["us-east4"], var.region)
    error_message = "The develop environment is currently approved only for us-east4."
  }
}

variable "container_image_digest" {
  description = "Immutable sha256 digest supplied out of band for the managed Artifact Registry staff-tracer image."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("sha256:[0-9a-f]{64}$", var.container_image_digest))
    error_message = "The container image input must be only a sha256 digest for the managed Artifact Registry image authority."
  }
}

variable "direct_vpc_subnet_cidr" {
  description = "RFC1918 /26-or-broader subnet CIDR reserved out of band for Direct VPC egress and private service access validation."
  type        = string
  nullable    = false

  validation {
    condition = can(cidrnetmask(var.direct_vpc_subnet_cidr)) && can(regex(
      "^(10\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])/(8|9|1[0-9]|2[0-6])|172\\.(1[6-9]|2[0-9]|3[0-1])\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])/(1[2-9]|2[0-6])|192\\.168\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\\.(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])/(1[6-9]|2[0-6]))$",
      var.direct_vpc_subnet_cidr
    )) && cidrhost(var.direct_vpc_subnet_cidr, 0) == split("/", var.direct_vpc_subnet_cidr)[0]
    error_message = "The Direct VPC subnet CIDR must be an RFC1918 /26-or-broader range supplied out of band."
  }
}
