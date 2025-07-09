# AI Core System - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the AI Core System to an Infomaniak VPS instance. The system is designed to run on Ubuntu 22.04 LTS with Docker and provides a scalable AI API service.

## Prerequisites

### Local Development Environment
- macOS (for local development)
- Docker Desktop
- Git
- SSH key pair for server access

### Server Requirements
- Infomaniak VPS Pro 4 or VPS Pro 8
- Ubuntu 22.04 LTS
- At least 16GB RAM (32GB recommended)
- 100GB+ SSD storage
- Public IP address
- Domain name (e.g., ai-api.cryptomaltese.com)

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   AI Core API   │    │   Redis Cache   │
│   (SSL/TLS)     │◄──►│   (FastAPI)     │◄──►│   (Session)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SSL Cert      │    │   AI Models     │    │   Monitoring    │
│   (Let's Encrypt)│    │   (GGUF/SafeT)  │    │   (Prometheus)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Deployment Steps

### 1. Local Setup

#### Clone the Repository
```bash
git clone <repository-url>
cd ai-core-system
```

#### Configure Environment
```bash
# Copy environment template
cp env.example .env

# Edit configuration
nano .env
```

Key configuration options:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Redis Configuration
REDIS_URL=redis://redis:6379

# Model Configuration
DEFAULT_MODEL=mistral-7b-instruct
MODEL_CONFIG_PATH=/app/config/models.json

# Security
API_KEY_HEADER=X-API-Key
DEFAULT_API_KEY=your-secure-api-key-here
ADMIN_API_KEY=your-admin-api-key-here

# Domain
DOMAIN_NAME=ai-api.cryptomaltese.com
```

#### Test Local Deployment
```bash
# Start services
docker-compose up -d

# Check logs
docker-compose logs -f ai-api

# Test API
curl -H "X-API-Key: your-secure-api-key-here" \
     http://localhost:8000/health
```

### 2. Server Preparation

#### Connect to VPS
```bash
ssh root@your-vps-ip
```

#### Update System
```bash
apt update && apt upgrade -y
```

#### Install Required Packages
```bash
apt install -y \
    curl \
    wget \
    git \
    ufw \
    certbot \
    python3-certbot-nginx \
    nginx \
    jq
```

### 3. Automated Deployment

#### Run Deployment Script
```bash
# Make script executable
chmod +x scripts/deploy_infomaniak.sh

# Run deployment
./scripts/deploy_infomaniak.sh
```

The script will:
1. Install Docker and Docker Compose
2. Setup SSL certificates
3. Configure firewall
4. Deploy the application
5. Setup monitoring (optional)

#### Manual Deployment Steps

If you prefer manual deployment:

##### Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Add user to docker group
usermod -aG docker $USER

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

##### Deploy Application
```bash
# Create deployment directory
mkdir -p /opt/ai-core-system
cd /opt/ai-core-system

# Copy application files (from local machine)
scp -r . root@your-vps-ip:/opt/ai-core-system/

# Create necessary directories
mkdir -p models cache logs backups nginx/ssl

# Build and start services
docker-compose build
docker-compose up -d
```

### 4. SSL Certificate Setup

#### Automatic Setup
```bash
# Make script executable
chmod +x scripts/setup_ssl.sh

# Run SSL setup
sudo ./scripts/setup_ssl.sh
```

#### Manual SSL Setup
```bash
# Install certbot
apt install -y certbot python3-certbot-nginx

# Obtain certificate
certbot certonly --standalone \
    --email admin@cryptomaltese.com \
    --agree-tos \
    --no-eff-email \
    --domains ai-api.cryptomaltese.com

# Setup nginx with SSL
# (See nginx/nginx.conf for configuration)
```

### 5. DNS Configuration

#### Update DNS Records
In your domain registrar or DNS provider:

```
Type: A
Name: ai-api
Value: your-vps-ip
TTL: 300
```

#### Verify DNS
```bash
nslookup ai-api.cryptomaltese.com
dig ai-api.cryptomaltese.com
```

### 6. Firewall Configuration

#### Setup UFW
```bash
# Reset firewall
ufw --force reset

# Set default policies
ufw default deny incoming
ufw default allow outgoing

# Allow SSH
ufw allow ssh

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw --force enable

# Check status
ufw status verbose
```

## Configuration

### Model Configuration

Edit `config/models.json` to configure available models:

```json
{
  "models": {
    "mistral-7b-instruct": {
      "type": "transformers",
      "path": "mistralai/Mistral-7B-Instruct-v0.3",
      "format": "safetensor",
      "device": "auto",
      "quantization": "4bit",
      "max_memory": "8GB"
    }
  }
}
```

### Nginx Configuration

The Nginx configuration is located in `nginx/nginx.conf` and includes:
- SSL termination
- Reverse proxy to FastAPI
- Rate limiting
- Security headers
- Gzip compression

### Environment Variables

Key environment variables in `.env`:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Redis Configuration
REDIS_URL=redis://redis:6379

# Model Configuration
DEFAULT_MODEL=mistral-7b-instruct
MODEL_CONFIG_PATH=/app/config/models.json

# Security
API_KEY_HEADER=X-API-Key
DEFAULT_API_KEY=your-secure-api-key
ADMIN_API_KEY=your-admin-api-key

# Performance
API_WORKERS=4
RATE_LIMIT_PER_MINUTE=60
MAX_PROMPT_LENGTH=4096
```

## Monitoring

### Health Checks
```bash
# Check service status
docker-compose ps

# Check application health
curl https://ai-api.cryptomaltese.com/health

# Check logs
docker-compose logs -f ai-api
```

### Metrics
```bash
# Get system metrics
curl -H "X-API-Key: your-api-key" \
     https://ai-api.cryptomaltese.com/api/v1/metrics
```

### Prometheus/Grafana (Optional)
```bash
# Start monitoring services
docker-compose --profile monitoring up -d

# Access Grafana
# URL: https://ai-api.cryptomaltese.com:3000
# Username: admin
# Password: admin
```

## API Usage

### Authentication
All API requests require an API key in the header:
```bash
X-API-Key: your-secure-api-key
```

### Text Generation
```bash
curl -X POST "https://ai-api.cryptomaltese.com/api/v1/generate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-7b-instruct",
    "prompt": "What is French labor law?",
    "max_tokens": 512,
    "temperature": 0.7
  }'
```

### Chat Conversation
```bash
curl -X POST "https://ai-api.cryptomaltese.com/api/v1/chat" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-7b-instruct",
    "messages": [
      {"role": "user", "content": "Hello"},
      {"role": "assistant", "content": "Hi there!"},
      {"role": "user", "content": "How are you?"}
    ]
  }'
```

### Model Management
```bash
# List models
curl -H "X-API-Key: your-api-key" \
     https://ai-api.cryptomaltese.com/api/v1/models

# Load model
curl -X POST "https://ai-api.cryptomaltese.com/api/v1/models/load" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral-7b-instruct"}'

# Unload model
curl -X POST "https://ai-api.cryptomaltese.com/api/v1/models/unload" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral-7b-instruct"}'
```

## Maintenance

### Backup
```bash
# Backup configuration
tar -czf backup-$(date +%Y%m%d).tar.gz \
    config/ models/ logs/ .env

# Backup Redis data
docker exec ai-core-redis redis-cli BGSAVE
```

### Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### SSL Certificate Renewal
```bash
# Manual renewal
certbot renew

# Check renewal status
certbot certificates
```

### Log Rotation
```bash
# Configure log rotation
cat > /etc/logrotate.d/ai-core << EOF
/opt/ai-core-system/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
```

## Troubleshooting

### Common Issues

#### Service Not Starting
```bash
# Check logs
docker-compose logs ai-api

# Check system resources
free -h
df -h

# Check Docker status
systemctl status docker
```

#### SSL Certificate Issues
```bash
# Check certificate status
certbot certificates

# Test SSL connection
openssl s_client -connect ai-api.cryptomaltese.com:443

# Renew certificate
certbot renew --force-renewal
```

#### Model Loading Issues
```bash
# Check model configuration
cat config/models.json

# Check available memory
free -h

# Check model files
ls -la models/
```

#### API Authentication Issues
```bash
# Check API key in headers
curl -v -H "X-API-Key: your-api-key" \
     https://ai-api.cryptomaltese.com/api/v1/models

# Check environment variables
docker-compose exec ai-api env | grep API_KEY
```

### Performance Optimization

#### Memory Management
```bash
# Monitor memory usage
docker stats

# Adjust model quantization
# Edit config/models.json to use 4bit quantization
```

#### Caching
```bash
# Check Redis cache
docker exec ai-core-redis redis-cli INFO memory

# Clear cache if needed
docker exec ai-core-redis redis-cli FLUSHDB
```

#### Load Balancing
```bash
# Scale API workers
# Edit .env: API_WORKERS=8

# Restart services
docker-compose restart ai-api
```

## Security Considerations

### API Key Management
- Use strong, unique API keys
- Rotate keys regularly
- Use different keys for different services
- Monitor API key usage

### Network Security
- Keep firewall rules minimal
- Use HTTPS for all communications
- Implement rate limiting
- Monitor access logs

### Model Security
- Validate all inputs
- Implement content filtering
- Monitor model usage
- Regular security updates

## Support

### Documentation
- API Documentation: https://ai-api.cryptomaltese.com/docs
- OpenAPI Spec: https://ai-api.cryptomaltese.com/openapi.json

### Monitoring
- Health Check: https://ai-api.cryptomaltese.com/health
- Metrics: https://ai-api.cryptomaltese.com/api/v1/metrics

### Logs
```bash
# Application logs
docker-compose logs -f ai-api

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# System logs
journalctl -u docker
journalctl -u nginx
```

## Next Steps

1. **Integration**: Connect Telegram and Email services
2. **Scaling**: Add load balancer and multiple instances
3. **Monitoring**: Setup comprehensive monitoring and alerting
4. **Backup**: Implement automated backup strategy
5. **Security**: Regular security audits and updates

---

For additional support, refer to the main documentation or contact the development team. 