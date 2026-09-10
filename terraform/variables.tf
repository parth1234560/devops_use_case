variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "project_name" {
  type    = string
  default = "aws-ha-app"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type = list(string)
  default = [
    "10.0.1.0/24",
    "10.0.2.0/24"
  ]
}

variable "private_subnet_cidrs" {
  type = list(string)
  default = [
    "10.0.11.0/24",
    "10.0.12.0/24"
  ]
}

variable "app_port" {
  type    = number
  default = 8080
}

variable "db_port" {
  type    = number
  default = 3306
}
variable "alarm_email" {
  type        = string
  description = "Email address for CloudWatch alarm notifications"
}
variable "github_connection_arn" {
  type        = string
  description = "AWS CodeConnections ARN for GitHub"
}

variable "github_repository" {
  type        = string
  description = "GitHub repository in owner/repository format"
}

variable "github_branch" {
  type    = string
  default = "main"
}