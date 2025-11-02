# Staging environment for Python AI Multi-Agent Platform
terraform {
  required_version = ">= 1.0"
  
  backend "gcs" {
    bucket = "py-ai-terraform-state-staging"
    prefix = "terraform/state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Data sources
data "google_project" "current" {}

# Main platform module
module "py_ai_platform" {
  source = "../../modules/py-ai-platform"

  # Project configuration
  project_id  = var.project_id
  region      = var.region
  environment = "staging"

  # Container images (from CI/CD pipeline)
  api_image    = var.api_image
  worker_image = var.worker_image

  # Staging-specific scaling
  min_instances        = 1
  max_instances        = 5
  worker_min_instances = 1
  worker_max_instances = 3

  # Resource allocation (smaller for staging)
  api_cpu_limit        = "1"
  api_memory_limit     = "2Gi"
  api_cpu_request      = "0.5"
  api_memory_request   = "1Gi"
  
  worker_cpu_limit     = "1"
  worker_memory_limit  = "2Gi"
  worker_cpu_request   = "0.5"
  worker_memory_request = "1Gi"

  # Database configuration
  redis_tier           = "BASIC"
  redis_memory_gb      = 2
  postgres_tier        = "db-custom-1-4096"
  postgres_disk_size   = 50
  postgres_max_disk_size = 200
  postgres_availability_type = "ZONAL"

  # Vector database
  vector_db_type           = var.vector_db_type
  documents_gcs_bucket     = var.documents_gcs_bucket
  mongodb_connection_string = var.mongodb_connection_string

  # API keys
  anthropic_api_key = var.anthropic_api_key
  openai_api_key    = var.openai_api_key
  tavily_api_key    = var.tavily_api_key

  # Monitoring
  alert_email = var.alert_email

  # Feature flags
  enable_streaming    = true
  enable_web_search   = true
  enable_multi_agent  = true

  # Performance settings (relaxed for staging)
  max_request_body_bytes         = 20971520  # 20MB
  rate_limit_requests_per_window = 200
  rate_limit_window_seconds      = 60

  # Labels
  additional_labels = {
    cost_center = "ai-platform"
    team       = "ai-engineering"
    purpose    = "staging-testing"
  }
}

# Staging-specific resources

# Cloud Storage bucket for document uploads
resource "google_storage_bucket" "staging_documents" {
  name          = "${var.project_id}-py-ai-staging-documents"
  location      = var.region
  force_destroy = true  # Allow destruction in staging

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30  # Delete after 30 days in staging
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    environment = "staging"
    purpose     = "document-storage"
  }
}

# IAM for document bucket
resource "google_storage_bucket_iam_binding" "staging_documents_admin" {
  bucket = google_storage_bucket.staging_documents.name
  role   = "roles/storage.objectAdmin"

  members = [
    "serviceAccount:${data.google_project.current.number}-compute@developer.gserviceaccount.com",
  ]
}

# Cloud Build trigger for automatic deployment
resource "google_cloudbuild_trigger" "staging_deploy" {
  name        = "py-ai-staging-deploy"
  description = "Deploy to staging on main branch push"

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^main$"
    }
  }

  build {
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "build",
        "-t", "gcr.io/${var.project_id}/py-ai-api:${COMMIT_SHA}",
        "--target", "prod",
        "."
      ]
    }

    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "build", 
        "-t", "gcr.io/${var.project_id}/py-ai-worker:${COMMIT_SHA}",
        "--target", "worker",
        "."
      ]
    }

    step {
      name = "gcr.io/cloud-builders/docker"
      args = ["push", "gcr.io/${var.project_id}/py-ai-api:${COMMIT_SHA}"]
    }

    step {
      name = "gcr.io/cloud-builders/docker"
      args = ["push", "gcr.io/${var.project_id}/py-ai-worker:${COMMIT_SHA}"]
    }

    step {
      name = "hashicorp/terraform:1.6"
      entrypoint = "sh"
      args = [
        "-c",
        <<-EOT
        cd terraform/environments/staging
        terraform init
        terraform plan -var="api_image=gcr.io/${var.project_id}/py-ai-api:${COMMIT_SHA}" -var="worker_image=gcr.io/${var.project_id}/py-ai-worker:${COMMIT_SHA}"
        terraform apply -auto-approve -var="api_image=gcr.io/${var.project_id}/py-ai-api:${COMMIT_SHA}" -var="worker_image=gcr.io/${var.project_id}/py-ai-worker:${COMMIT_SHA}"
        EOT
      ]
    }
  }

  substitutions = {
    _ENVIRONMENT = "staging"
  }
}

# Outputs
output "api_url" {
  description = "Staging API URL"
  value       = module.py_ai_platform.api_url
}

output "worker_url" {
  description = "Staging worker URL"
  value       = module.py_ai_platform.worker_url
}

output "documents_bucket" {
  description = "Staging documents bucket"
  value       = google_storage_bucket.staging_documents.name
}

output "database_connections" {
  description = "Database connection information"
  value = {
    redis_host = module.py_ai_platform.redis_host
    postgres   = module.py_ai_platform.postgres_connection
  }
  sensitive = true
}