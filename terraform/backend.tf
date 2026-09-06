terraform {
  required_version = ">= 1.10.0"

  backend "s3" {
    bucket       = "aws-ha-app-terraform-state-parth"
    key          = "aws-ha-app/terraform.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }
}