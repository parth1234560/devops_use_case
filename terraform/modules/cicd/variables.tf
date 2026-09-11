variable "project_name" {
  type = string
}
variable "artifact_bucket_name" {
  type = string
}
variable "github_connection_arn" {
  type = string
}

variable "github_repository" {
  type = string
}

variable "github_branch" {
  type    = string
  default = "main"
}

variable "codebuild_role_arn" {
  type = string
}

variable "codedeploy_role_arn" {
  type = string
}

variable "codepipeline_role_arn" {
  type = string
}

variable "asg_name" {
  type = string
}
variable "target_group_name" {
  type = string
}