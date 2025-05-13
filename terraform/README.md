# STOCKER Pro Infrastructure as Code

This directory contains Terraform configurations for provisioning and managing the STOCKER Pro API infrastructure on AWS.

## Architecture

The infrastructure consists of the following components:

- **VPC**: Isolated network environment with public and private subnets across multiple availability zones
- **EKS Cluster**: Managed Kubernetes cluster for container orchestration
- **RDS**: Managed PostgreSQL database for persistent storage
- **ElastiCache**: Managed Redis cluster for caching and session management
- **Helm Charts**: Automated deployment of supporting services (Ingress, Prometheus, Grafana, Loki)

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) (>= 1.0.0)
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) for Kubernetes interaction

## Usage

### Setting Up the Backend

Before initializing Terraform, create an S3 bucket and DynamoDB table for the remote state:

```bash
# Create S3 bucket for Terraform state
aws s3api create-bucket \
  --bucket stocker-pro-terraform-state \
  --region us-east-1

# Enable bucket versioning
aws s3api put-bucket-versioning \
  --bucket stocker-pro-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name stocker-pro-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### Initializing Terraform

Initialize Terraform with the S3 backend:

```bash
terraform init \
  -backend-config="bucket=stocker-pro-terraform-state" \
  -backend-config="key=stocker-pro/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=stocker-pro-terraform-locks"
```

### Deploying to Staging

```bash
# Create a terraform.tfvars file with sensitive values or use environment variables
echo 'db_password = "your-secure-password"' >> terraform.tfvars

# Plan the deployment
terraform plan -var-file=staging.tfvars

# Apply the changes
terraform apply -var-file=staging.tfvars
```

### Deploying to Production

```bash
# Plan the deployment
terraform plan -var-file=production.tfvars

# Apply the changes
terraform apply -var-file=production.tfvars
```

### Connecting to the EKS Cluster

After deployment, configure kubectl to connect to the EKS cluster:

```bash
aws eks update-kubeconfig --name stocker-pro-staging --region us-east-1
# or for production
# aws eks update-kubeconfig --name stocker-pro-production --region us-east-1
```

## Environment-Specific Configurations

- **staging.tfvars**: Configuration for the staging environment (lower resource requirements)
- **production.tfvars**: Configuration for the production environment (higher availability and performance)

## Security Considerations

- Sensitive values like database passwords should be managed using AWS Secrets Manager or environment variables
- All resources are deployed within private subnets with appropriate security groups
- Database and Redis instances are not directly accessible from the internet
- EKS cluster has private endpoints enabled for internal communication

## Monitoring and Logging

The infrastructure includes:

- **Prometheus**: For metrics collection and alerting
- **Grafana**: For metrics visualization and dashboards
- **Loki**: For log aggregation and searching

## Maintenance

### Updating Kubernetes Version

To update the Kubernetes version:

1. Update the `kubernetes_version` variable in the appropriate .tfvars file
2. Run `terraform plan` and `terraform apply` to apply the changes

### Scaling Resources

To scale the number of nodes or instance types:

1. Update the appropriate variables in the .tfvars file
2. Run `terraform plan` and `terraform apply` to apply the changes

## Destroying Infrastructure

```bash
# For staging
terraform destroy -var-file=staging.tfvars

# For production
terraform destroy -var-file=production.tfvars
```

**Warning**: This will destroy all resources managed by Terraform. Use with caution, especially in production environments.
