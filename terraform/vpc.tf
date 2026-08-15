# Standard 3-tier VPC: public subnets for the ALB, private subnets for EKS
# nodes and RDS. Uses the community module rather than hand-rolled
# route-table wiring -- it's the de facto standard for this exact shape and
# battle-tested across a huge number of EKS deployments, which matters more
# here than the marginal control of writing it by hand.
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.13"

  name = "${var.project_name}-${var.environment}"
  cidr = var.vpc_cidr

  azs              = var.azs
  private_subnets  = [for i, az in var.azs : cidrsubnet(var.vpc_cidr, 4, i)]
  public_subnets   = [for i, az in var.azs : cidrsubnet(var.vpc_cidr, 4, i + 8)]
  database_subnets = [for i, az in var.azs : cidrsubnet(var.vpc_cidr, 4, i + 4)]

  enable_nat_gateway     = true
  single_nat_gateway     = var.environment != "prod" # one NAT for non-prod keeps cost down; prod gets one per AZ below
  one_nat_gateway_per_az = var.environment == "prod"
  enable_dns_hostnames   = true

  create_database_subnet_group = true

  # Required tags for the AWS Load Balancer Controller and EKS to discover
  # these subnets automatically when provisioning ALBs / ENIs.
  public_subnet_tags = {
    "kubernetes.io/role/elb"                                       = "1"
    "kubernetes.io/cluster/${var.project_name}-${var.environment}" = "shared"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"                              = "1"
    "kubernetes.io/cluster/${var.project_name}-${var.environment}" = "shared"
  }
}
