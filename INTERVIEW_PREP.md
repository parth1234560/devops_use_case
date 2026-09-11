# What To Learn Before Presenting This Project In An Interview

Use this file as your interview preparation checklist.

## 1. Explain The Project In 60 Seconds

Practice saying:

> This project provisions a highly available AWS todo web application using Terraform. The application runs on private EC2 instances behind a public Application Load Balancer. It stores todo data in a Multi-AZ MySQL RDS database. Deployments are automated through CodePipeline, CodeBuild, and CodeDeploy blue-green deployments. EC2 instances are accessed securely using SSM instead of SSH.

## 2. Know The Architecture

Be able to explain these components:

- VPC
- public subnets
- private subnets
- internet gateway
- NAT gateway
- route tables
- security groups
- ALB
- Auto Scaling Group
- launch template
- EC2 instance profile
- RDS subnet group
- Multi-AZ RDS
- Secrets Manager
- CodePipeline
- CodeBuild
- CodeDeploy
- S3 artifact bucket
- CloudWatch alarms

## 3. Understand Public vs Private Subnets

Public subnet:

- has route to internet gateway
- hosts the ALB and NAT Gateway

Private subnet:

- does not expose instances directly to internet
- hosts EC2 app servers and RDS
- uses NAT Gateway for outbound access

Interview line:

> The EC2 instances and RDS database are private. Only the ALB is public. This reduces attack surface.

## 4. Understand ALB Flow

Request path:

```text
User Browser
  -> Public ALB
  -> Target Group
  -> Private EC2 on port 8080
  -> Python Todo App
  -> RDS MySQL
```

Know that users do not hit EC2 directly.

## 5. Understand Security Groups

Explain:

- ALB security group allows HTTP from internet.
- EC2 security group allows app port only from ALB security group.
- RDS security group allows MySQL only from EC2 security group.

This is security group referencing, not wide-open access.

## 6. Understand SSM Instead Of SSH

You should say:

> I did not expose SSH. EC2 instances are private and accessed using AWS Systems Manager Session Manager through IAM permissions.

Know commands:

```powershell
aws ssm describe-instance-information --region ap-south-1
aws ssm start-session --target INSTANCE_ID --region ap-south-1
```

## 7. Understand CodePipeline

Pipeline stages:

1. Source: GitHub through CodeConnections
2. Build: CodeBuild packages the app
3. Deploy: CodeDeploy deploys to EC2 Auto Scaling Group

Know why CodeBuild exists:

- runs `buildspec.yml`
- prepares deployment artifact
- sends artifact to CodePipeline

## 8. Understand CodeDeploy AppSpec

`appspec.yml` tells CodeDeploy:

- what files to copy
- where to copy them
- which lifecycle scripts to run

Lifecycle hooks used:

- ApplicationStop
- BeforeInstall
- AfterInstall
- ApplicationStart
- ValidateService

For blue-green, you also saw:

- BeforeAllowTraffic
- AllowTraffic
- AfterAllowTraffic
- BeforeBlockTraffic
- BlockTraffic
- AfterBlockTraffic

## 9. Understand Blue-Green Deployment

Be ready to explain:

> In blue-green deployment, the current environment is blue. CodeDeploy creates a replacement green Auto Scaling Group, deploys the new app version there, validates health checks, shifts ALB traffic to green, and then terminates blue after a wait period.

Benefits:

- safer deployments
- rollback support
- less downtime
- traffic only shifts after health checks pass

## 10. Understand RDS Multi-AZ

Important:

- Multi-AZ is for high availability.
- It creates a standby in another Availability Zone.
- It is not a read replica for scaling reads.
- AWS automatically fails over to standby if primary fails.

Interview line:

> Multi-AZ RDS provides automatic failover, not read scaling. For read scaling, I would add read replicas.

## 11. Understand Backups

Your RDS has:

- automated backups with 7-day retention
- final snapshot enabled
- deletion protection enabled

Know the difference:

- automated backups support point-in-time recovery
- snapshots are manual/final restore points
- deletion protection prevents accidental DB deletion

## 12. Understand Secrets Manager

The DB password is not hardcoded in the app.

The app:

- reads credentials from Secrets Manager
- discovers RDS endpoint with AWS API
- connects to MySQL

## 13. Understand The Todo App

Frontend:

- served from `/`
- HTML/CSS/JavaScript
- lets users create, complete, and delete todos

Backend:

- Python HTTP server
- API endpoints:
  - `/api/health`
  - `/api/todos`
  - `/api/todos/{id}`

Database:

- MySQL table `todos`
- stores title, notes, completion status, timestamps

## 14. Know Debugging Commands

Pipeline:

```powershell
aws codepipeline get-pipeline-state --name aws-ha-app-pipeline --region ap-south-1
```

Deployments:

```powershell
aws deploy list-deployments --application-name aws-ha-app --deployment-group-name aws-ha-app-deployment-group --region ap-south-1
aws deploy get-deployment --deployment-id DEPLOYMENT_ID --region ap-south-1
aws deploy get-deployment-instance --deployment-id DEPLOYMENT_ID --instance-id INSTANCE_ID --region ap-south-1
```

ALB:

```powershell
Invoke-WebRequest "http://ALB_DNS_NAME/health" -UseBasicParsing
Invoke-WebRequest "http://ALB_DNS_NAME/api/health" -UseBasicParsing
```

EC2:

```bash
sudo systemctl status aws-ha-app --no-pager
sudo tail -n 100 /var/log/aws-ha-app.log
sudo tail -n 100 /var/log/aws/codedeploy-agent/codedeploy-agent.log
```

## 15. Be Ready To Explain Problems You Solved

Good interview stories:

- CodeDeploy artifact was packaged incorrectly.
- EC2 instances were private, so SSH was not possible.
- SSM plugin was missing locally.
- CodeDeploy agent was not connected.
- Blue-green needed extra IAM permissions.
- App dependency installation had to happen after CodeDeploy copied files.
- Health validation needed retries because app startup can take time.
- Stale blue-green ASGs caused mixed ALB traffic.

## 16. Improvements To Mention

If asked what you would improve:

- use HTTPS with ACM certificate
- add Route 53 custom domain
- store static frontend in S3/CloudFront
- use a framework like FastAPI or Flask
- add database migrations
- add unit/integration tests
- add WAF
- add VPC endpoints for S3, SSM, Secrets Manager, RDS API
- add centralized structured logging
- use Terraform remote state locking and stricter state management
- add read replicas if read scaling is needed
- add alarms for CodeDeploy failures

## 17. Short Closing Pitch

Say:

> This project demonstrates infrastructure provisioning, secure private networking, CI/CD automation, blue-green deployment, application health validation, and persistent database-backed application design on AWS.
