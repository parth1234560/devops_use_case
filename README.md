# AWS HA App With Terraform, CodePipeline, and CodeDeploy Blue-Green

This project provisions a highly available AWS demo application using Terraform.
It creates a custom VPC, public subnets for an Application Load Balancer, private
subnets for EC2 and RDS, an Auto Scaling Group, Multi-AZ MySQL RDS, and a CI/CD
pipeline using CodePipeline, CodeBuild, and CodeDeploy blue-green deployments.

## Application

The app is a Python todo-list website located in `app/app.py`. It serves both
the frontend and backend from the same EC2-hosted service.

It runs on EC2 instances on port `8080` and exposes:

- `/` - the todo website frontend.
- `/health` - returns `OK` for ALB and CodeDeploy health validation.
- `/api/health` - verifies the app can query RDS.
- `/api/todos` - lists and creates todos.
- `/api/todos/{id}` - updates or deletes a todo.

The app is installed as a systemd service named:

```bash
aws-ha-app
```

## How To Access The App

The EC2 instances are private, so users do not access them directly from the
internet. Access goes through the public Application Load Balancer.

From the `terraform/` directory:

```powershell
terraform output -raw alb_dns_name
```

Health check through the ALB:

```powershell
Invoke-WebRequest "http://$(terraform output -raw alb_dns_name)/health" -UseBasicParsing
```

Expected result:

```text
StatusCode : 200
Content    : OK
```

Root endpoint:

```powershell
Invoke-WebRequest "http://$(terraform output -raw alb_dns_name)/" -UseBasicParsing
```

Open the ALB DNS name in a browser to use the todo website:

```text
http://ALB_DNS_NAME/
```

## EC2 Access

EC2 instances are launched in private subnets without public IP addresses. Use
AWS Systems Manager Session Manager instead of SSH.

List online managed instances:

```powershell
aws ssm describe-instance-information --region ap-south-1 --query "InstanceInformationList[?PingStatus=='Online'].{Id:InstanceId,IP:IPAddress}" --output table
```

Start a session:

```powershell
aws ssm start-session --target INSTANCE_ID --region ap-south-1
```

Inside the instance:

```bash
sudo systemctl status aws-ha-app --no-pager
curl -f http://localhost:8080/health
```

## CI/CD

The pipeline has three stages:

1. Source - pulls from GitHub using CodeStar/CodeConnections.
2. Build - CodeBuild packages the contents of the `app/` directory.
3. Deploy - CodeDeploy deploys to the Auto Scaling Group.

Check pipeline state:

```powershell
aws codepipeline get-pipeline-state --name aws-ha-app-pipeline --region ap-south-1 --query "stageStates[].{Stage:stageName,Status:latestExecution.status}" --output table
```

Start a new pipeline execution:

```powershell
aws codepipeline start-pipeline-execution --name aws-ha-app-pipeline --region ap-south-1
```

## Blue-Green Deployment

CodeDeploy is configured for blue-green deployments:

- Deployment type: `BLUE_GREEN`
- Deployment option: `WITH_TRAFFIC_CONTROL`
- Green fleet provisioning: `COPY_AUTO_SCALING_GROUP`
- Traffic shifting: via the ALB target group
- Old blue instances: terminated after 5 minutes

Verify deployment group configuration:

```powershell
aws deploy get-deployment-group --application-name aws-ha-app --deployment-group-name aws-ha-app-deployment-group --region ap-south-1 --query "deploymentGroupInfo.{Type:deploymentStyle.deploymentType,Option:deploymentStyle.deploymentOption,BlueGreen:blueGreenDeploymentConfiguration,LoadBalancer:loadBalancerInfo}" --output json
```

Watch latest deployment:

```powershell
$DEPLOY = aws deploy list-deployments --application-name aws-ha-app --deployment-group-name aws-ha-app-deployment-group --region ap-south-1 --query "deployments[0]" --output text

aws deploy get-deployment --deployment-id $DEPLOY --region ap-south-1 --query "deploymentInfo.{Status:status,Error:errorInformation,Overview:deploymentOverview}" --output json
```

During blue-green deployment, a temporary CodeDeploy Auto Scaling Group appears.

```powershell
aws autoscaling describe-auto-scaling-groups --region ap-south-1 --query "AutoScalingGroups[?contains(AutoScalingGroupName, 'aws-ha-app')].{Name:AutoScalingGroupName,Desired:DesiredCapacity,Instances:length(Instances)}" --output table
```

## RDS

The project provisions a private MySQL RDS instance in `terraform/modules/database`.

Important settings:

- Engine: MySQL 8.0
- Public access: disabled
- Subnets: private subnets
- Storage encryption: enabled
- Multi-AZ: enabled with `multi_az = true`
- Automated backup retention: 7 days by default
- Final snapshot: enabled on destroy
- Deletion protection: enabled

Multi-AZ RDS does not create a normal read replica for application reads. It
creates a synchronous standby instance in another Availability Zone for high
availability and failover. The standby is managed by AWS and is not used as a
read endpoint.

Backups are enabled through:

```hcl
backup_retention_period = 7
```

Terraform also configures:

```hcl
skip_final_snapshot       = false
final_snapshot_identifier = "aws-ha-app-mysql-final"
copy_tags_to_snapshot     = true
```

So the database has automated backups, and Terraform requires a final snapshot
when the DB is destroyed. Because deletion protection is enabled, disable
deletion protection first if you intentionally want to destroy the RDS instance.

## Todo Data Flow

The todo app stores data in the RDS MySQL database. On startup, the app:

1. Reads database credentials from AWS Secrets Manager.
2. Discovers the RDS endpoint using `rds:DescribeDBInstances`.
3. Connects to MySQL using PyMySQL.
4. Creates the `todos` table if it does not exist.

Todo records include:

- `id`
- `title`
- `notes`
- `completed`
- `created_at`
- `updated_at`

Because RDS is Multi-AZ, the data is stored in a highly available database
deployment with automatic failover to a standby Availability Zone.

## Cleanup

When the demo is complete, destroy resources to avoid AWS charges:

```powershell
terraform destroy
```

If RDS deletion protection is enabled, Terraform will not delete the DB until
deletion protection is disabled.
