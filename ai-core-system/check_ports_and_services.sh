#!/bin/bash

# Check Ports and Services for AI Core System
# This script checks if ports are open and services are running

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

# Function to check if ports are listening
check_ports_listening() {
    print_header "Checking if ports are listening"
    
    # Check port 80
    if netstat -tuln | grep -q ":80 "; then
        print_status "Port 80 is listening"
    else
        print_error "Port 80 is NOT listening"
    fi
    
    # Check port 443
    if netstat -tuln | grep -q ":443 "; then
        print_status "Port 443 is listening"
    else
        print_error "Port 443 is NOT listening"
    fi
    
    # Check port 8000
    if netstat -tuln | grep -q ":8000 "; then
        print_status "Port 8000 is listening"
    else
        print_warning "Port 8000 is NOT listening (expected if only internal)"
    fi
}

# Function to check Docker containers
check_docker_containers() {
    print_header "Checking Docker containers"
    
    cd "$APP_DIR"
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    
    print_status "Container status:"
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml ps
    
    echo ""
    print_status "Checking if containers are running..."
    
    # Check each container
    if $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml ps | grep -q "ai-core-nginx.*Up"; then
        print_status "Nginx container is running"
    else
        print_error "Nginx container is NOT running"
    fi
    
    if $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml ps | grep -q "ai-core-api.*Up"; then
        print_status "AI API container is running"
    else
        print_error "AI API container is NOT running"
    fi
    
    if $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml ps | grep -q "ai-core-redis.*Up"; then
        print_status "Redis container is running"
    else
        print_error "Redis container is NOT running"
    fi
}

# Function to check firewall status
check_firewall() {
    print_header "Checking Firewall Status"
    
    # Check UFW status
    if command_exists ufw; then
        UFW_STATUS=$(ufw status | head -1)
        print_status "UFW Status: $UFW_STATUS"
        
        if echo "$UFW_STATUS" | grep -q "inactive"; then
            print_warning "UFW is inactive - no firewall rules applied"
        else
            print_status "UFW is active - checking rules..."
            ufw status numbered | grep -E "(80|443)"
        fi
    else
        print_warning "UFW not installed"
    fi
    
    # Check iptables
    print_status "Checking iptables rules for ports 80 and 443:"
    iptables -L -n | grep -E "(80|443)" || print_warning "No iptables rules found for ports 80/443"
}

# Function to check if services are accessible locally
check_local_access() {
    print_header "Testing Local Access"
    
    # Test localhost:80
    print_status "Testing localhost:80..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost/health 2>/dev/null | grep -q "200\|301\|302"; then
        print_status "localhost:80 is accessible"
    else
        print_error "localhost:80 is NOT accessible"
    fi
    
    # Test localhost:443
    print_status "Testing localhost:443..."
    if curl -s -o /dev/null -w "%{http_code}" https://localhost/health 2>/dev/null | grep -q "200\|301\|302"; then
        print_status "localhost:443 is accessible"
    else
        print_error "localhost:443 is NOT accessible"
    fi
    
    # Test localhost:8000
    print_status "Testing localhost:8000..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null | grep -q "200"; then
        print_status "localhost:8000 is accessible"
    else
        print_warning "localhost:8000 is NOT accessible (may be internal only)"
    fi
}

# Function to check external connectivity
check_external_connectivity() {
    print_header "Testing External Connectivity"
    
    # Get server's public IP
    SERVER_IP=$(curl -s ifconfig.me)
    print_status "Server public IP: $SERVER_IP"
    
    # Test external access to port 80
    print_status "Testing external access to port 80..."
    if curl -s -o /dev/null -w "%{http_code}" "http://$SERVER_IP/health" 2>/dev/null | grep -q "200\|301\|302"; then
        print_status "External port 80 is accessible"
    else
        print_error "External port 80 is NOT accessible"
    fi
    
    # Test external access to port 443
    print_status "Testing external access to port 443..."
    if curl -s -o /dev/null -w "%{http_code}" "https://$SERVER_IP/health" 2>/dev/null | grep -q "200\|301\|302"; then
        print_status "External port 443 is accessible"
    else
        print_error "External port 443 is NOT accessible"
    fi
    
    # Test domain resolution
    print_status "Testing domain resolution..."
    RESOLVED_IP=$(dig +short "$DOMAIN" | head -1)
    if [[ -n "$RESOLVED_IP" ]]; then
        print_status "Domain $DOMAIN resolves to: $RESOLVED_IP"
        if [[ "$RESOLVED_IP" == "$SERVER_IP" ]]; then
            print_status "DNS resolution matches server IP"
        else
            print_warning "DNS resolution does NOT match server IP"
        fi
    else
        print_error "Domain $DOMAIN does not resolve"
    fi
}

# Function to start services if needed
start_services() {
    print_header "Starting Services"
    
    cd "$APP_DIR"
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    
    print_status "Starting services with SSL configuration..."
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml up -d
    
    print_status "Waiting for services to start..."
    sleep 10
    
    print_status "Checking service status after start..."
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml ps
}

# Function to provide recommendations
provide_recommendations() {
    print_header "Recommendations"
    
    echo ""
    echo "If services are not running or ports are not open:"
    echo ""
    echo "1. Start the services:"
    echo "   cd $APP_DIR && sudo $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml up -d"
    echo ""
    echo "2. Check if Docker service is running:"
    echo "   sudo systemctl status docker"
    echo ""
    echo "3. If Docker is not running:"
    echo "   sudo systemctl start docker"
    echo "   sudo systemctl enable docker"
    echo ""
    echo "4. Check firewall settings:"
    echo "   sudo ufw status"
    echo "   sudo ufw allow 80"
    echo "   sudo ufw allow 443"
    echo ""
    echo "5. Check if ports are being used by other services:"
    echo "   sudo netstat -tulpn | grep -E ':80|:443'"
    echo ""
    echo "6. Check container logs:"
    echo "   cd $APP_DIR && sudo $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml logs"
    echo ""
}

# Main function
main() {
    check_root
    
    print_header "Port and Service Check for AI Core System"
    echo ""
    
    # Run all checks
    check_ports_listening
    echo ""
    
    check_docker_containers
    echo ""
    
    check_firewall
    echo ""
    
    check_local_access
    echo ""
    
    check_external_connectivity
    echo ""
    
    # Ask if user wants to start services
    echo ""
    read -p "Do you want to start the services? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_services
        echo ""
        check_ports_listening
        echo ""
        check_local_access
    fi
    
    echo ""
    provide_recommendations
}

# Run main function
main "$@" 