variable "state_project_id" {
  description = "Lifecycle-independent GCP project identifier supplied out of band for the durable Terraform state bucket."
  type        = string
  nullable    = false
}

variable "state_bucket_location" {
  description = "Operator-supplied GCS location for the durable Terraform state bucket."
  type        = string
  nullable    = false
}

variable "state_bucket_name" {
  description = "Operator-supplied globally unique name for the durable Terraform state bucket."
  type        = string
  nullable    = false
}

variable "bootstrap_operator_principal" {
  description = "Operator-supplied human bootstrap principal for the one-time local bootstrap and later authority retirement ceremony."
  type        = string
  nullable    = false
}

variable "provisioner_operator_principal" {
  description = "Operator-held named human principal permitted to mint short-lived provisioner tokens for separately approved local Terraform operations."
  type        = string
  nullable    = false

  validation {
    condition     = startswith(var.provisioner_operator_principal, "user:") && can(regex("^user:[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.provisioner_operator_principal))
    error_message = "The provisioner operator principal must be one named user supplied out of band."
  }
}

variable "bootstrap_operator_status" {
  description = "Reviewed transition marker: bootstrap-active permits the bootstrap operator on the state bucket; bootstrap-retired removes that temporary authority."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["bootstrap-active", "bootstrap-retired"], var.bootstrap_operator_status)
    error_message = "Bootstrap operator status must be bootstrap-active or bootstrap-retired."
  }
}

variable "state_authority_principal" {
  description = "Reviewed later Terraform state authority principal for bucket-level state object access."
  type        = string
  nullable    = false
}

variable "recovery_authority_principal" {
  description = "Reviewed named recovery authority principal for bounded bucket-level state object recovery access."
  type        = string
  nullable    = false
}
