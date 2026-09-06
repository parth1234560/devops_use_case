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
output "instance_profile_arn" {
  value = module.iam.instance_profile_arn
}

output "instance_profile_name" {
  value = module.iam.instance_profile_name
}