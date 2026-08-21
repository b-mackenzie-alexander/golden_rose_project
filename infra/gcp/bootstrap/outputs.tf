output "bootstrap_contract" {
  description = "Value-safe marker that bootstrap state inputs remain operator-held."
  value       = "operator-held-values-required"
}

output "state_backend_type" {
  description = "Value-safe marker for the approved partial backend transport."
  value       = "gcs"
}

output "build_image_workflow_ref" {
  description = "Reviewed exact workflow_ref trusted for image publication."
  value       = local.build_image_workflow_ref
}

output "deploy_develop_workflow_ref" {
  description = "Reviewed exact workflow_ref trusted for deploy execution."
  value       = local.deploy_develop_workflow_ref
}
