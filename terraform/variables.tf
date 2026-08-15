variable "aws_region" {
  description = "AWS region for all resources."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name, used in resource naming and tags (e.g. staging, prod)."
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Short name prefixed onto resource names."
  type        = string
  default     = "vcode-fr-hc"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC. /16 gives room to grow subnets as team/traffic count increases."
  type        = string
  default     = "10.20.0.0/16"
}

variable "azs" {
  description = "Availability zones to spread subnets across. 3 AZs is the practical minimum for an EKS control plane and RDS Multi-AZ to actually tolerate a zone outage."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "eks_cluster_version" {
  description = "Kubernetes version for the EKS control plane."
  type        = string
  default     = "1.31"
}

variable "eks_node_instance_types" {
  description = "Instance types for the managed node group. Mixed list lets EKS pick whichever is available/cheapest at scale-out time (matters once autoscaling is under real load from multiple teams)."
  type        = list(string)
  default     = ["m6i.large", "m6a.large", "m5.large"]
}

variable "eks_node_min_size" {
  type    = number
  default = 2
}

variable "eks_node_max_size" {
  description = "Ceiling for the node autoscaler. Raise this before raising per-service HPA max replicas, or pods will go Pending with nowhere to schedule."
  type        = number
  default     = 10
}

variable "eks_node_desired_size" {
  type    = number
  default = 2
}

variable "db_instance_class" {
  description = "RDS instance class. db.t4g.medium is a reasonable prototype-to-early-prod size; move to r6g family once Postgres connection count or working-set size (not CPU) becomes the bottleneck -- check pg_stat_activity and buffer cache hit ratio before resizing blind."
  type        = string
  default     = "db.t4g.medium"
}

variable "db_allocated_storage_gb" {
  type    = number
  default = 50
}

variable "db_multi_az" {
  description = "Multi-AZ RDS failover. Doubles storage cost; turn on once this is actually serving users, not while still prototyping."
  type        = bool
  default     = false
}

variable "domain_name" {
  description = "Domain the ALB Ingress will serve (e.g. portal.example.com). Must have a matching ACM certificate in this region -- see acm_certificate_arn."
  type        = string
  default     = ""
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for domain_name, used by the ALB Ingress for TLS termination. Leave blank to deploy without HTTPS (fine for a first smoke test, not for real traffic)."
  type        = string
  default     = ""
}
