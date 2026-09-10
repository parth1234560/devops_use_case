output "vpc_id" {
  value = module.networking.vpc_id
}

output "public_subnet_ids" {
  value = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  value = module.networking.private_subnet_ids
}

output "alb_sg_id" {
  value = module.networking.alb_sg_id
}

output "ec2_sg_id" {
  value = module.networking.ec2_sg_id
}

output "rds_sg_id" {
  value = module.networking.rds_sg_id
}
//iam outputs
output "ec2_instance_profile_name" {
  value = module.iam.ec2_instance_profile_name
}

output "codebuild_role_arn" {
  value = module.iam.codebuild_role_arn
}

output "codedeploy_role_arn" {
  value = module.iam.codedeploy_role_arn
}

output "codepipeline_role_arn" {
  value = module.iam.codepipeline_role_arn
}
