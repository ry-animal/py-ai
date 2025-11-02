# Variables for Python AI Multi-Agent Platform Terraform module

variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# Container images
variable "api_image" {
  description = "Container image for the API service"
  type        = string
}

variable "worker_image" {
  description = "Container image for the worker service"
  type        = string
}

# API service configuration
variable "min_instances" {
  description = "Minimum number of API instances"
  type        = number
  default     = 1
}

variable "max_instances" {
  description = "Maximum number of API instances"
  type        = number
  default     = 10
}

variable "container_concurrency" {
  description = "Number of concurrent requests per container"
  type        = number
  default     = 100
}

variable "timeout_seconds" {
  description = "Request timeout in seconds"
  type        = number
  default     = 300
}

variable "api_cpu_limit" {
  description = "CPU limit for API containers"
  type        = string
  default     = "2"
}

variable "api_memory_limit" {
  description = "Memory limit for API containers"
  type        = string
  default     = "4Gi"
}

variable "api_cpu_request" {
  description = "CPU request for API containers"
  type        = string
  default     = "1"
}

variable "api_memory_request" {
  description = "Memory request for API containers"
  type        = string
  default     = "2Gi"
}

# Worker service configuration
variable "worker_min_instances" {
  description = "Minimum number of worker instances"
  type        = number
  default     = 1
}

variable "worker_max_instances" {
  description = "Maximum number of worker instances"
  type        = number
  default     = 5
}

variable "worker_cpu_limit" {
  description = "CPU limit for worker containers"
  type        = string
  default     = "2"
}

variable "worker_memory_limit" {
  description = "Memory limit for worker containers"
  type        = string
  default     = "4Gi"
}

variable "worker_cpu_request" {
  description = "CPU request for worker containers"
  type        = string
  default     = "0.5"
}

variable "worker_memory_request" {
  description = "Memory request for worker containers"
  type        = string
  default     = "1Gi"
}

# Redis configuration
variable "redis_tier" {
  description = "Redis service tier"
  type        = string
  default     = "STANDARD_HA"
  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.redis_tier)
    error_message = "Redis tier must be BASIC or STANDARD_HA."
  }
}

variable "redis_memory_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 4
}

variable "redis_ip_range" {
  description = "Reserved IP range for Redis"
  type        = string
  default     = "10.0.0.0/29"
}

# PostgreSQL configuration
variable "postgres_tier" {
  description = "PostgreSQL machine type"
  type        = string
  default     = "db-custom-2-8192"
}

variable "postgres_availability_type" {
  description = "PostgreSQL availability type"
  type        = string
  default     = "REGIONAL"
  validation {
    condition     = contains(["ZONAL", "REGIONAL"], var.postgres_availability_type)
    error_message = "PostgreSQL availability type must be ZONAL or REGIONAL."
  }
}

variable "postgres_disk_size" {
  description = "PostgreSQL disk size in GB"
  type        = number
  default     = 100
}

variable "postgres_max_disk_size" {
  description = "PostgreSQL maximum disk size in GB"
  type        = number
  default     = 1000
}

# Network configuration
variable "subnet_cidr" {
  description = "CIDR range for the subnet"
  type        = string
  default     = "10.1.0.0/16"
}

variable "pods_cidr" {
  description = "CIDR range for Kubernetes pods"
  type        = string
  default     = "10.2.0.0/16"
}

variable "services_cidr" {
  description = "CIDR range for Kubernetes services"
  type        = string
  default     = "10.3.0.0/16"
}

# Vector database configuration
variable "vector_db_type" {
  description = "Type of vector database to use"
  type        = string
  default     = "vertex"
  validation {
    condition     = contains(["vertex", "snowflake", "mongodb", "cockroach"], var.vector_db_type)
    error_message = "Vector DB type must be one of: vertex, snowflake, mongodb, cockroach."
  }
}

variable "documents_gcs_bucket" {
  description = "GCS bucket for document storage (Vertex AI)"
  type        = string
  default     = ""
}

# Database connection strings
variable "mongodb_connection_string" {
  description = "MongoDB connection string"
  type        = string
  sensitive   = true
}

# API keys
variable "anthropic_api_key" {
  description = "Anthropic API key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "tavily_api_key" {
  description = "Tavily API key for web search"
  type        = string
  sensitive   = true
  default     = ""
}

# Monitoring
variable "alert_email" {
  description = "Email address for monitoring alerts"
  type        = string
}

# Feature flags
variable "enable_streaming" {
  description = "Enable streaming responses"
  type        = bool
  default     = true
}

variable "enable_web_search" {
  description = "Enable web search functionality"
  type        = bool
  default     = true
}

variable "enable_multi_agent" {
  description = "Enable multi-agent architecture"
  type        = bool
  default     = true
}

# Performance tuning
variable "max_request_body_bytes" {
  description = "Maximum request body size in bytes"
  type        = number
  default     = 10485760  # 10MB
}

variable "rate_limit_requests_per_window" {
  description = "Rate limit requests per window"
  type        = number
  default     = 120
}

variable "rate_limit_window_seconds" {
  description = "Rate limit window in seconds"
  type        = number
  default     = 60
}

variable "agent_memory_ttl_seconds" {
  description = "Agent memory TTL in seconds"
  type        = number
  default     = 86400  # 24 hours
}

# Tags and labels
variable "additional_labels" {
  description = "Additional labels to apply to resources"
  type        = map(string)
  default     = {}
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "ai-platform"
}

variable "team" {
  description = "Team responsible for the resources"
  type        = string
  default     = "ai-engineering"
}