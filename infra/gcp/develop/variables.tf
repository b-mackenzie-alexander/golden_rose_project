variable "project_id" {
  description = "GCP project identifier supplied by the root module."
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
  description = "Immutable Artifact Registry image reference supplied by the root module."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("@sha256:[0-9a-f]{64}$", var.container_image_digest))
    error_message = "The container image must be pinned by immutable sha256 digest."
  }
}
