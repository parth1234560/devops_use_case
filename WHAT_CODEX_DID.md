# What Codex Did In This Project

This file summarizes the work Codex helped implement, debug, and verify.

## 1. Fixed CodePipeline And CodeDeploy Packaging

The original deployment failed because CodeDeploy was not receiving the app bundle in the shape it expects.

Codex updated `buildspec.yml` so CodeBuild publishes the contents of the `app/` directory directly, with `appspec.yml` at the artifact root.

This fixed the common CodeDeploy issue where `appspec.yml` is hidden inside another zip file.

## 2. Fixed EC2 Agent Connectivity

The EC2 instances were private and initially not reachable through SSM or CodeDeploy.

Codex updated EC2 bootstrapping so new instances install and start:

- AWS Systems Manager Agent
- AWS CodeDeploy Agent

This allowed:

- SSM Session Manager access
- CodeDeploy lifecycle events to reach EC2
- private EC2 instances to remain private without SSH

## 3. Added Root Terraform Outputs

Codex added useful Terraform outputs for:

- CodeBuild project name
- CodeDeploy application name
- CodeDeploy deployment group name
- CodePipeline name

These made AWS CLI verification easier.

## 4. Converted Deployment To Blue-Green

The deployment group was changed from in-place deployment to blue-green deployment.

Codex configured:

- `BLUE_GREEN` deployment type
- `WITH_TRAFFIC_CONTROL`
- green fleet provisioning with `COPY_AUTO_SCALING_GROUP`
- ALB target group integration
- old blue instance termination after 5 minutes

## 5. Fixed CodeDeploy IAM Permissions

Blue-green deployment failed because the CodeDeploy service role did not have enough permissions to work with Auto Scaling and launch templates.

Codex added permissions for:

- `ec2:RunInstances`
- `ec2:CreateTags`
- `iam:PassRole`

This allowed CodeDeploy to create the green Auto Scaling Group.

## 6. Built The Todo Web Application

Codex replaced the basic demo HTTP server with a real todo-list web application.

The app now includes:

- frontend HTML/CSS/JavaScript
- backend API endpoints
- RDS MySQL persistence
- todo creation
- todo listing
- todo completion toggling
- todo deletion
- health checks

The app is still hosted on EC2 and exposed through the ALB.

## 7. Connected The App To RDS

Codex updated the app so it:

- reads DB credentials from AWS Secrets Manager
- discovers the RDS endpoint through the AWS RDS API
- connects using PyMySQL
- creates the `todos` table automatically
- stores and queries todo data from RDS

## 8. Updated Deployment Scripts

Codex updated CodeDeploy scripts to:

- install Python and pip
- install app dependencies after the app files are copied
- configure service environment variables
- retry health validation until the app is ready

This fixed failures caused by dependency timing and app startup delay.

## 9. Updated IAM For EC2

Codex updated the EC2 IAM role so the app can:

- read the DB secret from Secrets Manager
- describe the RDS instance to discover the database endpoint
- read deployment artifacts from S3
- connect to SSM

## 10. Updated README

Codex rewrote the README to explain:

- the app
- ALB access
- SSM access
- CI/CD
- blue-green deployment
- RDS Multi-AZ
- backups
- cleanup

## 11. Verified The End-To-End System

Codex helped verify:

- Terraform validation
- CodePipeline Source, Build, Deploy stages
- CodeDeploy blue-green lifecycle events
- ALB `/health`
- ALB `/api/health`
- RDS connectivity
- todo frontend loading in the browser

## Final Result

The final project is a working AWS high-availability todo web application with:

- private EC2 app servers
- public ALB
- Multi-AZ RDS MySQL
- CodePipeline
- CodeBuild
- CodeDeploy blue-green deployment
- RDS-backed frontend and backend application
