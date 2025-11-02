# Variables for staging environment

variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "us-central1"
}

# Container images (provided by CI/CD)
variable "api_image" {
  description = "API container image"
  type        = string
}

variable "worker_image" {
  description = "Worker container image"
  type        = string
}

# Vector database configuration
variable "vector_db_type" {
  description = "Vector database type"
  type        = string
  default     = "vertex"
}

variable "documents_gcs_bucket" {
  description = "GCS bucket for documents"
  type        = string
  default     = ""
}

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
  description = "Tavily API key"
  type        = string
  sensitive   = true
  default     = ""
}

# Monitoring
variable "alert_email" {
  description = "Email for alerts"
  type        = string
}

# GitHub configuration for Cloud Build
variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "py-ai"
}