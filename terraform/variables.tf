# Variables for STOCKER Pro API infrastructure

variable "project_name" {
  description = "The name of the project"
  type        = string
  default     = "stocker-pro"
}

variable "environment" {
  description = "The environment (staging, production)"
  type        = string
  default     = "staging"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "aws_region" {
  description = "The AWS region to deploy resources to"
  type        = string
  default     = "us-east-1"
}

# VPC Variables
variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "The availability zones to use"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "private_subnets" {
  description = "The private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets" {
  description = "The public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

# EKS Variables
variable "kubernetes_version" {
  description = "The Kubernetes version to use"
  type        = string
  default     = "1.26"
}

# App Node Group Variables
variable "app_instance_types" {
  description = "The instance types to use for the app node group"
  type        = list(string)
  default     = ["t3.medium", "t3a.medium"]
}

variable "app_min_size" {
  description = "The minimum size of the app node group"
  type        = number
  default     = 2
}

variable "app_max_size" {
  description = "The maximum size of the app node group"
  type        = number
  default     = 5
}

variable "app_desired_size" {
  description = "The desired size of the app node group"
  type        = number
  default     = 2
}

# Monitoring Node Group Variables
variable "monitoring_instance_types" {
  description = "The instance types to use for the monitoring node group"
  type        = list(string)
  default     = ["t3.large", "t3a.large"]
}

variable "monitoring_min_size" {
  description = "The minimum size of the monitoring node group"
  type        = number
  default     = 1
}

variable "monitoring_max_size" {
  description = "The maximum size of the monitoring node group"
  type        = number
  default     = 3
}

variable "monitoring_desired_size" {
  description = "The desired size of the monitoring node group"
  type        = number
  default     = 1
}

# Database Node Group Variables
variable "database_instance_types" {
  description = "The instance types to use for the database node group"
  type        = list(string)
  default     = ["t3.large", "t3a.large"]
}

variable "database_min_size" {
  description = "The minimum size of the database node group"
  type        = number
  default     = 1
}

variable "database_max_size" {
  description = "The maximum size of the database node group"
  type        = number
  default     = 3
}

variable "database_desired_size" {
  description = "The desired size of the database node group"
  type        = number
  default     = 1
}

# RDS Variables
variable "rds_instance_class" {
  description = "The instance class to use for RDS"
  type        = string
  default     = "db.t3.medium"
}

variable "rds_allocated_storage" {
  description = "The amount of storage to allocate for RDS (in GB)"
  type        = number
  default     = 20
}

variable "rds_max_allocated_storage" {
  description = "The maximum amount of storage to allocate for RDS (in GB)"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "The name of the database"
  type        = string
  default     = "stocker"
}

variable "db_username" {
  description = "The username for the database"
  type        = string
  default     = "stocker"
  sensitive   = true
}

variable "db_password" {
  description = "The password for the database"
  type        = string
  sensitive   = true
}

# Redis Variables
variable "redis_node_type" {
  description = "The node type to use for Redis"
  type        = string
  default     = "cache.t3.medium"
}
