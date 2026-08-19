output "environment" {
  description = "Value-safe environment marker."
  value       = "develop"
}

output "data_boundary" {
  description = "Value-safe data-boundary marker."
  value       = "fictional-synthetic-only"
}

output "database_contract" {
  description = "Sensitive minimal database metadata and reviewed role identifiers for the private synthetic develop environment."
  value       = module.develop.database_contract
  sensitive   = true
}

output "database_recovery_contract" {
  description = "Sensitive reviewed database recovery-input contract pending later gate approval."
  value       = module.develop.database_recovery_contract
  sensitive   = true
}

output "cost_guardrail_contract" {
  description = "Value-safe reviewed cost-guardrail contract for the private synthetic develop environment."
  value       = module.develop.cost_guardrail_contract
}

output "observability_contract" {
  description = "Value-safe reviewed observability contract for the private synthetic develop environment."
  value       = module.develop.observability_contract
}
