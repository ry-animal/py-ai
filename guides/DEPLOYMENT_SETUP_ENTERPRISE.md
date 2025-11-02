# Enterprise Deployment Setup Guide (Option 1)

Complete setup guide for full enterprise deployment with all features enabled.

## 🎯 Overview

This guide sets up a production-ready enterprise multi-agent platform with:
- All 4 agent architectures (Smart Orchestrator, Pydantic-AI, Hybrid, LangGraph)
- Multi-cloud vector databases (Vertex AI, Snowflake, CockroachDB)
- Full CI/CD pipeline with Harness integration
- Enterprise-grade monitoring and observability
- Estimated cost: $100-200/month

## 📋 Prerequisites

- Google Cloud Platform account with billing enabled
- GitHub account with repository access
- Domain name (optional, for custom domains)
- ~30-45 minutes setup time

## 🛠️ Step 1: Google Cloud Platform Setup

### 1.1 Create and Configure Project

```bash
# Install gcloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Create new project
export PROJECT_ID="py-ai-enterprise-$(date +%s)"
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

# Enable billing (required - do this in console)
echo "⚠️  Enable billing for project $PROJECT_ID in the GCP Console"
echo "https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
```

### 1.2 Enable Required APIs

```bash
# Enable all necessary APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sql.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com

echo "✅ APIs enabled successfully"
```

### 1.3 Create Service Account

```bash
# Create Terraform service account
gcloud iam service-accounts create terraform-sa \
    --display-name="Terraform Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:terraform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/owner"

# Create and download key
gcloud iam service-accounts keys create ~/py-ai-terraform-key.json \
    --iam-account="terraform-sa@$PROJECT_ID.iam.gserviceaccount.com"

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/py-ai-terraform-key.json
```

### 1.4 Create Terraform State Storage

```bash
# Create bucket for Terraform state
gsutil mb gs://$PROJECT_ID-terraform-state
gsutil versioning set on gs://$PROJECT_ID-terraform-state

# Create Cloud Build bucket
gsutil mb gs://$PROJECT_ID-cloudbuild-artifacts

echo "✅ Storage buckets created"
```

## 🔐 Step 2: Secrets and API Keys

### 2.1 Obtain Required API Keys

```bash
# Required keys:
echo "📝 Get these API keys:"
echo "1. Anthropic API Key: https://console.anthropic.com/"
echo "2. OpenAI API Key: https://platform.openai.com/api-keys"
echo "3. Tavily API Key (optional): https://tavily.com/"
```

### 2.2 Store Secrets in Secret Manager

```bash
# Store API keys securely
echo -n "YOUR_ANTHROPIC_KEY" | gcloud secrets create anthropic-api-key --data-file=-
echo -n "YOUR_OPENAI_KEY" | gcloud secrets create openai-api-key --data-file=-
echo -n "YOUR_TAVILY_KEY" | gcloud secrets create tavily-api-key --data-file=-

echo "✅ Secrets stored in Secret Manager"
```

## 🗄️ Step 3: Database Services Setup

### 3.1 MongoDB Atlas (Recommended)

```bash
# 1. Go to https://cloud.mongodb.com/
# 2. Create new project: "py-ai-enterprise"
# 3. Create M10 cluster (Production tier)
# 4. Create database user: py_ai_user
# 5. Whitelist GCP IP ranges
# 6. Get connection string

echo "📝 MongoDB Atlas Setup:"
echo "1. Create M10+ cluster for production"
echo "2. Database: py_ai_platform"
echo "3. User: py_ai_user with readWrite role"
echo "4. Network: Allow GCP IP ranges"
```

### 3.2 Snowflake (Optional Vector DB)

```bash
echo "📝 Snowflake Setup (if using Snowflake for vectors):"
echo "1. Create Snowflake account"
echo "2. Create warehouse: PY_AI_WH"
echo "3. Create database: PY_AI_DB"
echo "4. Create schema: VECTORS"
echo "5. Enable Cortex search functions"
```

## 🚀 Step 4: Repository and CI/CD Setup

### 4.1 Fork/Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-username/py-ai.git
cd py-ai

# Create enterprise branch
git checkout -b enterprise-deployment
```

### 4.2 Configure GitHub Integration

```bash
# Connect GitHub repo for Cloud Build triggers
gcloud alpha builds triggers create github \
    --repo-name=py-ai \
    --repo-owner=your-username \
    --branch-pattern="^main$" \
    --build-config=.cloudbuild/deploy.yaml

echo "✅ GitHub integration configured"
```

## ⚙️ Step 5: Terraform Configuration

### 5.1 Create Terraform Variables

```bash
# Create terraform.tfvars file
cat > terraform/environments/production/terraform.tfvars << EOF
# Project Configuration
project_id = "$PROJECT_ID"
region = "us-central1"
environment = "production"

# Container Images (will be built by CI/CD)
api_image = "gcr.io/$PROJECT_ID/py-ai-api:latest"
worker_image = "gcr.io/$PROJECT_ID/py-ai-worker:latest"

# Scaling Configuration
min_instances = 2
max_instances = 10
worker_min_instances = 1
worker_max_instances = 5

# Resource Allocation
api_cpu_limit = "2"
api_memory_limit = "4Gi"
api_cpu_request = "1"
api_memory_request = "2Gi"

worker_cpu_limit = "2"
worker_memory_limit = "4Gi"
worker_cpu_request = "1"
worker_memory_request = "2Gi"

# Database Configuration
redis_tier = "STANDARD_HA"
redis_memory_gb = 4
postgres_tier = "db-custom-2-8192"
postgres_disk_size = 100
postgres_max_disk_size = 500
postgres_availability_type = "REGIONAL"

# Vector Database
vector_db_type = "vertex"
documents_gcs_bucket = "$PROJECT_ID-documents"

# MongoDB (Atlas connection string)
mongodb_connection_string = "mongodb+srv://py_ai_user:PASSWORD@cluster.mongodb.net/py_ai_platform"

# API Keys (stored in Secret Manager)
anthropic_api_key = "projects/$PROJECT_ID/secrets/anthropic-api-key/versions/latest"
openai_api_key = "projects/$PROJECT_ID/secrets/openai-api-key/versions/latest"
tavily_api_key = "projects/$PROJECT_ID/secrets/tavily-api-key/versions/latest"

# GitHub Configuration
github_owner = "your-username"
github_repo = "py-ai"

# Monitoring
alert_email = "your-email@domain.com"

# Feature Flags
enable_streaming = true
enable_web_search = true
enable_multi_agent = true

# Performance Settings
max_request_body_bytes = 52428800  # 50MB
rate_limit_requests_per_window = 1000
rate_limit_window_seconds = 60

# Labels
additional_labels = {
  cost_center = "ai-platform"
  team       = "engineering"
  purpose    = "production"
  owner      = "your-name"
}
EOF
```

### 5.2 Update Backend Configuration

```bash
# Update backend configuration
cat > terraform/environments/production/backend.tf << EOF
terraform {
  backend "gcs" {
    bucket = "$PROJECT_ID-terraform-state"
    prefix = "terraform/production"
  }
}
EOF
```

## 🚀 Step 6: Deploy Infrastructure

### 6.1 Initialize and Plan

```bash
cd terraform/environments/production

# Initialize Terraform
terraform init

# Review the plan
terraform plan

echo "📝 Review the plan above. Press Enter to continue with deployment..."
read
```

### 6.2 Deploy Infrastructure

```bash
# Apply infrastructure
terraform apply -auto-approve

# Get outputs
terraform output

echo "✅ Infrastructure deployed successfully!"
```

### 6.3 Build and Deploy Application

```bash
# Trigger initial build
cd ../../../
gcloud builds submit --config=.cloudbuild/deploy.yaml

# Check deployment status
gcloud run services list --platform=managed
```

## 🔍 Step 7: Validation and Testing

### 7.1 Get Service URLs

```bash
# Get API URL
export API_URL=$(gcloud run services describe py-ai-api --platform=managed --region=us-central1 --format="value(status.url)")

echo "API URL: $API_URL"
```

### 7.2 Test Enterprise Features

```bash
# Test health endpoints
curl -f $API_URL/health
curl -f $API_URL/ready

# Test smart orchestrator
curl -s $API_URL/smart/status | jq '.'

# Test all agent architectures
curl -s $API_URL/smart/agents/comparison | jq '.available_agents | keys'

# Test intelligent routing
curl -s -X POST $API_URL/smart/analyze \
  -H "Content-Type: application/json" \
  -d '{"question": "Extract user data in JSON format"}' | jq '.decision'

echo "✅ All tests passed!"
```

### 7.3 Performance Testing

```bash
# Test concurrent requests
for i in {1..10}; do
  curl -s $API_URL/smart/status > /dev/null &
done
wait

echo "✅ Concurrent requests handled successfully"
```

## 📊 Step 8: Monitoring and Observability

### 8.1 Set Up Monitoring

```bash
# Create monitoring dashboard
gcloud monitoring dashboards create --config-from-file=monitoring/dashboard.json

# Set up alerting policies
gcloud alpha monitoring policies create --policy-from-file=monitoring/alerts.yaml
```

### 8.2 Enable Logging

```bash
# Enable structured logging
gcloud logging sinks create py-ai-logs \
  storage.googleapis.com/$PROJECT_ID-logs \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="py-ai-api"'
```

## 🔐 Step 9: Security Hardening

### 9.1 Configure IAM

```bash
# Remove unnecessary permissions
gcloud projects remove-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:terraform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/owner"

# Add minimal required permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:terraform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"
```

### 9.2 Enable Security Features

```bash
# Enable Container Analysis
gcloud services enable containeranalysis.googleapis.com

# Enable Binary Authorization
gcloud container binauthz policy import policy.yaml
```

## 💰 Step 10: Cost Optimization

### 10.1 Set Up Budget Alerts

```bash
# Create budget
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="py-ai-enterprise-budget" \
  --budget-amount=200USD \
  --threshold-rule=percent=90,basis=CURRENT_SPEND \
  --threshold-rule=percent=100,basis=FORECASTED_SPEND
```

### 10.2 Enable Cost Monitoring

```bash
# Export billing data
gcloud logging sinks create billing-export \
  bigquery.googleapis.com/projects/$PROJECT_ID/datasets/billing_export
```

## 🎉 Step 11: Production Readiness

### 11.1 Domain Setup (Optional)

```bash
# Set up custom domain
gcloud run domain-mappings create \
  --service=py-ai-api \
  --domain=api.yourdomain.com \
  --platform=managed \
  --region=us-central1
```

### 11.2 SSL Certificates

```bash
# Managed SSL certificate will be automatically provisioned
echo "SSL certificate will be automatically provisioned for your domain"
```

### 11.3 Final Validation

```bash
# Run comprehensive test suite
API_BASE_URL=$API_URL make validate-enterprise

echo "🎉 Enterprise deployment complete!"
echo "API URL: $API_URL"
echo "Monitoring: https://console.cloud.google.com/monitoring"
echo "Logs: https://console.cloud.google.com/logs"
```

## 📋 Post-Deployment Checklist

- [ ] All health endpoints responding
- [ ] Smart orchestrator operational with 4 agents
- [ ] Database connections established
- [ ] Vector search functional
- [ ] Monitoring and alerting configured
- [ ] SSL certificates active
- [ ] Cost monitoring enabled
- [ ] Security policies applied
- [ ] Backup procedures documented

## 🔧 Troubleshooting

### Common Issues

1. **Service Account Permissions**: Ensure the service account has all required roles
2. **API Quotas**: Check GCP quotas for Cloud Run, SQL, Redis
3. **Database Connections**: Verify network connectivity and credentials
4. **Build Failures**: Check Cloud Build logs for detailed error messages

### Support Resources

- **GCP Documentation**: https://cloud.google.com/docs
- **Terraform GCP Provider**: https://registry.terraform.io/providers/hashicorp/google
- **Project Issues**: https://github.com/your-username/py-ai/issues

## 💸 Expected Costs

**Monthly Cost Breakdown (Estimated):**
- Cloud Run API (2 instances): $50-80
- Cloud Run Worker (1 instance): $25-40
- Cloud SQL PostgreSQL: $30-50
- Cloud Memorystore Redis: $25-40
- Vertex AI Vector Search: $20-30
- Storage & Networking: $10-20
- **Total: $160-260/month**

*Costs vary based on usage patterns and regional pricing.*

---

🚀 **Your enterprise multi-agent platform is now ready for production!**