terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.31"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state is required for a team touching this from more than one
  # machine -- local state (the default) has no locking and two people
  # running `apply` at once will corrupt it. Create the bucket/table once by
  # hand (or in a separate bootstrap root) before pointing this at it, then
  # uncomment. Left commented so a first `terraform init` doesn't fail on a
  # bucket that doesn't exist yet.
  #
  # backend "s3" {
  #   bucket         = "vcode-fr-hc-tfstate-<your-account-id>"
  #   key            = "portal/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "vcode-fr-hc-tfstate-lock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "vcode-fr-hc"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
