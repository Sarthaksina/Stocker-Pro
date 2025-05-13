# Terraform variable values for production environment

environment = "production"
aws_region = "us-east-1"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnets = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

# EKS Configuration
kubernetes_version = "1.26"

# App Node Group
app_instance_types = ["t3.large", "t3a.large"]
app_min_size = 3
app_max_size = 10
app_desired_size = 3

# Monitoring Node Group
monitoring_instance_types = ["t3.large", "t3a.large"]
monitoring_min_size = 2
monitoring_max_size = 4
monitoring_desired_size = 2

# Database Node Group
database_instance_types = ["t3.large", "t3a.large"]
database_min_size = 2
database_max_size = 4
database_desired_size = 2

# RDS Configuration
rds_instance_class = "db.t3.large"
rds_allocated_storage = 50
rds_max_allocated_storage = 200

# Redis Configuration
redis_node_type = "cache.t3.medium"
