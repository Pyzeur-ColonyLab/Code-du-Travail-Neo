#!/bin/bash

# AI Core System - Infomaniak Deployment Script
# This script deploys the AI Core System to an Infomaniak VPS

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
VPS_IP=""
VPS_USER="root"
SSH_KEY="~/.ssh/id_rsa"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
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

# Function to get user input
get_input() {
    local prompt="$1"
    local default="$2"
    local input
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " input
        echo "${input:-$default}"
    else
        read -p "$prompt: " input
        echo "$input"
    fi
}

# Function to validate IP address
validate_ip() {
    local ip=$1
    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        OIFS=$IFS
        IFS='.'
        ip=($ip)
        IFS=$OIFS
        [[ ${ip[0]} -le 255 && ${ip[1]} -le 255 && ${ip[2]} -le 255 && ${ip[3]} -le 255 ]]
    else
        return 1
    fi
}

# Function to test SSH connection
test_ssh() {
    local host="$1"
    local user="$2"
    local key="$3"
    
    print_status "Testing SSH connection to $user@$host..."
    
    if ssh -o ConnectTimeout=10 -o BatchMode=yes -i "$key" "$user@$host" "echo 'SSH connection successful'" 2>/dev/null; then
        print_success "SSH connection established"
        return 0
    else
        print_error "SSH connection failed"
        return 1
    fi
}

# Function to install Docker on remote server
install_docker() {
    local host="$1"
    local user="$2"
    local key="$3"
    
    print_status "Installing Docker on remote server..."
    
    ssh -i "$key" "$user@$host" << 'EOF'
        # Update system
        apt-get update
        
        # Install required packages
        apt-get install -y \
            apt-transport-https \
            ca-certificates \
            curl \
            gnupg \
            lsb-release \
            software-properties-common
        
        # Add Docker's official GPG key
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        
        # Add Docker repository
        echo \
            "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
            $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
        
        # Install Docker
        apt-get update
        apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        
        # Start and enable Docker
        systemctl start docker
        systemctl enable docker
        
        # Add user to docker group
        usermod -aG docker $USER
        
        # Install Docker Compose
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        
        # Verify installation
        docker --version
        docker-compose --version
EOF
    
    print_success "Docker installed successfully"
}

# Function to setup SSL certificates
setup_ssl() {
    local host="$1"
    local user="$2"
    local key="$3"
    local domain="$4"
    local email="$5"
    
    print_status "Setting up SSL certificates for $domain..."
    
    ssh -i "$key" "$user@$host" << EOF
        # Install certbot
        apt-get update
        apt-get install -y certbot
        
        # Create SSL directory
        mkdir -p /etc/nginx/ssl
        
        # Generate self-signed certificate for initial setup
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout /etc/nginx/ssl/key.pem \
            -out /etc/nginx/ssl/cert.pem \
            -subj "/C=FR/ST=State/L=City/O=Organization/CN=$domain"
        
        # Set permissions
        chmod 600 /etc/nginx/ssl/key.pem
        chmod 644 /etc/nginx/ssl/cert.pem
EOF
    
    print_success "SSL certificates setup completed"
}

# Function to deploy application
deploy_app() {
    local host="$1"
    local user="$2"
    local key="$3"
    
    print_status "Deploying AI Core System..."
    
    # Create deployment directory
    ssh -i "$key" "$user@$host" "mkdir -p /opt/ai-core-system"
    
    # Copy application files
    print_status "Copying application files..."
    scp -i "$key" -r . "$user@$host:/opt/ai-core-system/"
    
    # Create necessary directories
    ssh -i "$key" "$user@$host" << 'EOF'
        cd /opt/ai-core-system
        mkdir -p models cache logs backups nginx/ssl
        chmod 755 models cache logs backups nginx/ssl
EOF
    
    # Copy environment file
    if [ -f ".env" ]; then
        scp -i "$key" .env "$user@$host:/opt/ai-core-system/"
    else
        print_warning "No .env file found. Please create one manually."
    fi
    
    # Build and start containers
    print_status "Building and starting containers..."
    ssh -i "$key" "$user@$host" << 'EOF'
        cd /opt/ai-core-system
        
        # Build images
        docker-compose build
        
        # Start services
        docker-compose up -d
        
        # Wait for services to be ready
        sleep 30
        
        # Check service status
        docker-compose ps
EOF
    
    print_success "Application deployed successfully"
}

# Function to setup firewall
setup_firewall() {
    local host="$1"
    local user="$2"
    local key="$3"
    
    print_status "Setting up firewall..."
    
    ssh -i "$key" "$user@$host" << 'EOF'
        # Install UFW if not present
        apt-get update
        apt-get install -y ufw
        
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
        
        # Allow API port (if needed externally)
        ufw allow 8000/tcp
        
        # Enable firewall
        ufw --force enable
        
        # Show status
        ufw status verbose
EOF
    
    print_success "Firewall configured successfully"
}

# Function to setup monitoring
setup_monitoring() {
    local host="$1"
    local user="$2"
    local key="$3"
    
    print_status "Setting up monitoring..."
    
    ssh -i "$key" "$user@$host" << 'EOF'
        cd /opt/ai-core-system
        
        # Create monitoring directories
        mkdir -p monitoring/grafana/dashboards monitoring/grafana/datasources
        
        # Start monitoring services
        docker-compose --profile monitoring up -d
        
        # Wait for services to be ready
        sleep 30
        
        # Show monitoring status
        docker-compose --profile monitoring ps
EOF
    
    print_success "Monitoring setup completed"
}

# Function to show deployment status
show_status() {
    local host="$1"
    local user="$2"
    local key="$3"
    
    print_status "Checking deployment status..."
    
    ssh -i "$key" "$user@$host" << 'EOF'
        echo "=== Docker Services Status ==="
        cd /opt/ai-core-system && docker-compose ps
        
        echo -e "\n=== System Resources ==="
        df -h
        free -h
        
        echo -e "\n=== Application Health ==="
        curl -s http://localhost/health | jq . || echo "Health check failed"
        
        echo -e "\n=== SSL Certificate Status ==="
        openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout | grep -E "(Subject:|Not After)"
        
        echo -e "\n=== Firewall Status ==="
        ufw status
EOF
}

# Main deployment function
main() {
    echo "=========================================="
    echo "AI Core System - Infomaniak Deployment"
    echo "=========================================="
    echo
    
    # Get deployment information
    VPS_IP=$(get_input "Enter VPS IP address" "$VPS_IP")
    VPS_USER=$(get_input "Enter SSH user" "$VPS_USER")
    SSH_KEY=$(get_input "Enter SSH key path" "$SSH_KEY")
    DOMAIN=$(get_input "Enter domain name" "$DOMAIN")
    EMAIL=$(get_input "Enter admin email" "$EMAIL")
    
    # Validate inputs
    if ! validate_ip "$VPS_IP"; then
        print_error "Invalid IP address: $VPS_IP"
        exit 1
    fi
    
    if [ ! -f "$SSH_KEY" ]; then
        print_error "SSH key not found: $SSH_KEY"
        exit 1
    fi
    
    # Test SSH connection
    if ! test_ssh "$VPS_IP" "$VPS_USER" "$SSH_KEY"; then
        print_error "Cannot establish SSH connection. Please check your credentials."
        exit 1
    fi
    
    # Confirm deployment
    echo
    print_warning "Deployment Configuration:"
    echo "  VPS IP: $VPS_IP"
    echo "  SSH User: $VPS_USER"
    echo "  Domain: $DOMAIN"
    echo "  Email: $EMAIL"
    echo
    
    read -p "Proceed with deployment? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled"
        exit 0
    fi
    
    # Start deployment
    print_status "Starting deployment process..."
    
    # Install Docker
    install_docker "$VPS_IP" "$VPS_USER" "$SSH_KEY"
    
    # Setup SSL
    setup_ssl "$VPS_IP" "$VPS_USER" "$SSH_KEY" "$DOMAIN" "$EMAIL"
    
    # Setup firewall
    setup_firewall "$VPS_IP" "$VPS_USER" "$SSH_KEY"
    
    # Deploy application
    deploy_app "$VPS_IP" "$VPS_USER" "$SSH_KEY"
    
    # Setup monitoring (optional)
    read -p "Setup monitoring (Prometheus/Grafana)? (y/N): " setup_mon
    if [[ $setup_mon =~ ^[Yy]$ ]]; then
        setup_monitoring "$VPS_IP" "$VPS_USER" "$SSH_KEY"
    fi
    
    # Show final status
    show_status "$VPS_IP" "$VPS_USER" "$SSH_KEY"
    
    # Deployment summary
    echo
    print_success "Deployment completed successfully!"
    echo
    echo "Access URLs:"
    echo "  API: https://$DOMAIN"
    echo "  Documentation: https://$DOMAIN/docs"
    echo "  Health Check: https://$DOMAIN/health"
    if [[ $setup_mon =~ ^[Yy]$ ]]; then
        echo "  Grafana: https://$DOMAIN:3000"
        echo "  Prometheus: https://$DOMAIN:9090"
    fi
    echo
    echo "Next steps:"
    echo "1. Update DNS records to point $DOMAIN to $VPS_IP"
    echo "2. Obtain proper SSL certificates using Let's Encrypt"
    echo "3. Update API keys in the .env file"
    echo "4. Configure monitoring dashboards"
    echo
}

# Run main function
main "$@" 