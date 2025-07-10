# 🔧 Pre-Deployment Setup Guide

This guide helps you set up the environment and DNS configuration before running the deployment script.

## 📋 Prerequisites Checklist

Before running the deployment script, ensure you have:

- [ ] **Infomaniak VPS** with Ubuntu 22.04/Debian 12
- [ ] **Domain access** to cryptomaltese.com DNS settings
- [ ] **Server IP address** from your VPS
- [ ] **Root access** to the server
- [ ] **GitHub access** to the repository

## 🌐 Step 1: DNS Configuration

### 1.1 Get Your Server IP
```bash
# On your server, get the public IP
curl ifconfig.me
# or
curl ipinfo.io/ip
```

### 1.2 Configure DNS Records

In your domain registrar or DNS provider (Cloudflare, etc.), add these records:

```dns
# Main AI API subdomain
Type: A
Name: ai
Value: YOUR_SERVER_IP
TTL: 300

# Optional: www subdomain for the API
Type: A
Name: www.ai
Value: YOUR_SERVER_IP
TTL: 300
```

### 1.3 Verify DNS Propagation
```bash
# Check if DNS is propagating
dig ai.cryptomaltese.com
host ai.cryptomaltese.com

# Wait for propagation (can take up to 24 hours)
# Usually takes 5-15 minutes for most providers
```

## 🔑 Step 2: Environment Configuration

### 2.1 Create Environment File Locally

Create a `.env` file in the `ai-core-system` directory:

```bash
cd ai-core-system
cp env.example .env
nano .env
```

### 2.2 Configure Environment Variables

Edit the `.env` file with your specific configuration:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
DEBUG=false
LOG_LEVEL=INFO
LOG_FORMAT=json

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_MAX_CONNECTIONS=20
REDIS_TIMEOUT=5

# Model Configuration
MODEL_CONFIG_PATH=/app/models.json
MODEL_CACHE_DIR=/app/cache
DEFAULT_MODEL=mistral-7b-instruct
MODEL_LOAD_TIMEOUT=300
MODEL_UNLOAD_TIMEOUT=60

# Security Configuration
API_KEY_HEADER=X-API-Key
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
MAX_PROMPT_LENGTH=4096
MAX_TOKENS_PER_REQUEST=2048
ALLOWED_ORIGINS=["*"]
ENABLE_CORS=true

# Authentication (IMPORTANT: Change these!)
API_KEYS=["your-secure-production-api-key-1", "your-secure-production-api-key-2"]
JWT_SECRET_KEY=your-secure-jwt-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Monitoring and Metrics
ENABLE_METRICS=true
METRICS_PORT=9090
HEALTH_CHECK_INTERVAL=30
PROMETHEUS_ENABLED=true

# SSL/TLS Configuration
SSL_ENABLED=true
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# Domain Configuration
DOMAIN=ai.cryptomaltese.com
EMAIL=admin@cryptomaltese.com

# Performance Configuration
WORKER_PROCESSES=4
WORKER_THREADS=2
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=300
KEEP_ALIVE_TIMEOUT=5

# Model Memory Management
MAX_MODEL_MEMORY_GB=16
MODEL_QUANTIZATION=4bit
ENABLE_MODEL_CACHING=true
MODEL_CACHE_TTL=3600

# Logging Configuration
LOG_FILE_PATH=/app/logs/ai-api.log
LOG_MAX_SIZE_MB=100
LOG_BACKUP_COUNT=5

# Development Configuration
RELOAD_ON_CHANGE=false
ENABLE_DEBUG_ENDPOINTS=false
ENABLE_SWAGGER_UI=true
ENABLE_REDOC=true

# Deployment Configuration
DEPLOYMENT_ENVIRONMENT=production
DEPLOYMENT_VERSION=1.0.0
```

### 2.3 Generate Secure Keys

Generate secure API keys and secrets:

```bash
# Generate API keys
openssl rand -hex 32
# Use this output for API_KEYS

# Generate JWT secret
openssl rand -hex 32
# Use this output for JWT_SECRET_KEY
```

## 🎯 Step 3: Model Configuration

### 3.1 Configure Models

Edit the `models.json` file:

```json
{
  "models": {
    "mistral-7b-instruct": {
      "type": "transformers",
      "path": "mistralai/Mistral-7B-Instruct-v0.3",
      "format": "safetensor",
      "device": "auto",
      "quantization": "4bit",
      "max_memory": "8GB",
      "context_length": 4096,
      "threads": 8
    },
    "llama-2-7b-chat": {
      "type": "gguf",
      "path": "/models/llama-2-7b-chat.gguf",
      "format": "gguf",
      "device": "cpu",
      "quantization": "4bit",
      "max_memory": "4GB",
      "context_length": 4096,
      "threads": 8
    }
  }
}
```

## 🚀 Step 4: Deployment Options

### Option A: Deploy with Self-Signed SSL (Quick Start)

```bash
# 1. Clone repository
git clone https://github.com/Pyzeur-ColonyLab/Code-du-Travail-Neo.git
cd Code-du-Travail-Neo/ai-core-system

# 2. Run deployment script
chmod +x deploy_infomaniak.sh
sudo ./deploy_infomaniak.sh

# 3. When asked about Let's Encrypt, choose 'n' for now
# The script will use self-signed certificates
```

### Option B: Deploy with Let's Encrypt SSL (Recommended)

**Prerequisites:**
- DNS must be properly configured and propagated
- Domain must point to your server IP
- Port 80 must be accessible from the internet

```bash
# 1. Verify DNS is working
dig ai.cryptomaltese.com
# Should return your server IP

# 2. Clone and deploy
git clone https://github.com/Pyzeur-ColonyLab/Code-du-Travail-Neo.git
cd Code-du-Travail-Neo/ai-core-system

# 3. Run deployment script
chmod +x deploy_infomaniak.sh
sudo ./deploy_infomaniak.sh

# 4. When asked about Let's Encrypt, choose 'y'
# The script will obtain proper SSL certificates
```

## 🔍 Step 5: Verification

### 5.1 Check Service Status
```bash
# Check if services are running
docker ps

# Check systemd service
systemctl status ai-core-system

# View logs
docker-compose logs -f
```

### 5.2 Test API Endpoints
```bash
# Test health endpoint
curl http://localhost/health

# Test with domain (after DNS setup)
curl https://ai.cryptomaltese.com/health

# Test API with key
curl -H "X-API-Key: your-api-key" \
     https://ai.cryptomaltese.com/api/v1/models
```

## 🚨 Troubleshooting

### DNS Issues
```bash
# Check DNS propagation
dig ai.cryptomaltese.com
host ai.cryptomaltese.com

# Check if domain resolves to your IP
host ai.cryptomaltese.com
```

### SSL Certificate Issues
```bash
# Check certificate status
certbot certificates

# Test SSL connection
openssl s_client -connect ai.cryptomaltese.com:443

# Renew certificates manually
certbot renew
```

### Service Issues
```bash
# Check container status
docker-compose ps

# View container logs
docker-compose logs ai-api
docker-compose logs nginx

# Restart services
docker-compose restart
```

## 📞 Next Steps

After successful deployment:

1. **Test all API endpoints**
2. **Configure monitoring** (optional)
3. **Set up backup verification**
4. **Monitor system resources**
5. **Configure additional security** (firewall rules, etc.)

---

**Ready to deploy?** Make sure you've completed all the steps above before running the deployment script! 🚀 