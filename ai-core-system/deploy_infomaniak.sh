#!/bin/bash

# AI Core System - Infomaniak VPS Deployment Script
# This script deploys the AI Core System on an Infomaniak VPS
# Assumes the repository is already cloned and script is run from ai-core-system directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="ai-api.cryptomaltese.com"
EMAIL="admin@cryptomaltese.com"
APP_DIR="/opt/ai-core-system"
CURRENT_DIR="$(pwd)"

# Logging
LOG_FILE="/var/log/ai-core-deployment.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo -e "${BLUE}=== AI Core System Deployment Script ===${NC}"
echo "Starting deployment at $(date)"
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo "Current directory: $CURRENT_DIR"
echo "Target app directory: $APP_DIR"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Function to check if we're in the correct directory
check_directory() {
    if [[ ! -f "docker-compose.yml" ]] || [[ ! -f "Dockerfile" ]]; then
        print_error "This script must be run from the ai-core-system directory"
        print_error "Current directory: $CURRENT_DIR"
        print_error "Expected files: docker-compose.yml, Dockerfile"
        exit 1
    fi
    print_status "Directory check passed - running from ai-core-system directory"
}

# Function to update system
update_system() {
    print_status "Updating system packages..."
    apt-get update
    apt-get upgrade -y
    apt-get install -y curl wget git ufw fail2ban cron
}

# Function to install Docker
install_docker() {
    print_status "Installing Docker..."
    
    if command_exists docker; then
        print_warning "Docker is already installed"
        return
    fi
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Install Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    print_status "Docker installed successfully"
}

# Function to configure firewall
configure_firewall() {
    print_status "Configuring firewall..."
    
    # Reset firewall
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow API port (if not using reverse proxy)
    ufw allow 8000/tcp
    
    # Enable firewall
    ufw --force enable
    
    print_status "Firewall configured successfully"
}

# Function to configure fail2ban
configure_fail2ban() {
    print_status "Configuring fail2ban..."
    
    # Create fail2ban configuration
    cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3
EOF
    
    # Restart fail2ban
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    print_status "Fail2ban configured successfully"
}

# Function to configure cron service
configure_cron() {
    print_status "Configuring cron service..."
    
    # Start and enable cron service
    systemctl start cron
    systemctl enable cron
    
    # Verify cron is running
    if systemctl is-active --quiet cron; then
        print_status "Cron service is running"
    else
        print_warning "Cron service failed to start"
    fi
}

# Function to setup application directory
setup_app_directory() {
    print_status "Setting up application directory..."
    
    # Create target directory if it doesn't exist
    mkdir -p "$APP_DIR"
    
    # Create necessary subdirectories
    mkdir -p "$APP_DIR/logs"
    mkdir -p "$APP_DIR/cache"
    mkdir -p "$APP_DIR/models"
    mkdir -p "$APP_DIR/ssl"
    mkdir -p "$APP_DIR/backups"
    
    # Copy current directory contents to target directory
    print_status "Copying application files to $APP_DIR..."
    cp -r . "$APP_DIR/"
    
    # Set permissions
    chown -R root:root "$APP_DIR"
    chmod -R 755 "$APP_DIR"
    
    print_status "Application directory setup complete: $APP_DIR"
}

# Function to create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    
    cat > "$APP_DIR/.env" << EOF
# AI Core System Environment Configuration
# Generated on $(date)

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

# Authentication
API_KEYS=["your-production-api-key-1", "your-production-api-key-2"]
JWT_SECRET_KEY=$(openssl rand -hex 32)
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

# Cloudflare Configuration
CLOUDFLARE_ENABLED=false
CLOUDFLARE_API_TOKEN=
CLOUDFLARE_ZONE_ID=
CLOUDFLARE_DOMAIN=$DOMAIN

# Backup Configuration
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=/backups

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
DEPLOYMENT_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF
    
    print_status "Environment file created: $APP_DIR/.env"
    print_warning "Please edit the API keys and other sensitive settings in the .env file"
}

# Function to create model configuration
create_model_config() {
    print_status "Creating model configuration..."
    
    cat > "$APP_DIR/models.json" << EOF
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
EOF
    
    print_status "Model configuration created: $APP_DIR/models.json"
}

# Function to setup SSL certificates
setup_ssl() {
    print_status "Setting up SSL certificates..."
    
    # Install Certbot
    apt-get install -y certbot python3-certbot-nginx
    
    # Create self-signed certificate for initial setup
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$APP_DIR/ssl/key.pem" \
        -out "$APP_DIR/ssl/cert.pem" \
        -subj "/C=FR/ST=France/L=Paris/O=AI Core System/CN=$DOMAIN"
    
    # Copy SSL nginx configuration
    cp "$APP_DIR/nginx/nginx-ssl.conf" "$APP_DIR/nginx/nginx.conf"
    
    print_status "Self-signed SSL certificate created"
    print_warning "You should replace this with a proper certificate from Let's Encrypt"
}

# Function to create systemd service
create_systemd_service() {
    print_status "Creating systemd service..."
    
    cat > /etc/systemd/system/ai-core-system.service << EOF
[Unit]
Description=AI Core System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/bin/bash -c 'if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then docker-compose -f docker-compose-ssl.yml up -d; else docker-compose up -d; fi'
ExecStop=/bin/bash -c 'if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then docker-compose -f docker-compose-ssl.yml down; else docker-compose down; fi'
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd and enable service
    systemctl daemon-reload
    systemctl enable ai-core-system.service
    
    print_status "Systemd service created and enabled"
}

# Function to create backup script
create_backup_script() {
    print_status "Creating backup script..."
    
    cat > "$APP_DIR/backup.sh" << 'EOF'
#!/bin/bash

# AI Core System Backup Script

BACKUP_DIR="/opt/ai-core-system/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="ai-core-backup-$DATE.tar.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Stop services
cd /opt/ai-core-system
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    docker-compose -f docker-compose-ssl.yml down
else
    docker-compose down
fi

# Create backup
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude='./cache' \
    --exclude='./logs' \
    --exclude='./models' \
    .

# Start services
if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
    docker-compose -f docker-compose-ssl.yml up -d
else
    docker-compose up -d
fi

# Clean old backups (keep last 7 days)
find "$BACKUP_DIR" -name "ai-core-backup-*.tar.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
EOF
    
    chmod +x "$APP_DIR/backup.sh"
    
    # Add to crontab with error handling
    if command_exists crontab; then
        # Check if cron job already exists
        if ! crontab -l 2>/dev/null | grep -q "$APP_DIR/backup.sh"; then
            (crontab -l 2>/dev/null; echo "0 2 * * * $APP_DIR/backup.sh") | crontab -
            print_status "Backup script scheduled in crontab"
        else
            print_warning "Backup cron job already exists"
        fi
    else
        print_warning "crontab not available, backup script created but not scheduled"
        print_warning "You can manually schedule it with: crontab -e"
    fi
    
    print_status "Backup script created"
}

# Function to create monitoring setup
create_monitoring() {
    print_status "Setting up monitoring..."
    
    mkdir -p "$APP_DIR/monitoring"
    
    # Create Prometheus configuration
    cat > "$APP_DIR/monitoring/prometheus.yml" << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-core-api'
    static_configs:
      - targets: ['ai-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s
EOF
    
    print_status "Monitoring configuration created"
}

# Function to deploy application
deploy_application() {
    print_status "Deploying application..."
    
    cd "$APP_DIR"
    
    # Check if SSL is enabled
    if [[ -f "ssl/cert.pem" ]] && [[ -f "ssl/key.pem" ]]; then
        print_status "SSL certificates found, using SSL configuration..."
        docker-compose -f docker-compose-ssl.yml build
        docker-compose -f docker-compose-ssl.yml up -d
    else
        print_status "No SSL certificates found, using HTTP configuration..."
        docker-compose build
        docker-compose up -d
    fi
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 30
    
    # Check service status
    if docker-compose ps | grep -q "Up"; then
        print_status "Application deployed successfully"
    else
        print_error "Application deployment failed"
        docker-compose logs
        exit 1
    fi
}

# Function to setup Let's Encrypt SSL
setup_letsencrypt() {
    print_status "Setting up Let's Encrypt SSL certificate..."
    
    # Stop nginx temporarily
    cd "$APP_DIR"
    docker-compose down
    
    # Get certificate
    certbot certonly --standalone \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN"
    
    # Copy certificates
    cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem "$APP_DIR/ssl/cert.pem"
    cp /etc/letsencrypt/live/$DOMAIN/privkey.pem "$APP_DIR/ssl/key.pem"
    
    # Set permissions
    chmod 644 "$APP_DIR/ssl/cert.pem"
    chmod 600 "$APP_DIR/ssl/key.pem"
    
    # Copy SSL nginx configuration
    cp "$APP_DIR/nginx/nginx-ssl.conf" "$APP_DIR/nginx/nginx.conf"
    
    # Start services with SSL configuration
    docker-compose -f docker-compose-ssl.yml up -d
    
    # Setup auto-renewal with error handling
    if command_exists crontab; then
        # Check if SSL renewal job already exists
        if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
            (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet && cd $APP_DIR && docker-compose -f docker-compose-ssl.yml restart nginx") | crontab -
            print_status "SSL certificate auto-renewal scheduled"
        else
            print_warning "SSL renewal cron job already exists"
        fi
    else
        print_warning "crontab not available, SSL renewal not scheduled"
        print_warning "You can manually renew certificates with: certbot renew"
    fi
    
    print_status "Let's Encrypt SSL certificate configured"
}

# Function to display final information
display_final_info() {
    echo ""
    echo -e "${GREEN}=== Deployment Complete ===${NC}"
    echo ""
    echo "AI Core System has been deployed successfully!"
    echo ""
    echo "Service Information:"
    echo "  - API URL: https://$DOMAIN"
    echo "  - Health Check: https://$DOMAIN/health"
    echo "  - API Documentation: https://$DOMAIN/docs"
    echo "  - Application Directory: $APP_DIR"
    echo ""
    echo "Management Commands:"
    echo "  - Start services: systemctl start ai-core-system"
    echo "  - Stop services: systemctl stop ai-core-system"
    echo "  - View logs: docker-compose logs -f"
    echo "  - Backup: $APP_DIR/backup.sh"
    echo ""
    echo "Next Steps:"
    echo "1. Edit the API keys in $APP_DIR/.env"
    echo "2. Configure your models in $APP_DIR/models.json"
    echo "3. Test the API endpoints"
    echo "4. Set up monitoring (optional)"
    echo ""
    echo "Log file: $LOG_FILE"
    echo ""
}

# Main deployment function
main() {
    check_root
    check_directory
    
    print_status "Starting AI Core System deployment..."
    
    update_system
    install_docker
    configure_firewall
    configure_fail2ban
    configure_cron
    setup_app_directory
    create_env_file
    create_model_config
    setup_ssl
    create_systemd_service
    create_backup_script
    create_monitoring
    deploy_application
    
    # Ask if user wants to setup Let's Encrypt
    echo ""
    read -p "Do you want to setup Let's Encrypt SSL certificate? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_letsencrypt
    fi
    
    display_final_info
}

# Run main function
main "$@" 