output "codebuild_project_name" {
  value = aws_codebuild_project.app.name
}

output "codedeploy_application_name" {
  value = aws_codedeploy_app.app.name
}

output "codedeploy_deployment_group_name" {
  value = aws_codedeploy_deployment_group.app.deployment_group_name
}

output "codepipeline_name" {
  value = aws_codepipeline.app.name
}
