output "bootstrap_contract" {
  description = "Value-safe marker that bootstrap state inputs remain operator-held."
  value       = "operator-held-values-required"
}

output "state_backend_type" {
  description = "Value-safe marker for the approved partial backend transport."
  value       = "gcs"
}
