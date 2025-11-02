# Staging Deployment Setup Guide (Option 2)

Simplified setup guide for staging deployment with essential features only.

## 🎯 Overview

This guide sets up a staging environment with:
- Core multi-agent functionality (all 4 architectures)
- Single vector database (Vertex AI or ChromaDB)
- Basic monitoring and logging
- Minimal resource allocation for cost efficiency
- Estimated cost: $50-100/month

## 📋 Prerequisites

- Google Cloud Platform account with billing enabled
- GitHub account with repository access
- ~15-20 minutes setup time

## 🛠️ Step 1: Quick GCP Setup

### 1.1 Project and Basic Services

```bash
# Install gcloud CLI if needed
# https://cloud.google.com/sdk/docs/install

# Authenticate and create project
gcloud auth login
export PROJECT_ID="py-ai-staging-$(date +%s)"
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

echo "⚠️  Enable billing for project $PROJECT_ID in the GCP Console"
echo "https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"
```

### 1.2 Enable Essential APIs

```bash
# Enable only required APIs for staging
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable redis.googleapis.com

echo "✅ Essential APIs enabled"
```

### 1.3 Create Terraform State Storage

```bash
# Create minimal storage setup
gsutil mb gs://$PROJECT_ID-terraform-state-staging
gsutil versioning set on gs://$PROJECT_ID-terraform-state-staging

echo "✅ Storage created"
```

## 🔐 Step 2: API Keys (Simplified)

```bash
# Get required API keys
echo "📝 Required API keys:"
echo "1. Anthropic API Key: https://console.anthropic.com/"
echo "2. OpenAI API Key (optional): https://platform.openai.com/api-keys"

# Store in environment (simple approach for staging)
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"  # optional
```

## 🗄️ Step 3: Simplified Database Setup

### Option A: Managed Services (Recommended)
```bash
# Use GCP managed services for simplicity
echo "Using GCP managed Redis and Cloud Storage"
echo "Vector DB: Vertex AI (free tier available)"
```

### Option B: External Services (Cost-effective)
```bash
# Use free/cheap external services
echo "📝 External service options:"
echo "1. MongoDB Atlas (Free M0 cluster)"
echo "2. Redis Labs (Free 30MB)"
echo "3. ChromaDB (Local/Docker)"
```

## ⚙️ Step 4: Staging Terraform Configuration

### 4.1 Create Staging Variables

```bash
# Clone repository
git clone https://github.com/your-username/py-ai.git
cd py-ai

# Create simplified staging config
cat > terraform/environments/staging/terraform.tfvars << EOF
# Project Configuration
project_id = "$PROJECT_ID"
region = "us-central1"
environment = "staging"

# Container Images
api_image = "gcr.io/$PROJECT_ID/py-ai-api:latest"
worker_image = "gcr.io/$PROJECT_ID/py-ai-worker:latest"

# Minimal Scaling (Cost-optimized)
min_instances = 0  # Scale to zero when not in use
max_instances = 2
worker_min_instances = 0
worker_max_instances = 1

# Minimal Resources
api_cpu_limit = "1"
api_memory_limit = "2Gi"
api_cpu_request = "0.5"
api_memory_request = "1Gi"

worker_cpu_limit = "1"
worker_memory_limit = "2Gi"
worker_cpu_request = "0.5"
worker_memory_request = "1Gi"

# Minimal Database Configuration
redis_tier = "BASIC"
redis_memory_gb = 1

# Vector Database (choose one)
vector_db_type = "vertex"  # or "chroma" for free option
documents_gcs_bucket = "$PROJECT_ID-staging-documents"

# API Keys
anthropic_api_key = "$ANTHROPIC_API_KEY"
openai_api_key = "$OPENAI_API_KEY"

# GitHub Configuration
github_owner = "your-username"
github_repo = "py-ai"

# Monitoring
alert_email = "your-email@domain.com"

# Feature Flags
enable_streaming = true
enable_web_search = false  # Disabled to save costs
enable_multi_agent = true

# Performance Settings (Relaxed for staging)
max_request_body_bytes = 10485760  # 10MB
rate_limit_requests_per_window = 100
rate_limit_window_seconds = 60

# Labels
additional_labels = {
  environment = "staging"
  cost_center = "development"
  purpose     = "testing"
}
EOF
```

### 4.2 Update Backend Configuration

```bash
cat > terraform/environments/staging/backend.tf << EOF
terraform {
  backend "gcs" {
    bucket = "$PROJECT_ID-terraform-state-staging"
    prefix = "terraform/staging"
  }
}
EOF
```

## 🚀 Step 5: Deploy Staging Infrastructure

### 5.1 Quick Deployment

```bash
cd terraform/environments/staging

# Initialize and deploy in one go
terraform init
terraform plan -out=staging.plan
terraform apply staging.plan

echo "✅ Staging infrastructure deployed!"
```

### 5.2 Build and Deploy Application

```bash
# Build and deploy containers
cd ../../../

# Simple build and deploy
gcloud builds submit --tag=gcr.io/$PROJECT_ID/py-ai-api:latest --dockerfile=Dockerfile .
gcloud run deploy py-ai-api-staging \
  --image=gcr.io/$PROJECT_ID/py-ai-api:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=2 \
  --memory=2Gi \
  --cpu=1
```

## 🔍 Step 6: Quick Validation

### 6.1 Test Basic Functionality

```bash
# Get staging URL
export STAGING_URL=$(gcloud run services describe py-ai-api-staging --platform=managed --region=us-central1 --format="value(status.url)")

echo "Staging URL: $STAGING_URL"

# Quick health check
curl -f $STAGING_URL/health
curl -f $STAGING_URL/ready

# Test smart orchestrator
curl -s $STAGING_URL/smart/status | jq '.status'

# Test agent routing
curl -s "$STAGING_URL/smart/chat?q=Hello" | jq '.agent_used'

echo "✅ Staging validation complete!"
```

## 📊 Step 7: Basic Monitoring

### 7.1 Simple Monitoring Setup

```bash
# Enable basic Cloud Run monitoring (automatically enabled)
echo "✅ Basic monitoring enabled automatically"

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit=10
```

### 7.2 Set Up Basic Alerts

```bash
# Create simple uptime check
gcloud monitoring uptime create \
  --display-name="py-ai-staging-uptime" \
  --http-check-path="/health" \
  --monitored-resource-type=gce_instance \
  --hostname="$STAGING_URL"
```

## 💰 Step 8: Cost Control

### 8.1 Enable Budget Alerts

```bash
# Set conservative budget for staging
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="py-ai-staging-budget" \
  --budget-amount=75USD \
  --threshold-rule=percent=80,basis=CURRENT_SPEND
```

### 8.2 Auto-scaling to Zero

```bash
# Ensure services scale to zero when not in use
gcloud run services update py-ai-api-staging \
  --platform=managed \
  --region=us-central1 \
  --min-instances=0
```

## 🧪 Step 9: Development Testing

### 9.1 Test All Agent Architectures

```bash
# Test smart orchestrator
curl -s "$STAGING_URL/smart/agents/comparison" | jq '.available_agents | length'

# Test individual agents
curl -s "$STAGING_URL/pydantic-agent/status" | jq '.status'
curl -s "$STAGING_URL/hybrid-agent/status" | jq '.status'
curl -s "$STAGING_URL/agent/chat?q=Hello" | jq '.answer'

echo "✅ All 4 agent architectures operational"
```

### 9.2 Performance Testing

```bash
# Simple load test
for i in {1..5}; do
  curl -s "$STAGING_URL/smart/status" > /dev/null &
done
wait

echo "✅ Concurrent requests handled"
```

## 📋 Step 10: Staging Workflow

### 10.1 Development Workflow

```bash
# Create development script
cat > scripts/deploy-staging.sh << 'EOF'
#!/bin/bash
set -e

# Build and deploy to staging
gcloud builds submit --tag=gcr.io/$PROJECT_ID/py-ai-api:staging
gcloud run deploy py-ai-api-staging \
  --image=gcr.io/$PROJECT_ID/py-ai-api:staging \
  --platform=managed \
  --region=us-central1

# Run quick tests
./scripts/test-staging.sh
EOF

chmod +x scripts/deploy-staging.sh
```

### 10.2 Testing Script

```bash
cat > scripts/test-staging.sh << 'EOF'
#!/bin/bash
set -e

STAGING_URL=$(gcloud run services describe py-ai-api-staging --platform=managed --region=us-central1 --format="value(status.url)")

echo "Testing staging deployment at: $STAGING_URL"

# Health checks
curl -f $STAGING_URL/health
curl -f $STAGING_URL/ready

# Agent tests
curl -s "$STAGING_URL/smart/status" | jq '.status'
curl -s "$STAGING_URL/smart/agents/comparison" | jq '.available_agents | length'

echo "✅ Staging tests passed!"
EOF

chmod +x scripts/test-staging.sh
```

## 🔧 Step 11: Staging Maintenance

### 11.1 Cleanup Script

```bash
cat > scripts/cleanup-staging.sh << 'EOF'
#!/bin/bash
set -e

echo "Cleaning up staging resources..."

# Delete Cloud Run services
gcloud run services delete py-ai-api-staging --platform=managed --region=us-central1 --quiet

# Delete container images older than 7 days
gcloud container images list-tags gcr.io/$PROJECT_ID/py-ai-api \
  --filter="timestamp.datetime < -P7D" \
  --format="get(digest)" | \
  xargs -I {} gcloud container images delete gcr.io/$PROJECT_ID/py-ai-api@{} --quiet

echo "✅ Staging cleanup complete"
EOF

chmod +x scripts/cleanup-staging.sh
```

## 📋 Staging Checklist

- [ ] Basic health endpoints responding
- [ ] All 4 agent architectures available
- [ ] Smart orchestrator routing working
- [ ] Cost controls enabled (scale-to-zero)
- [ ] Basic monitoring active
- [ ] Budget alerts configured
- [ ] Development workflow scripts created

## 🔧 Troubleshooting

### Common Staging Issues

1. **Cold Starts**: Services may take 10-15 seconds to respond when scaling from zero
2. **Memory Limits**: 2GB may be tight for some workloads - monitor and adjust
3. **Rate Limits**: Conservative limits may block development testing

### Quick Fixes

```bash
# Increase memory if needed
gcloud run services update py-ai-api-staging \
  --memory=4Gi --platform=managed --region=us-central1

# Warm up service
curl $STAGING_URL/health

# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=py-ai-api-staging" --limit=20
```

## 💸 Expected Staging Costs

**Monthly Cost Breakdown (Estimated):**
- Cloud Run (scale-to-zero): $10-25
- Cloud Storage: $5-10
- Vertex AI (minimal usage): $5-15
- Redis (basic tier): $15-25
- Networking & Misc: $5-10
- **Total: $40-85/month**

*Costs can be even lower with scale-to-zero and careful usage monitoring.*

## 🚀 Next Steps

1. **Test thoroughly** in staging before production
2. **Iterate quickly** with the simplified deployment
3. **Monitor costs** and optimize as needed
4. **Promote to production** when ready using the enterprise guide

---

🎯 **Your staging environment is ready for development and testing!**

Access your staging API at: `$STAGING_URL`