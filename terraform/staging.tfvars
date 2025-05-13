# Terraform variable values for staging environment

environment = "staging"
aws_region = "us-east-1"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]
private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
public_subnets = ["10.0.101.0/24", "10.0.102.0/24"]

# EKS Configuration
kubernetes_version = "1.26"

# App Node Group
app_instance_types = ["t3.medium", "t3a.medium"]
app_min_size = 2
app_max_size = 4
app_desired_size = 2

# Monitoring Node Group
monitoring_instance_types = ["t3.medium", "t3a.medium"]
monitoring_min_size = 1
monitoring_max_size = 2
monitoring_desired_size = 1

# Database Node Group
database_instance_types = ["t3.medium", "t3a.medium"]
database_min_size = 1
database_max_size = 2
database_desired_size = 1

# RDS Configuration
rds_instance_class = "db.t3.medium"
rds_allocated_storage = 20
rds_max_allocated_storage = 50

# Redis Configuration
redis_node_type = "cache.t3.small"
