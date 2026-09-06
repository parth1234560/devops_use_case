module "networking" {
  source = "./modules/networking"

  project_name         = var.project_name
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  app_port             = var.app_port
  db_port              = var.db_port
}
module "iam" {
  source = "./modules/iam"

  project_name = var.project_name
}