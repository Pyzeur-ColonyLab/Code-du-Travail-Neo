# 🚀 Deployment Guide - Code du Travail Neo

This guide provides step-by-step instructions for deploying the three microservices that make up the Code du Travail Neo system.

## 📋 Prerequisites

### Required Accounts
- **Infomaniak Cloud Account**: For hosting the services
- **Domain Management**: Access to cryptomaltese.com DNS settings
- **Cloudflare Account**: For DNS management and SSL certificates
- **Telegram Bot Token**: From @BotFather
- **HuggingFace Token**: For accessing AI models

### Technical Requirements
- Basic knowledge of Docker and Docker Compose
- Familiarity with Linux command line
- Understanding of DNS and SSL certificates
- Experience with cloud deployment

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Main AI Core   │    │  Telegram Bot   │    │   Mail Service  │
│     System      │    │    Service      │    │                 │
│                 │    │                 │    │                 │
│ • API Server    │    │ • Bot Handler   │    │ • Email Monitor │
│ • Model Manager │    │ • Session Mgmt  │    │ • SMTP/IMAP     │
│ • Redis Cache   │    │ • Rate Limiting │    │ • Templates     │
│ • Health Check  │    │ • Webhook       │    │ • Queue Mgmt    │
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

### Phase 1: Main AI Core System
**Priority: HIGH** - Foundation for all other services

1. **Server Setup**: VPS Pro 4-8 on Infomaniak
2. **Domain Configuration**: ai-api.cryptomaltese.com
3. **SSL Certificate**: Let's Encrypt via Cloudflare
4. **Service Deployment**: Docker containers
5. **Testing**: API endpoints and model loading

### Phase 2: Telegram Service
**Priority: MEDIUM** - Lightweight, easy to test

1. **Server Setup**: VPS Pro 2-4 on Infomaniak
2. **Domain Configuration**: telegram.cryptomaltese.com
3. **Bot Configuration**: Webhook setup
4. **Service Deployment**: Docker containers
5. **Testing**: Bot commands and AI integration

### Phase 3: Mail Service
**Priority: MEDIUM** - Complex, requires email infrastructure

1. **Server Setup**: VPS Pro 4-8 on Infomaniak
2. **Domain Configuration**: mail.cryptomaltese.com
3. **Email Setup**: IMAP/SMTP configuration
4. **Service Deployment**: Docker containers
5. **Testing**: Email processing and AI responses

## 🔧 Detailed Deployment Steps

### Step 1: Infrastructure Preparation

#### 1.1 Create Infomaniak Instances

**Main AI Core System:**
```bash
# VPS Pro 4 or 8
Instance Type: VPS Pro 4
CPU: 4 vCPUs
RAM: 16 GB
Storage: 100 GB SSD
OS: Ubuntu 22.04 LTS
Network: 1 Gbps
```

**Telegram Service:**
```bash
# VPS Pro 2 or 4
Instance Type: VPS Pro 2
CPU: 2 vCPUs
RAM: 4 GB
Storage: 50 GB SSD
OS: Ubuntu 22.04 LTS
Network: 1 Gbps
```

**Mail Service:**
```bash
# VPS Pro 4 or 8
Instance Type: VPS Pro 4
CPU: 4 vCPUs
RAM: 8 GB
Storage: 100 GB SSD
OS: Ubuntu 22.04 LTS
Network: 1 Gbps
```

#### 1.2 DNS Configuration

Configure these records in Cloudflare for cryptomaltese.com:

```dns
# Main AI API
ai-api.cryptomaltese.com.      IN  A       MAIN_SERVER_IP

# Telegram Bot
telegram.cryptomaltese.com.    IN  A       TELEGRAM_SERVER_IP

# Mail Service
mail.cryptomaltese.com.        IN  A       MAIL_SERVER_IP
cryptomaltese.com.             IN  MX  10  mail.cryptomaltese.com.

# Email authentication
cryptomaltese.com.             IN  TXT     "v=spf1 mx ~all"
```

### Step 2: Main AI Core System Deployment

#### 2.1 Server Preparation

```bash
# Connect to your main AI server
ssh root@YOUR_MAIN_SERVER_IP

# Update system
apt update && apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install docker-compose -y

# Create application directory
mkdir -p /opt/ai-core-system
cd /opt/ai-core-system
```

#### 2.2 Environment Configuration

```bash
# Create environment file
cat > .env << 'EOF'
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
DEBUG=false

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=

# Model Configuration
MODEL_CONFIG_PATH=/app/models.json
MODEL_CACHE_DIR=/app/cache
DEFAULT_MODEL=mistral-7b-instruct

# Security
API_KEY_HEADER=X-API-Key
RATE_LIMIT_PER_MINUTE=60
MAX_PROMPT_LENGTH=4096

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
```

#### 2.3 SSL Certificate Setup

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate
certbot --nginx -d ai-api.cryptomaltese.com

# Test certificate renewal
certbot renew --dry-run
```

#### 2.4 Service Deployment

```bash
# Clone the specification repository
git clone https://github.com/your-username/Code-du-Travail-Neo.git
cd Code-du-Travail-Neo

# Follow the deployment instructions in 01_MAIN_SYSTEM_SPECIFICATION.txt
# This will include building Docker images and starting services
```

### Step 3: Telegram Service Deployment

#### 3.1 Server Preparation

```bash
# Connect to your Telegram server
ssh root@YOUR_TELEGRAM_SERVER_IP

# Update system and install Docker (same as above)
apt update && apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install docker-compose -y

# Create application directory
mkdir -p /opt/telegram-service
cd /opt/telegram-service
```

#### 3.2 Bot Configuration

```bash
# Get bot token from @BotFather on Telegram
# Create environment file
cat > .env << 'EOF'
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
WEBHOOK_URL=https://telegram.cryptomaltese.com/webhook
WEBHOOK_SECRET=your_webhook_secret

# AI System Configuration
AI_API_URL=https://ai-api.cryptomaltese.com
AI_API_KEY=your_api_key_here
DEFAULT_MODEL=mistral-7b-instruct

# Database Configuration
DATABASE_URL=postgresql://user:password@postgres:5432/telegram_bot
DB_USER=telegram_bot
DB_PASSWORD=secure_password

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
MAX_MESSAGES_PER_MINUTE=30
MAX_CONVERSATION_LENGTH=50
SESSION_TIMEOUT=3600

# Security
SECRET_KEY=your_secret_key_here
EOF
```

#### 3.3 SSL Certificate Setup

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate
certbot --nginx -d telegram.cryptomaltese.com
```

#### 3.4 Service Deployment

```bash
# Follow the deployment instructions in 02_TELEGRAM_SERVICE_SPECIFICATION.txt
# This will include building Docker images and starting services
```

### Step 4: Mail Service Deployment

#### 4.1 Server Preparation

```bash
# Connect to your mail server
ssh root@YOUR_MAIL_SERVER_IP

# Update system and install Docker (same as above)
apt update && apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
apt install docker-compose -y

# Create application directory
mkdir -p /opt/mail-service
cd /opt/mail-service
```

#### 4.2 Email Configuration

```bash
# Create environment file
cat > .env << 'EOF'
# AI System Configuration
AI_API_URL=https://ai-api.cryptomaltese.com
AI_API_KEY=your_api_key_here
DEFAULT_MODEL=mistral-7b-instruct

# Email Configuration
EMAIL_ADDRESS=ai@cryptomaltese.com
EMAIL_PASSWORD=secure_email_password
EMAIL_DOMAIN=cryptomaltese.com

# IMAP Configuration
IMAP_HOST=mail.cryptomaltese.com
IMAP_PORT=993
IMAP_SSL=true
IMAP_FOLDER=INBOX

# SMTP Configuration
SMTP_HOST=mail.cryptomaltese.com
SMTP_PORT=587
SMTP_SSL=true
SMTP_USERNAME=ai@cryptomaltese.com
SMTP_PASSWORD=secure_email_password

# Database Configuration
DATABASE_URL=postgresql://user:password@postgres:5432/mail_service
DB_USER=mail_service
DB_PASSWORD=secure_password

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
EMAIL_CHECK_INTERVAL=30
MAX_EMAILS_PER_HOUR=100
MAX_ATTACHMENT_SIZE=10485760
PROCESSING_TIMEOUT=300

# Security
SECRET_KEY=your_secret_key_here
ALLOWED_SENDERS=*
EOF
```

#### 4.3 SSL Certificate Setup

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate
certbot --nginx -d mail.cryptomaltese.com
```

#### 4.4 Service Deployment

```bash
# Follow the deployment instructions in 03_MAIL_SERVICE_SPECIFICATION.txt
# This will include building Docker images and starting services
```

## 🧪 Testing and Validation

### 1. Main AI Core System Tests

```bash
# Test API health
curl https://ai-api.cryptomaltese.com/api/v1/health

# Test model listing
curl -H "X-API-Key: your_api_key" \
     https://ai-api.cryptomaltese.com/api/v1/models

# Test generation endpoint
curl -X POST https://ai-api.cryptomaltese.com/api/v1/generate \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_key" \
     -d '{
       "model": "mistral-7b-instruct",
       "prompt": "Hello, how are you?",
       "max_tokens": 50
     }'
```

### 2. Telegram Service Tests

```bash
# Test webhook endpoint
curl -X POST https://telegram.cryptomaltese.com/webhook \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'

# Test bot commands via Telegram
# Send /start to your bot
# Send /help to your bot
# Send a test message
```

### 3. Mail Service Tests

```bash
# Test service health
curl https://mail.cryptomaltese.com/health

# Test email processing
# Send an email to ai@cryptomaltese.com
# Check if you receive an AI-generated response
```

## 📊 Monitoring Setup

### 1. Health Checks

Create monitoring scripts for each service:

```bash
#!/bin/bash
# health_check.sh

# Main AI Core System
curl -f https://ai-api.cryptomaltese.com/api/v1/health || echo "AI Core System DOWN"

# Telegram Service
curl -f https://telegram.cryptomaltese.com/health || echo "Telegram Service DOWN"

# Mail Service
curl -f https://mail.cryptomaltese.com/health || echo "Mail Service DOWN"
```

### 2. Log Monitoring

```bash
# Monitor logs for each service
docker-compose logs -f ai-api
docker-compose logs -f telegram-bot
docker-compose logs -f mail-service
```

### 3. Resource Monitoring

```bash
# Monitor system resources
htop
df -h
free -h
```

## 🔒 Security Considerations

### 1. Firewall Configuration

```bash
# Configure UFW firewall
ufw allow ssh
ufw allow 80
ufw allow 443
ufw enable
```

### 2. API Key Management

- Store API keys securely in environment variables
- Rotate API keys regularly
- Use different API keys for different services
- Monitor API key usage

### 3. SSL/TLS Configuration

- Use Let's Encrypt certificates
- Configure automatic renewal
- Use strong SSL/TLS settings
- Enable HSTS headers

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
   docker ps -a
   
   # Check container logs
   docker logs container_name
   
   # Restart services
   docker-compose restart
   ```

3. **DNS Issues**
   ```bash
   # Check DNS resolution
   nslookup ai-api.cryptomaltese.com
   dig ai-api.cryptomaltese.com
   ```

4. **API Connection Issues**
   ```bash
   # Test API connectivity
   curl -v https://ai-api.cryptomaltese.com/api/v1/health
   
   # Check firewall rules
   ufw status
   ```

## 📈 Scaling Considerations

### 1. Horizontal Scaling

- Use load balancers for multiple instances
- Implement shared Redis clusters
- Use shared PostgreSQL databases
- Configure auto-scaling policies

### 2. Performance Optimization

- Monitor resource usage
- Optimize Docker configurations
- Implement caching strategies
- Use CDN for static content

### 3. Backup Strategies

- Regular database backups
- Configuration file backups
- SSL certificate backups
- Disaster recovery plans

## 📞 Support

For deployment issues or questions:

1. Check the individual specification files for detailed instructions
2. Review the troubleshooting section above
3. Check service logs for error messages
4. Verify network connectivity and DNS settings
5. Ensure all environment variables are correctly set

---

**Happy Deploying! 🚀** 