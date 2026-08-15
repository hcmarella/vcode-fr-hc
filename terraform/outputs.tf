output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "configure_kubectl" {
  description = "Run this after apply to point kubectl at the new cluster."
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "ecr_backend_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_repository_url" {
  value = aws_ecr_repository.frontend.repository_url
}

output "rds_endpoint" {
  value     = aws_db_instance.portal.endpoint
  sensitive = true
}

output "sync_queue_url" {
  value = aws_sqs_queue.sync_queue.url
}

output "worker_irsa_role_arn" {
  description = "Annotate the sync-worker k8s ServiceAccount with this (see k8s/serviceaccounts.yaml)."
  value       = module.worker_irsa_role.iam_role_arn
}

output "backend_irsa_role_arn" {
  description = "Annotate the backend-api k8s ServiceAccount with this (see k8s/serviceaccounts.yaml)."
  value       = module.backend_irsa_role.iam_role_arn
}
