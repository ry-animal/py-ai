# Main Terraform module for Python AI Multi-Agent Platform
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
  }
}

# Local variables
locals {
  app_name = "py-ai-platform"
  labels = {
    app         = local.app_name
    environment = var.environment
    managed_by  = "terraform"
    platform    = "multi-agent-ai"
  }
}

# Google Cloud Run service for the API
resource "google_cloud_run_service" "py_ai_api" {
  name     = "${local.app_name}-api"
  location = var.region
  project  = var.project_id

  template {
    metadata {
      labels = local.labels
      annotations = {
        "autoscaling.knative.dev/maxScale" = var.max_instances
        "autoscaling.knative.dev/minScale" = var.min_instances
        "run.googleapis.com/cpu-throttling" = "false"
        "run.googleapis.com/execution-environment" = "gen2"
      }
    }

    spec {
      container_concurrency = var.container_concurrency
      timeout_seconds      = var.timeout_seconds

      containers {
        image = var.api_image
        
        ports {
          container_port = 8000
          name          = "http1"
        }

        # Environment variables
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "VECTOR_DB_TYPE"
          value = var.vector_db_type
        }

        env {
          name  = "ANTHROPIC_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret_version.anthropic_key.secret
              key  = "latest"
            }
          }
        }

        env {
          name  = "OPENAI_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret_version.openai_key.secret
              key  = "latest"
            }
          }
        }

        env {
          name  = "REDIS_URL"
          value = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}/0"
        }

        env {
          name  = "MONGODB_URL"
          value = var.mongodb_connection_string
        }

        env {
          name  = "POSTGRES_URL"
          value = "postgresql://${google_sql_user.postgres_user.name}:${google_sql_user.postgres_user.password}@${google_sql_database_instance.postgres.private_ip_address}:5432/${google_sql_database.main.name}"
        }

        # Resource limits
        resources {
          limits = {
            cpu    = var.api_cpu_limit
            memory = var.api_memory_limit
          }
          requests = {
            cpu    = var.api_cpu_request
            memory = var.api_memory_request
          }
        }

        # Health checks
        startup_probe {
          http_get {
            path = "/health"
            port = 8000
          }
          initial_delay_seconds = 10
          timeout_seconds      = 5
          period_seconds       = 10
          failure_threshold    = 3
        }

        liveness_probe {
          http_get {
            path = "/health"
            port = 8000
          }
          initial_delay_seconds = 30
          timeout_seconds      = 5
          period_seconds       = 30
          failure_threshold    = 3
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  lifecycle {
    ignore_changes = [
      template[0].metadata[0].annotations["run.googleapis.com/operation-id"],
    ]
  }
}

# Cloud Run service for Celery workers
resource "google_cloud_run_service" "py_ai_worker" {
  name     = "${local.app_name}-worker"
  location = var.region
  project  = var.project_id

  template {
    metadata {
      labels = local.labels
      annotations = {
        "autoscaling.knative.dev/maxScale" = var.worker_max_instances
        "autoscaling.knative.dev/minScale" = var.worker_min_instances
        "run.googleapis.com/execution-environment" = "gen2"
      }
    }

    spec {
      containers {
        image = var.worker_image
        
        # Worker command
        command = ["uv", "run", "celery", "-A", "app.tasks", "worker", "--loglevel=info"]

        # Same environment as API
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }

        env {
          name  = "VECTOR_DB_TYPE"
          value = var.vector_db_type
        }

        env {
          name  = "REDIS_URL"
          value = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}/1"
        }

        env {
          name  = "MONGODB_URL"
          value = var.mongodb_connection_string
        }

        resources {
          limits = {
            cpu    = var.worker_cpu_limit
            memory = var.worker_memory_limit
          }
          requests = {
            cpu    = var.worker_cpu_request
            memory = var.worker_memory_request
          }
        }
      }
    }
  }

  autogenerate_revision_name = true
}

# Redis instance for caching and Celery broker
resource "google_redis_instance" "cache" {
  name           = "${local.app_name}-cache"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_gb
  region         = var.region
  project        = var.project_id

  redis_version     = "REDIS_7_0"
  display_name      = "${local.app_name} Cache"
  reserved_ip_range = var.redis_ip_range

  labels = local.labels

  lifecycle {
    prevent_destroy = true
  }
}

# PostgreSQL instance for metadata
resource "google_sql_database_instance" "postgres" {
  name             = "${local.app_name}-postgres"
  database_version = "POSTGRES_15"
  region          = var.region
  project         = var.project_id

  settings {
    tier                        = var.postgres_tier
    availability_type           = var.postgres_availability_type
    disk_size                   = var.postgres_disk_size
    disk_type                   = "PD_SSD"
    disk_autoresize            = true
    disk_autoresize_limit      = var.postgres_max_disk_size

    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      location                       = var.region
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 30
        retention_unit   = "COUNT"
      }
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
      require_ssl     = true
    }

    database_flags {
      name  = "log_statement"
      value = "all"
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"
    }
  }

  deletion_protection = true

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

resource "google_sql_database" "main" {
  name     = "${replace(local.app_name, "-", "_")}_db"
  instance = google_sql_database_instance.postgres.name
  project  = var.project_id
}

resource "google_sql_user" "postgres_user" {
  name     = "${replace(local.app_name, "-", "_")}_user"
  instance = google_sql_database_instance.postgres.name
  password = random_password.postgres_password.result
  project  = var.project_id
}

resource "random_password" "postgres_password" {
  length  = 16
  special = true
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "${local.app_name}-vpc"
  auto_create_subnetworks = false
  project                 = var.project_id
}

resource "google_compute_subnetwork" "subnet" {
  name          = "${local.app_name}-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = var.region
  network       = google_compute_network.vpc.id
  project       = var.project_id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.services_cidr
  }
}

# Private service connection for Cloud SQL
resource "google_compute_global_address" "private_ip_address" {
  name          = "${local.app_name}-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
  project       = var.project_id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Vector Database Resources
resource "google_vertex_ai_index" "document_index" {
  count        = var.vector_db_type == "vertex" ? 1 : 0
  region       = var.region
  display_name = "${local.app_name}-documents"
  project      = var.project_id

  metadata {
    contents_delta_uri = var.documents_gcs_bucket
    config {
      dimensions                = 384  # sentence-transformers/all-MiniLM-L6-v2
      approximate_neighbors_count = 150
      distance_measure_type     = "COSINE_DISTANCE"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 1000
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }

  labels = local.labels
}

resource "google_vertex_ai_index_endpoint" "index_endpoint" {
  count        = var.vector_db_type == "vertex" ? 1 : 0
  region       = var.region
  display_name = "${local.app_name}-index-endpoint"
  project      = var.project_id

  labels = local.labels
}

# Secret Manager for API keys
resource "google_secret_manager_secret" "anthropic_key" {
  secret_id = "${local.app_name}-anthropic-key"
  project   = var.project_id

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  labels = local.labels
}

resource "google_secret_manager_secret_version" "anthropic_key" {
  secret      = google_secret_manager_secret.anthropic_key.name
  secret_data = var.anthropic_api_key
}

resource "google_secret_manager_secret" "openai_key" {
  secret_id = "${local.app_name}-openai-key"
  project   = var.project_id

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  labels = local.labels
}

resource "google_secret_manager_secret_version" "openai_key" {
  secret      = google_secret_manager_secret.openai_key.name
  secret_data = var.openai_api_key
}

# IAM for Cloud Run services
resource "google_cloud_run_service_iam_binding" "invoker" {
  location = google_cloud_run_service.py_ai_api.location
  project  = google_cloud_run_service.py_ai_api.project
  service  = google_cloud_run_service.py_ai_api.name
  role     = "roles/run.invoker"

  members = [
    "allUsers", # Make this more restrictive in production
  ]
}

# Cloud Monitoring
resource "google_monitoring_notification_channel" "email" {
  display_name = "${local.app_name} Email Alerts"
  type         = "email"
  project      = var.project_id

  labels = {
    email_address = var.alert_email
  }
}

resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "${local.app_name} High Error Rate"
  project      = var.project_id

  conditions {
    display_name = "Error rate too high"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${google_cloud_run_service.py_ai_api.name}\""
      duration        = "300s"
      comparison      = "COMPARISON_GREATER_THAN"
      threshold_value = 0.05

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]

  alert_strategy {
    auto_close = "1800s"
  }
}

# Outputs
output "api_url" {
  description = "URL of the deployed API"
  value       = google_cloud_run_service.py_ai_api.status[0].url
}

output "worker_url" {
  description = "URL of the worker service"
  value       = google_cloud_run_service.py_ai_worker.status[0].url
}

output "redis_host" {
  description = "Redis instance host"
  value       = google_redis_instance.cache.host
  sensitive   = true
}

output "postgres_connection" {
  description = "PostgreSQL connection details"
  value = {
    host     = google_sql_database_instance.postgres.private_ip_address
    database = google_sql_database.main.name
    username = google_sql_user.postgres_user.name
  }
  sensitive = true
}

output "vector_index_id" {
  description = "Vertex AI index ID (if using Vertex)"
  value       = var.vector_db_type == "vertex" ? google_vertex_ai_index.document_index[0].name : null
}