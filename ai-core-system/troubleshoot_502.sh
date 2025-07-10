#!/bin/bash

# Troubleshoot 502 Error for AI Core System
# This script helps diagnose and fix 502 Bad Gateway errors

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="ai.cryptomaltese.com"
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

# Function to check Docker service status
check_docker_status() {
    print_header "Docker Service Status"
    
    if systemctl is-active --quiet docker; then
        print_status "Docker service is running"
    else
        print_error "Docker service is not running"
        print_status "Starting Docker service..."
        systemctl start docker
        systemctl enable docker
    fi
}

# Function to check container status
check_container_status() {
    print_header "Container Status"
    
    cd "$APP_DIR"
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    
    print_status "Checking container status..."
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml ps
    
    echo ""
    print_status "Container logs (last 20 lines each):"
    echo ""
    
    # Check AI API logs
    print_status "AI API logs:"
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml logs --tail=20 ai-api
    echo ""
    
    # Check Nginx logs
    print_status "Nginx logs:"
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml logs --tail=20 nginx
    echo ""
    
    # Check Redis logs
    print_status "Redis logs:"
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml logs --tail=20 redis
    echo ""
}

# Function to check network connectivity
check_network_connectivity() {
    print_header "Network Connectivity"
    
    cd "$APP_DIR"
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    
    # Check if containers can reach each other
    print_status "Testing internal network connectivity..."
    
    # Test AI API container connectivity
    if $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml exec -T ai-api ping -c 1 redis >/dev/null 2>&1; then
        print_status "AI API can reach Redis"
    else
        print_error "AI API cannot reach Redis"
    fi
    
    # Test Nginx container connectivity
    if $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml exec -T nginx ping -c 1 ai-api >/dev/null 2>&1; then
        print_status "Nginx can reach AI API"
    else
        print_error "Nginx cannot reach AI API"
    fi
    
    # Test AI API service directly
    print_status "Testing AI API service directly..."
    if $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml exec -T ai-api curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_status "AI API health endpoint is responding"
    else
        print_error "AI API health endpoint is not responding"
    fi
}

# Function to check SSL certificate
check_ssl_certificate() {
    print_header "SSL Certificate Status"
    
    # Check certificate files
    if [[ -f "$APP_DIR/ssl/cert.pem" ]] && [[ -f "$APP_DIR/ssl/key.pem" ]]; then
        print_status "SSL certificate files exist"
        
        # Check certificate validity
        if command_exists openssl; then
            print_status "Certificate details:"
            openssl x509 -in "$APP_DIR/ssl/cert.pem" -text -noout | grep -E "(Subject:|Not Before:|Not After:)"
        fi
    else
        print_error "SSL certificate files missing"
        print_status "Expected files:"
        print_status "  - $APP_DIR/ssl/cert.pem"
        print_status "  - $APP_DIR/ssl/key.pem"
    fi
}

# Function to check port availability
check_port_availability() {
    print_header "Port Availability"
    
    # Check if ports are in use
    if netstat -tuln | grep -q ":80 "; then
        print_status "Port 80 is in use"
    else
        print_warning "Port 80 is not in use"
    fi
    
    if netstat -tuln | grep -q ":443 "; then
        print_status "Port 443 is in use"
    else
        print_warning "Port 443 is not in use"
    fi
    
    if netstat -tuln | grep -q ":8000 "; then
        print_status "Port 8000 is in use"
    else
        print_warning "Port 8000 is not in use"
    fi
}

# Function to test external connectivity
test_external_connectivity() {
    print_header "External Connectivity Test"
    
    print_status "Testing HTTP connection..."
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$DOMAIN/health" 2>/dev/null || echo "000")
    print_status "HTTP status: $HTTP_STATUS"
    
    print_status "Testing HTTPS connection..."
    HTTPS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/health" 2>/dev/null || echo "000")
    print_status "HTTPS status: $HTTPS_STATUS"
    
    if [[ "$HTTPS_STATUS" == "200" ]]; then
        print_status "✅ HTTPS connection is working!"
    elif [[ "$HTTPS_STATUS" == "502" ]]; then
        print_error "❌ 502 Bad Gateway error detected"
        print_status "This usually means the backend service is not responding"
    else
        print_warning "⚠️  HTTPS returned status: $HTTPS_STATUS"
    fi
}

# Function to restart services
restart_services() {
    print_header "Restarting Services"
    
    cd "$APP_DIR"
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    
    print_status "Stopping all services..."
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml down
    
    print_status "Starting services with SSL configuration..."
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml up -d
    
    print_status "Waiting for services to start..."
    sleep 15
    
    print_status "Checking service status after restart..."
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml ps
}

# Function to provide recommendations
provide_recommendations() {
    print_header "Troubleshooting Recommendations"
    
    echo ""
    echo "If you're still getting 502 errors, try these steps:"
    echo ""
    echo "1. Check the AI API application logs:"
    echo "   cd $APP_DIR && $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml logs -f ai-api"
    echo ""
    echo "2. Check if the AI API is starting properly:"
    echo "   cd $APP_DIR && $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml exec ai-api ps aux"
    echo ""
    echo "3. Test the AI API directly:"
    echo "   cd $APP_DIR && $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml exec ai-api curl http://localhost:8000/health"
    echo ""
    echo "4. Check environment variables:"
    echo "   cd $APP_DIR && $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml exec ai-api env | grep -E '(REDIS|API|MODEL)'"
    echo ""
    echo "5. Rebuild the AI API container:"
    echo "   cd $APP_DIR && $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml build ai-api"
    echo "   cd $APP_DIR && $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml up -d"
    echo ""
}

# Main function
main() {
    check_root
    
    print_header "502 Error Troubleshooting for AI Core System"
    echo ""
    
    # Run all checks
    check_docker_status
    echo ""
    
    check_container_status
    echo ""
    
    check_network_connectivity
    echo ""
    
    check_ssl_certificate
    echo ""
    
    check_port_availability
    echo ""
    
    test_external_connectivity
    echo ""
    
    # Ask if user wants to restart services
    echo ""
    read -p "Do you want to restart the services? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        restart_services
        echo ""
        test_external_connectivity
    fi
    
    echo ""
    provide_recommendations
}

# Run main function
main "$@" 