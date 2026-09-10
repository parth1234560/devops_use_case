terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    random = {
      source = "hashicorp/random"
    }
  }
}
module "networking" {
  source = "./modules/networking"

  project_name         = var.project_name
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  app_port             = var.app_port
  db_port              = var.db_port
}
module "cicd" {
  source = "./modules/cicd"

  project_name = var.project_name

  github_connection_arn = var.github_connection_arn
  github_repository     = var.github_repository
  github_branch         = var.github_branch

  codebuild_role_arn    = module.iam.codebuild_role_arn
  codedeploy_role_arn   = module.iam.codedeploy_role_arn
  codepipeline_role_arn = module.iam.codepipeline_role_arn

  asg_name             = module.compute.asg_name
  artifact_bucket_name = module.artifacts.bucket_name

}
module "artifacts" {
  source = "./modules/artifacts"

  project_name = var.project_name
}
module "iam" {
  source = "./modules/iam"

  project_name = var.project_name
  # These two will be connected when we create
  # the artifact bucket and DB secret.
  artifact_bucket_arn   = module.artifacts.bucket_arn
  db_secret_arn         = module.database.db_secret_arn
  github_connection_arn = var.github_connection_arn
}

module "compute" {
  source = "./modules/compute"

  project_name = var.project_name

  vpc_id             = module.networking.vpc_id
  public_subnet_ids  = module.networking.public_subnet_ids
  private_subnet_ids = module.networking.private_subnet_ids

  alb_sg_id = module.networking.alb_sg_id
  ec2_sg_id = module.networking.ec2_sg_id

  ec2_instance_profile_name = module.iam.ec2_instance_profile_name

  app_port = var.app_port
}
module "database" {
  source = "./modules/database"

  project_name = var.project_name

  private_subnet_ids = module.networking.private_subnet_ids
  rds_sg_id          = module.networking.rds_sg_id
}
module "monitoring" {
  source = "./modules/monitoring"

  project_name = var.project_name

  alarm_email = var.alarm_email

  alb_arn_suffix          = module.compute.alb_arn_suffix
  target_group_arn_suffix = module.compute.target_group_arn_suffix

  asg_name                = module.compute.asg_name
  rds_instance_identifier = module.database.db_instance_identifier
}