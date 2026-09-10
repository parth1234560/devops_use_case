output "db_instance_endpoint" {
  value = aws_db_instance.mysql.address
}

output "db_instance_port" {
  value = aws_db_instance.mysql.port
}

output "db_name" {
  value = aws_db_instance.mysql.db_name
}

output "db_secret_arn" {
  value = aws_secretsmanager_secret.db.arn
}

output "db_instance_identifier" {
  value = aws_db_instance.mysql.identifier
}