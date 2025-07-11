#!/bin/bash

# Fixed SSL Certificate Script for Docker - AI Core System
# This script properly handles Docker services during SSL certificate renewal

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="ai.cryptomaltese.com"
EMAIL="admin@cryptomaltese.com"
APP_DIR="/opt/ai-core-system"

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

print_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get docker compose command
get_docker_compose_cmd() {
    if command_exists docker; then
        # Try docker compose (newer version)
        if docker compose version >/dev/null 2>&1; then
            echo "docker compose"
        # Try docker-compose (older version)
        elif command_exists docker-compose; then
            echo "docker-compose"
        else
            print_error "Neither 'docker compose' nor 'docker-compose' is available"
            exit 1
        fi
    else
        print_error "Docker is not installed"
        exit 1
    fi
}

# Function to check DNS resolution
check_dns_resolution() {
    print_status "Checking DNS resolution for $DOMAIN..."
    
    # Try different DNS lookup commands
    RESOLVED_IP=""
    
    # Try dig first (most reliable)
    if command_exists dig; then
        RESOLVED_IP=$(dig +short "$DOMAIN" | head -1)
    # Try host command as fallback
    elif command_exists host; then
        RESOLVED_IP=$(host "$DOMAIN" | grep "has address" | awk '{print $NF}' | head -1)
    # Try nslookup as last resort
    elif command_exists nslookup; then
        RESOLVED_IP=$(nslookup "$DOMAIN" | grep -A1 "Name:" | tail -1 | awk '{print $2}')
    else
        print_error "No DNS lookup tools available"
        exit 1
    fi
    
    # Check if we got a valid IP
    if [[ -n "$RESOLVED_IP" ]] && [[ "$RESOLVED_IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        # Get server's public IP
        SERVER_IP=$(curl -s ifconfig.me)
        
        if [[ "$RESOLVED_IP" == "$SERVER_IP" ]]; then
            print_status "DNS resolution successful: $DOMAIN -> $RESOLVED_IP"
            return 0
        else
            print_warning "DNS resolution mismatch:"
            print_warning "  Domain $DOMAIN resolves to: $RESOLVED_IP"
            print_warning "  Server IP is: $SERVER_IP"
            print_warning "  DNS may not be properly configured or propagated"
            return 1
        fi
    else
        print_error "DNS resolution failed for $DOMAIN"
        print_error "Please configure DNS records before proceeding"
        return 1
    fi
}

# Function to backup current certificates
backup_current_certificates() {
    print_status "Backing up current certificates..."
    
    if [[ -f "$APP_DIR/ssl/cert.pem" ]] || [[ -f "$APP_DIR/ssl/key.pem" ]]; then
        BACKUP_DIR="$APP_DIR/ssl/backup-$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        if [[ -f "$APP_DIR/ssl/cert.pem" ]]; then
            cp "$APP_DIR/ssl/cert.pem" "$BACKUP_DIR/"
        fi
        
        if [[ -f "$APP_DIR/ssl/key.pem" ]]; then
            cp "$APP_DIR/ssl/key.pem" "$BACKUP_DIR/"
        fi
        
        print_status "Certificates backed up to: $BACKUP_DIR"
    fi
}

# Function to check current service status
check_service_status() {
    print_status "Checking current service status..."
    
    cd "$APP_DIR"
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    
    # Check if services are running
    if $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
        print_status "Services are currently running"
        return 0
    else
        print_warning "Services are not running"
        return 1
    fi
}

# Function to stop only nginx (keep other services running)
stop_nginx_only() {
    print_status "Stopping only Nginx container for certificate renewal..."
    
    cd "$APP_DIR"
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    
    # Stop only nginx container
    $DOCKER_COMPOSE_CMD stop nginx
    
    # Wait a moment for nginx to fully stop
    sleep 3
    
    print_status "Nginx stopped, other services remain running"
}

# Function to obtain new SSL certificate
obtain_ssl_certificate() {
    print_status "Obtaining SSL certificate for $DOMAIN..."
    
    # Get certificate using standalone mode
    certbot certonly --standalone \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN"
    
    # Check if certificate was obtained successfully
    if [[ $? -eq 0 ]]; then
        print_status "SSL certificate obtained successfully"
        return 0
    else
        print_error "Failed to obtain SSL certificate"
        return 1
    fi
}

# Function to install new certificates
install_new_certificates() {
    print_status "Installing new SSL certificates..."
    
    # Create ssl directory if it doesn't exist
    mkdir -p "$APP_DIR/ssl"
    
    # Copy certificates
    cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem "$APP_DIR/ssl/cert.pem"
    cp /etc/letsencrypt/live/$DOMAIN/privkey.pem "$APP_DIR/ssl/key.pem"
    
    # Set permissions
    chmod 644 "$APP_DIR/ssl/cert.pem"
    chmod 600 "$APP_DIR/ssl/key.pem"
    
    print_status "SSL certificates installed successfully"
}

# Function to restart nginx with new certificates
restart_nginx() {
    print_status "Restarting Nginx with new certificates..."
    
    cd "$APP_DIR"
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    
    # Start nginx with SSL configuration
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml up -d nginx
    
    # Wait for nginx to be ready
    print_status "Waiting for Nginx to start..."
    sleep 5
    
    # Check nginx status
    if $DOCKER_COMPOSE_CMD ps nginx | grep -q "Up"; then
        print_status "Nginx restarted successfully with SSL"
    else
        print_error "Nginx restart failed"
        $DOCKER_COMPOSE_CMD logs nginx
        exit 1
    fi
}

# Function to verify all services are running
verify_services() {
    print_status "Verifying all services are running..."
    
    cd "$APP_DIR"
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    
    # Check all services
    if $DOCKER_COMPOSE_CMD ps | grep -q "Up"; then
        print_status "All services are running"
        $DOCKER_COMPOSE_CMD ps
    else
        print_error "Some services failed to start"
        $DOCKER_COMPOSE_CMD ps
        exit 1
    fi
}

# Function to setup auto-renewal
setup_auto_renewal() {
    print_status "Setting up SSL certificate auto-renewal..."
    
    if command_exists crontab; then
        # Check if SSL renewal job already exists
        if ! crontab -l 2>/dev/null | grep -q "fix_ssl_certificate_docker.sh"; then
            (crontab -l 2>/dev/null; echo "0 12 * * * $APP_DIR/fix_ssl_certificate_docker.sh") | crontab -
            print_status "SSL certificate auto-renewal scheduled"
        else
            print_warning "SSL renewal cron job already exists"
        fi
    else
        print_warning "crontab not available, SSL renewal not scheduled"
        print_warning "You can manually renew certificates with: $APP_DIR/fix_ssl_certificate_docker.sh"
    fi
}

# Function to test SSL certificate
test_ssl_certificate() {
    print_status "Testing SSL certificate..."
    
    # Wait a bit for nginx to fully initialize
    sleep 3
    
    # Test SSL connection
    if command_exists openssl; then
        print_status "Certificate details:"
        echo | openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" 2>/dev/null | openssl x509 -noout -subject -dates
    fi
    
    # Test HTTP response
    print_status "Testing HTTPS health check..."
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/health" 2>/dev/null || echo "000")
    
    if [[ "$HTTP_STATUS" == "200" ]]; then
        print_status "SSL certificate test successful"
        print_status "Health check returned: $HTTP_STATUS"
    else
        print_warning "SSL certificate test returned status: $HTTP_STATUS"
        print_warning "This might be normal if the service is still starting up"
    fi
}

# Function to display final information
display_final_info() {
    echo ""
    echo -e "${GREEN}=== SSL Certificate Fix Complete ===${NC}"
    echo ""
    echo "SSL certificate has been updated for $DOMAIN"
    echo ""
    echo "Service Information:"
    echo "  - API URL: https://$DOMAIN"
    echo "  - Health Check: https://$DOMAIN/health"
    echo "  - API Documentation: https://$DOMAIN/docs"
    echo ""
    echo "Certificate Information:"
    echo "  - Certificate: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    echo "  - Private Key: /etc/letsencrypt/live/$DOMAIN/privkey.pem"
    echo "  - Auto-renewal: Configured"
    echo ""
    echo "Test the certificate:"
    echo "  curl -I https://$DOMAIN/health"
    echo ""
    echo "All services should now be running with SSL enabled!"
    echo ""
}

# Main function
main() {
    check_root
    
    print_header "Fixed SSL Certificate Script for Docker"
    echo ""
    
    # Check DNS resolution
    if ! check_dns_resolution; then
        print_error "DNS resolution failed. Cannot proceed."
        exit 1
    fi
    
    # Check current service status
    check_service_status
    
    # Backup current certificates
    backup_current_certificates
    
    # Stop only nginx (keep other services running)
    stop_nginx_only
    
    # Obtain new SSL certificate
    if obtain_ssl_certificate; then
        # Install new certificates
        install_new_certificates
        
        # Restart nginx with new certificates
        restart_nginx
        
        # Verify all services are running
        verify_services
        
        # Setup auto-renewal
        setup_auto_renewal
        
        # Test SSL certificate
        test_ssl_certificate
        
        # Display final information
        display_final_info
    else
        print_error "SSL certificate fix failed"
        
        # Try to restart nginx anyway
        print_status "Attempting to restart nginx..."
        cd "$APP_DIR"
        DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
        $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml up -d nginx
        
        exit 1
    fi
}

# Run main function
main "$@" 