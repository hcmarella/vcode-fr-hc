# EKS cluster + one managed node group. Autoscaling here is what turns "more
# teams join and push at the same time" from a capacity risk into a knob:
# HPA (see k8s/hpa-*.yaml) scales pod replicas on load, Karpenter/cluster
# autoscaler (enabled via the module's addon below) scales nodes to fit them.
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.31"

  cluster_name    = "${var.project_name}-${var.environment}"
  cluster_version = var.eks_cluster_version

  cluster_endpoint_public_access = true # restrict to your office/VPN CIDR in cluster_endpoint_public_access_cidrs for real prod

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  enable_cluster_creator_admin_permissions = true

  cluster_addons = {
    coredns            = { most_recent = true }
    kube-proxy         = { most_recent = true }
    vpc-cni            = { most_recent = true }
    aws-ebs-csi-driver = { most_recent = true }
  }

  eks_managed_node_groups = {
    default = {
      instance_types = var.eks_node_instance_types
      min_size       = var.eks_node_min_size
      max_size       = var.eks_node_max_size
      desired_size   = var.eks_node_desired_size

      labels = {
        role = "general"
      }
    }
  }

  # IRSA (IAM Roles for Service Accounts) -- lets specific k8s ServiceAccounts
  # assume specific IAM roles (e.g. the worker's SQS access below) without
  # handing broad node-level IAM permissions to every pod on the node.
  enable_irsa = true
}

# --- IRSA role: sync worker -> SQS ---
# The worker pods need to receive/delete messages from the sync queue.
# Scoped to exactly that queue and those two actions, not broad SQS access.
module "worker_irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.44"

  role_name = "${var.project_name}-${var.environment}-worker"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["${var.project_name}:sync-worker"]
    }
  }
}

resource "aws_iam_role_policy" "worker_sqs" {
  name = "${var.project_name}-${var.environment}-worker-sqs"
  role = module.worker_irsa_role.iam_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
      ]
      Resource = aws_sqs_queue.sync_queue.arn
    }]
  })
}

# --- IRSA role: backend API -> SQS (send only, for webhook-triggered enqueue) ---
module "backend_irsa_role" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.44"

  role_name = "${var.project_name}-${var.environment}-backend"

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["${var.project_name}:backend-api"]
    }
  }
}

resource "aws_iam_role_policy" "backend_sqs_send" {
  name = "${var.project_name}-${var.environment}-backend-sqs-send"
  role = module.backend_irsa_role.iam_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:SendMessage"]
      Resource = aws_sqs_queue.sync_queue.arn
    }]
  })
}
