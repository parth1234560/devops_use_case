resource "random_password" "db" {
  length           = 24
  special          = true
  override_special = "!#$%&*+-.:;<=>?^_`~"
}
resource "aws_secretsmanager_secret" "db" {
  name = "${var.project_name}/database"

  tags = {
    Name    = "${var.project_name}-database-secret"
    Project = var.project_name
  }
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id

  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db.result
    db_name  = var.db_name
  })
}

resource "aws_db_subnet_group" "main" {
  name = "${var.project_name}-db-subnet-group"

  subnet_ids = var.private_subnet_ids

  tags = {
    Name    = "${var.project_name}-db-subnet-group"
    Project = var.project_name
  }
}

resource "aws_db_instance" "mysql" {
  identifier = "${var.project_name}-mysql"

  engine         = "mysql"
  engine_version = "8.0"

  instance_class = var.db_instance_class

  allocated_storage = var.allocated_storage
  storage_type      = "gp3"

  storage_encrypted = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result

  port = 3306

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.rds_sg_id]

  publicly_accessible = false

  multi_az = true

  backup_retention_period = var.backup_retention_period

  backup_window      = "18:00-19:00"
  maintenance_window = "sun:19:00-sun:20:00"

  deletion_protection = true

  skip_final_snapshot = false

  final_snapshot_identifier = "${var.project_name}-mysql-final"

  copy_tags_to_snapshot = true

  auto_minor_version_upgrade = true

  tags = {
    Name    = "${var.project_name}-mysql"
    Project = var.project_name
  }
}