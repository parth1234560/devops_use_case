# What You Did In This Project

This file summarizes your role and the hands-on work you performed.

## 1. Built And Operated The AWS Infrastructure

You worked with a Terraform project that provisions:

- VPC
- public subnets
- private subnets
- route tables
- internet gateway
- NAT gateway
- security groups
- Application Load Balancer
- Auto Scaling Group
- EC2 launch template
- RDS MySQL
- IAM roles
- CodePipeline
- CodeBuild
- CodeDeploy
- CloudWatch monitoring

## 2. Ran Terraform

You applied Terraform changes and verified infrastructure updates.

Important commands you used:

```powershell
terraform validate
terraform plan
terraform apply
terraform output -raw alb_dns_name
```

## 3. Debugged CodePipeline And CodeDeploy

You checked pipeline and deployment status using AWS CLI.

Commands you used included:

```powershell
aws codepipeline get-pipeline-state --name aws-ha-app-pipeline --region ap-south-1
aws deploy list-deployments --application-name aws-ha-app --deployment-group-name aws-ha-app-deployment-group --region ap-south-1
aws deploy get-deployment --deployment-id DEPLOYMENT_ID --region ap-south-1
aws deploy get-deployment-instance --deployment-id DEPLOYMENT_ID --instance-id INSTANCE_ID --region ap-south-1
```

You identified deployment failures by reading CodeDeploy lifecycle events.

## 4. Accessed Private EC2 Instances Securely

You learned that the EC2 instances are private and cannot be accessed directly by SSH.

You installed the Session Manager plugin locally and connected using SSM:

```powershell
aws ssm start-session --target INSTANCE_ID --region ap-south-1
```

Inside EC2, you checked:

```bash
sudo systemctl status codedeploy-agent
sudo systemctl status aws-ha-app
curl -f http://localhost:8080/health
```

## 5. Verified CodeDeploy Agents

You checked CodeDeploy agent logs and confirmed the agent was polling AWS:

```bash
sudo tail -n 100 /var/log/aws/codedeploy-agent/codedeploy-agent.log
```

This helped prove private EC2 instances could reach CodeDeploy through outbound network access.

## 6. Triggered CI/CD Deployments

You manually started pipeline runs:

```powershell
aws codepipeline start-pipeline-execution --name aws-ha-app-pipeline --region ap-south-1
```

You watched Source, Build, and Deploy stages until they completed.

## 7. Verified Blue-Green Deployment

You checked that CodeDeploy was configured as:

- `BLUE_GREEN`
- `WITH_TRAFFIC_CONTROL`
- `COPY_AUTO_SCALING_GROUP`

You also verified that CodeDeploy created a temporary green Auto Scaling Group and shifted ALB traffic.

## 8. Verified The Todo App

You opened the app in your browser through the ALB.

You verified:

- frontend loads
- `/api/health` returns database connected
- RDS-backed API works
- ALB routes traffic to EC2

## 9. Pushed Code To GitHub

You committed and pushed changes so CodePipeline could pull them from GitHub.

Important commands:

```powershell
git status
git add .
git commit -m "message"
git push
```

## Final Result

You now have a working DevOps project that demonstrates:

- infrastructure as code
- private app servers
- load balancing
- auto scaling
- secure access with SSM
- CI/CD automation
- blue-green deployment
- RDS-backed application persistence
- production-style troubleshooting
