# 🚀 AI Core System Deployment Guide

This guide provides step-by-step instructions for deploying the AI Core System on an Infomaniak VPS.

## 📋 Prerequisites

### Required Accounts
- **Infomaniak Cloud Account**: For hosting the service
- **Domain Management**: Access to cryptomaltese.com DNS settings
- **GitHub Account**: For accessing the repository

### Technical Requirements
- Ubuntu 22.04 LTS or Debian 12 server
- Root access to the server
- Basic knowledge of Docker and command line

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   AI API        │    │   Redis Cache   │
│   (SSL/HTTP)    │    │   (FastAPI)     │    │                 │
│                 │    │                 │    │                 │
│ • SSL Termination│   │ • Model Manager │    │ • Response Cache│
│ • Rate Limiting │    │ • API Endpoints │    │ • Session Store │
│ • Load Balancing│    │ • Health Checks │    │ • Queue Mgmt    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Domain & DNS  │
                    │ cryptomaltese.com│
                    └─────────────────┘
```

## 🎯 Deployment Strategy

### Phase 1: Server Setup
1. **Server Preparation**: VPS Pro 4-8 on Infomaniak
2. **Domain Configuration**: ai-api.cryptomaltese.com
3. **SSL Certificate**: Let's Encrypt via Certbot
4. **Service Deployment**: Docker containers
5. **Testing**: API endpoints and model loading

## 🔧 Detailed Deployment Steps

### Step 1: Server Preparation

#### 1.1 Connect to Your Server
```bash
ssh root@YOUR_SERVER_IP
```

#### 1.2 Update System
```bash
apt update && apt upgrade -y
```

### Step 2: Repository Setup

#### 2.1 Clone the Repository
```bash
# Clone the main repository
git clone https://github.com/your-username/Code-du-Travail-Neo.git
cd Code-du-Travail-Neo/ai-core-system

# Verify you're in the correct directory
ls -la
# Should show: docker-compose.yml, Dockerfile, deploy_infomaniak.sh, etc.
```

#### 2.2 Run the Deployment Script
```bash
# Make the script executable
chmod +x deploy_infomaniak.sh

# Run the deployment script
sudo ./deploy_infomaniak.sh
```

### Step 3: What the Script Does

The deployment script automatically handles:

1. **System Updates**: Updates packages and installs dependencies
2. **Docker Installation**: Installs Docker and Docker Compose
3. **Security Setup**: Configures firewall and fail2ban
4. **Application Setup**: Copies files to `/opt/ai-core-system`
5. **Configuration**: Creates environment and model configuration files
6. **SSL Setup**: Creates self-signed certificates (can be upgraded to Let's Encrypt)
7. **Service Management**: Creates systemd service for auto-start
8. **Backup Setup**: Configures automated backups
9. **Monitoring**: Sets up basic monitoring

### Step 4: Post-Deployment Configuration

#### 4.1 Edit Environment Configuration
```bash
nano /opt/ai-core-system/.env
```

**Important settings to configure:**
```bash
# API Keys (REQUIRED)
API_KEYS=["your-production-api-key-1", "your-production-api-key-2"]

# Model Configuration
DEFAULT_MODEL=mistral-7b-instruct

# Security Settings
RATE_LIMIT_PER_MINUTE=60
MAX_PROMPT_LENGTH=4096
```

#### 4.2 Configure Models
```bash
nano /opt/ai-core-system/models.json
```

**Example model configuration:**
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

### Step 5: SSL Certificate Setup

#### 5.1 Let's Encrypt SSL (Recommended)
```bash
# The script will prompt you to setup Let's Encrypt
# If you choose 'y', it will automatically:
# - Stop nginx temporarily
# - Obtain SSL certificate
# - Configure nginx for SSL
# - Restart services with SSL
```

#### 5.2 Manual SSL Setup (Alternative)
```bash
cd /opt/ai-core-system

# Get certificate
certbot certonly --standalone \
    --email admin@cryptomaltese.com \
    --agree-tos \
    --no-eff-email \
    -d ai-api.cryptomaltese.com

# Copy certificates
cp /etc/letsencrypt/live/ai-api.cryptomaltese.com/fullchain.pem ssl/cert.pem
cp /etc/letsencrypt/live/ai-api.cryptomaltese.com/privkey.pem ssl/key.pem

# Restart with SSL
docker-compose -f docker-compose-ssl.yml down
docker-compose -f docker-compose-ssl.yml up -d
```

## 🧪 Testing and Validation

### 1. Health Check
```bash
# Test basic health
curl http://localhost/health

# Test with domain (after DNS setup)
curl https://ai-api.cryptomaltese.com/health
```

### 2. API Testing
```bash
# Test model listing
curl -H "X-API-Key: your-api-key" \
     https://ai-api.cryptomaltese.com/api/v1/models

# Test generation
curl -X POST https://ai-api.cryptomaltese.com/api/v1/generate \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-api-key" \
     -d '{
       "model": "mistral-7b-instruct",
       "prompt": "Hello, how are you?",
       "max_tokens": 50
     }'
```

### 3. Service Status
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Check systemd service
systemctl status ai-core-system
```

## 📊 Management Commands

### Service Management
```bash
# Start services
systemctl start ai-core-system

# Stop services
systemctl stop ai-core-system

# Restart services
systemctl restart ai-core-system

# View service status
systemctl status ai-core-system
```

### Docker Management
```bash
cd /opt/ai-core-system

# View running containers
docker-compose ps

# View logs
docker-compose logs -f

# Restart specific service
docker-compose restart ai-api

# Update and rebuild
git pull
docker-compose build
docker-compose up -d
```

### Backup and Maintenance
```bash
# Manual backup
/opt/ai-core-system/backup.sh

# View backup files
ls -la /opt/ai-core-system/backups/

# Check disk usage
df -h

# Monitor system resources
htop
```

## 🔒 Security Considerations

### 1. API Key Management
- Use strong, unique API keys
- Rotate keys regularly
- Monitor API key usage
- Store keys securely in environment variables

### 2. Firewall Configuration
The script automatically configures:
- SSH access only
- HTTP (80) and HTTPS (443) ports
- API port (8000) if needed
- Rate limiting via nginx

### 3. SSL/TLS Security
- Uses Let's Encrypt certificates
- Automatic renewal setup
- Strong SSL/TLS configuration
- HSTS headers enabled

## 🚨 Troubleshooting

### Common Issues

1. **SSL Certificate Issues**
   ```bash
   # Check certificate status
   certbot certificates
   
   # Renew certificates manually
   certbot renew
   ```

2. **Docker Issues**
   ```bash
   # Check container status
   docker-compose ps -a
   
   # Check container logs
   docker-compose logs container_name
   
   # Restart services
   docker-compose restart
   ```

3. **API Connection Issues**
   ```bash
   # Test API connectivity
   curl -v http://localhost/health
   
   # Check firewall rules
   ufw status
   ```

4. **Memory Issues**
   ```bash
   # Check memory usage
   free -h
   
   # Check Docker memory usage
   docker stats
   ```

### Log Locations
```bash
# Application logs
tail -f /opt/ai-core-system/logs/ai-api.log

# Docker logs
docker-compose logs -f

# System logs
journalctl -u ai-core-system -f

# Nginx logs
docker-compose logs nginx
```

## 📈 Monitoring and Scaling

### 1. Resource Monitoring
```bash
# Monitor system resources
htop
df -h
free -h

# Monitor Docker resources
docker stats
```

### 2. Application Monitoring
```bash
# Check API metrics
curl https://ai-api.cryptomaltese.com/metrics

# Monitor response times
curl -w "@curl-format.txt" https://ai-api.cryptomaltese.com/health
```

### 3. Scaling Considerations
- Monitor memory usage for model loading
- Consider horizontal scaling for high traffic
- Implement load balancing for multiple instances
- Use shared Redis clusters for caching

## 📞 Support

For deployment issues:

1. Check the troubleshooting section above
2. Review service logs for error messages
3. Verify network connectivity and DNS settings
4. Ensure all environment variables are correctly set
5. Check system resources (CPU, memory, disk)

---

**Happy Deploying! 🚀** 