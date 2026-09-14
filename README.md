# AWS Highly Available DevOps Platform

**Terraform · AWS · CI/CD · Blue-Green Deployment via codepipeline · Auto Scaling · RDS · IAM · CloudWatch**

A production-style AWS deployment project that provisions a highly available Python application using **Terraform** and automates application delivery through **AWS CodePipeline, CodeBuild and CodeDeploy**.

The application runs on private EC2 instances behind an Application Load Balancer, stores data in a Multi-AZ MySQL database, and uses CodeDeploy Blue-Green deployments to release new versions with controlled traffic shifting.

---

## Architecture

```text
                         ┌──────────────────┐
                         │      GitHub      │
                         │ Application Code │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │  AWS CodePipeline│
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    CodeBuild     │
                         │ Build & Package  │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    CodeDeploy    │
                         │   Blue-Green     │
                         └────────┬─────────┘
                                  │
                       Traffic Shift / Deploy
                                  │
                                  ▼
        ┌─────────────────────────────────────────────────┐
        │                     AWS VPC                     │
        │                                                 │
        │   Public Subnets                                │
        │   ┌─────────────────────────────────────────┐   │
Internet ───►│        Application Load Balancer        │   │
        │   └──────────────────┬──────────────────────┘   │
        │                      │                          │
        │   Private Subnets    │                          │
        │            ┌─────────┴─────────┐                │
        │            ▼                   ▼                │
        │      ┌───────────┐       ┌───────────┐          │
        │      │ EC2 / AZ1 │       │ EC2 / AZ2 │          │
        │      │   ASG     │       │   ASG     │          │
        │      └─────┬─────┘       └─────┬─────┘          │
        │            │                   │                │
        │            └─────────┬─────────┘                │
        │                      ▼                          │
        │              ┌───────────────┐                  │
        │              │   RDS MySQL   │                  │
        │              │   Multi-AZ     │                  │
        │              └───────────────┘                  │
        │                                                 │
        └─────────────────────────────────────────────────┘

     Supporting Services:
     IAM · Secrets Manager · SSM · CloudWatch · SNS
```

---

## What This Project Does

The project solves a simple real-world problem:

> **How can an application be deployed on AWS with high availability, private infrastructure, automated deployments and a safe release strategy?**

Terraform provisions the infrastructure, while AWS services handle application delivery and runtime operations.

### Key capabilities

* Highly available AWS architecture across multiple Availability Zones
* Private EC2 application servers
* Application Load Balancer for incoming traffic
* Auto Scaling Group for application capacity
* Multi-AZ MySQL RDS for database availability
* Infrastructure as Code using Terraform
* Automated CI/CD using AWS CodePipeline
* Application packaging with CodeBuild
* Blue-Green deployments using CodeDeploy
* Secrets stored in AWS Secrets Manager
* EC2 administration through Systems Manager instead of SSH
* Health checks through ALB and CodeDeploy
* Database encryption and automated backups

---

## Application

The project includes a small Python Todo application.

```text
Browser
   │
   ▼
Application Load Balancer
   │
   ▼
Private EC2 Instance
   │
   ▼
RDS MySQL
```

### Endpoints

| Endpoint          | Purpose                             |
| ----------------- | ----------------------------------- |
| `/`               | Todo application                    |
| `/health`         | Application health check            |
| `/api/health`     | Application + database health check |
| `/api/todos`      | Create/list todos                   |
| `/api/todos/{id}` | Update/delete a todo                |

The application runs as a `systemd` service on port `8080`.

---

# Infrastructure

## Networking

Terraform creates a custom VPC with:

* Public subnets for the Application Load Balancer
* Private subnets for EC2 and RDS
* Multiple Availability Zones
* Separate security groups for ALB, EC2 and database traffic

The EC2 instances and database are **not directly exposed to the internet**.

Traffic follows:

```text
Internet
   ↓
Public ALB
   ↓
Private EC2
   ↓
Private RDS
```

---

## Compute

The application runs inside an **EC2 Auto Scaling Group**.

The configuration supports:

```text
Minimum     : 2
Desired     : 2
Maximum     : 4
```

The instances are launched in private subnets and do not receive public IP addresses.

The Auto Scaling Group provides:

* Instance replacement
* Capacity management
* Multi-AZ deployment
* Integration with CodeDeploy Blue-Green deployments

---

## Application Load Balancer

The ALB is the public entry point.

It:

* Accepts HTTP traffic
* Routes requests to healthy EC2 instances
* Performs `/health` checks
* Removes unhealthy instances from service

This means users never need to connect directly to an EC2 instance.

---

# Database

The application uses **Amazon RDS for MySQL**.

Configuration includes:

* MySQL 8.0
* Private subnets
* Multi-AZ deployment
* Storage encryption
* Automated backups
* 7-day backup retention
* Deletion protection
* Final snapshot on destruction

The Multi-AZ configuration provides a standby database in another Availability Zone for failover.

---

# Secrets Management

Database credentials are not hard-coded into the application or Terraform configuration.

The application retrieves credentials from:

```text
AWS Secrets Manager
        │
        ▼
     EC2 App
        │
        ▼
     RDS MySQL
```

This keeps sensitive database credentials outside the source code.

---

# CI/CD Pipeline

The deployment pipeline uses native AWS services.

```text
GitHub
   │
   ▼
CodePipeline
   │
   ▼
CodeBuild
   │
   ▼
CodeDeploy
   │
   ▼
Blue-Green Deployment
```

### 1. Source — CodePipeline

CodePipeline monitors the GitHub repository and starts a deployment when application changes are detected.

### 2. Build — CodeBuild

CodeBuild prepares the application artifact that will be deployed.

The build configuration is defined in:

```text
buildspec.yml
```

### 3. Deploy — CodeDeploy

CodeDeploy takes the application artifact and performs the deployment to the EC2 environment.

---

# Blue-Green Deployment

The project uses CodeDeploy **Blue-Green deployment with traffic control**.

The idea is simple:

```text
              Current Version
                   BLUE
                 EC2 EC2
                   │
                   │
             Application
              Load Balancer
                   │
                   ▼

        New Version is created
                   │
                  GREEN
                 EC2 EC2
```

The Green environment is provisioned from the existing Auto Scaling configuration.

After the new instances pass health checks, traffic is shifted from Blue to Green.

```text
Before:

ALB ─────► BLUE
           v1


After deployment:

ALB ─────► GREEN
           v2
```

The previous Blue environment is kept temporarily to provide a rollback window and is configured to be terminated after the deployment wait period.

This makes the deployment safer than replacing the running instances directly.

---

# Security

Security is handled at multiple layers.

### Network

```text
Internet
   ↓
ALB
   ↓
EC2
   ↓
RDS
```

Only required traffic is allowed between security groups.

### IAM

AWS IAM roles are used instead of storing long-lived AWS credentials on EC2 instances.

### Instance Access

EC2 instances are managed through **AWS Systems Manager Session Manager** instead of exposing SSH to the internet.

### Database

RDS is:

* Private
* Encrypted
* Multi-AZ
* Protected from accidental deletion

---

# Infrastructure as Code

All major AWS infrastructure is managed through Terraform.

```text
terraform/
├── modules/
│   ├── networking/
│   ├── iam/
│   ├── compute/
│   ├── database/
│   └── monitoring/
│
├── main.tf
├── variables.tf
├── outputs.tf
└── ...
```

The infrastructure is modular so individual components can be maintained independently.

---

# Monitoring

The infrastructure is designed around AWS monitoring services such as CloudWatch and SNS.

Important signals include:

* ALB errors
* Unhealthy targets
* EC2 CPU utilization
* Auto Scaling capacity
* RDS CPU utilization
* RDS storage
* Database connections

Alerts can be delivered through SNS.

---

# Deployment Flow

A typical application release looks like this:

```text
1. Push code to GitHub
          ↓
2. CodePipeline detects change
          ↓
3. CodeBuild creates deployment artifact
          ↓
4. CodeDeploy starts Blue-Green deployment
          ↓
5. Green instances are created
          ↓
6. Application health checks run
          ↓
7. ALB traffic moves to Green
          ↓
8. Blue environment is kept temporarily
          ↓
9. Blue instances are terminated
```

---

# Why These AWS Services?

| Requirement               | AWS Solution              |
| ------------------------- | ------------------------- |
| Infrastructure automation | Terraform                 |
| Public entry point        | Application Load Balancer |
| Application compute       | EC2                       |
| High availability         | Multi-AZ + Auto Scaling   |
| Database                  | RDS MySQL                 |
| Database HA               | RDS Multi-AZ              |
| Secret management         | Secrets Manager           |
| CI/CD orchestration       | CodePipeline              |
| Build/package             | CodeBuild                 |
| Deployment                | CodeDeploy                |
| Safe releases             | Blue-Green deployment     |
| Server access             | Systems Manager           |
| Monitoring                | CloudWatch                |
| Notifications             | SNS                       |

---

# Project Structure

```text
.
├── app/
│   ├── app.py
│   ├── appspec.yml
│   ├── aws-ha-app.service
│   ├── requirements.txt
│   └── scripts/
│
├── terraform/
│   ├── modules/
│   │   ├── networking/
│   │   ├── iam/
│   │   ├── compute/
│   │   ├── database/
│   │   └── monitoring/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
│
├── buildspec.yml
└── README.md
```

---

# Running the Project

Initialize Terraform:

```bash
cd terraform
terraform init
```

Validate:

```bash
terraform validate
```

Review infrastructure changes:

```bash
terraform plan
```

Deploy:

```bash
terraform apply
```

After deployment, retrieve the ALB endpoint:

```bash
terraform output -raw alb_dns_name
```

The application is accessed through the ALB rather than directly through the EC2 instances.

---

# Cleanup

This project uses real AWS resources, so remember to clean up after testing:

```bash
terraform destroy
```

RDS deletion protection must be disabled before intentionally destroying the database.

---

## Tech Stack

**Cloud:** AWS
**IaC:** Terraform
**Compute:** EC2, Auto Scaling
**Networking:** VPC, ALB, Security Groups
**Database:** RDS MySQL
**CI/CD:** CodePipeline, CodeBuild, CodeDeploy
**Deployment:** Blue-Green
**Security:** IAM, Secrets Manager, SSM
**Monitoring:** CloudWatch, SNS
**Application:** Python
