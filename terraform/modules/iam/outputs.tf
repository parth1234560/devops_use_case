output "ec2_instance_profile_name" {
  value = aws_iam_instance_profile.ec2.name
}

output "codebuild_role_arn" {
  value = aws_iam_role.codebuild.arn
}

output "codedeploy_role_arn" {
  value = aws_iam_role.codedeploy.arn
}

output "codepipeline_role_arn" {
  value = aws_iam_role.codepipeline.arn
}
