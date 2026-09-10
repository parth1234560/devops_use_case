resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts"

  tags = {
    Name    = "${var.project_name}-alerts"
    Project = var.project_name
  }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}


# -------------------------
# ALB Target 5XX
# -------------------------

resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${var.project_name}-alb-5xx"
  alarm_description   = "ALB target 5XX errors are high"
  comparison_operator = "GreaterThanThreshold"

  evaluation_periods = 2
  period             = 300
  threshold          = 5

  metric_name = "HTTPCode_Target_5XX_Count"
  namespace   = "AWS/ApplicationELB"
  statistic   = "Sum"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}


# -------------------------
# ALB Unhealthy Hosts
# -------------------------

resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_hosts" {
  alarm_name          = "${var.project_name}-alb-unhealthy-hosts"
  alarm_description   = "ALB has unhealthy targets"
  comparison_operator = "GreaterThanThreshold"

  evaluation_periods = 2
  period             = 300
  threshold          = 0

  metric_name = "UnHealthyHostCount"
  namespace   = "AWS/ApplicationELB"
  statistic   = "Average"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.target_group_arn_suffix
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}


# -------------------------
# EC2 CPU
# -------------------------

resource "aws_cloudwatch_metric_alarm" "ec2_cpu" {
  alarm_name          = "${var.project_name}-ec2-cpu"
  alarm_description   = "EC2 CPU utilization is high"
  comparison_operator = "GreaterThanThreshold"

  evaluation_periods = 2
  period             = 300
  threshold          = 80

  metric_name = "CPUUtilization"
  namespace   = "AWS/EC2"
  statistic   = "Average"

  dimensions = {
    AutoScalingGroupName = var.asg_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}


# -------------------------
# ASG Capacity
# -------------------------

resource "aws_cloudwatch_metric_alarm" "asg_capacity" {
  alarm_name          = "${var.project_name}-asg-capacity"
  alarm_description   = "ASG is running at maximum capacity"
  comparison_operator = "GreaterThanOrEqualToThreshold"

  evaluation_periods = 2
  period             = 300
  threshold          = 4

  metric_name = "GroupInServiceInstances"
  namespace   = "AWS/AutoScaling"
  statistic   = "Average"

  dimensions = {
    AutoScalingGroupName = var.asg_name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}


# -------------------------
# RDS CPU
# -------------------------

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.project_name}-rds-cpu"
  alarm_description   = "RDS CPU utilization is high"
  comparison_operator = "GreaterThanThreshold"

  evaluation_periods = 2
  period             = 300
  threshold          = 80

  metric_name = "CPUUtilization"
  namespace   = "AWS/RDS"
  statistic   = "Average"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_identifier
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}


# -------------------------
# RDS Free Storage
# -------------------------

resource "aws_cloudwatch_metric_alarm" "rds_free_storage" {
  alarm_name          = "${var.project_name}-rds-free-storage"
  alarm_description   = "RDS free storage is low"
  comparison_operator = "LessThanThreshold"

  evaluation_periods = 2
  period             = 300

  # 5 GB in bytes
  threshold = 5368709120

  metric_name = "FreeStorageSpace"
  namespace   = "AWS/RDS"
  statistic   = "Average"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_identifier
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}


# -------------------------
# RDS Connections
# -------------------------

resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  alarm_name          = "${var.project_name}-rds-connections"
  alarm_description   = "RDS database connections are high"
  comparison_operator = "GreaterThanThreshold"

  evaluation_periods = 2
  period             = 300
  threshold          = 80

  metric_name = "DatabaseConnections"
  namespace   = "AWS/RDS"
  statistic   = "Average"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_identifier
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}