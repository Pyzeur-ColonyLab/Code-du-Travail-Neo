#!/bin/bash

# Simple Fix for AI Core System
# This script rebuilds and restarts services without git operations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
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

# Function to check current directory
check_current_directory() {
    print_header "Checking Current Directory"
    
    if [[ ! -f "docker-compose-ssl.yml" ]]; then
        print_error "docker-compose-ssl.yml not found in current directory"
        print_error "Please run this script from /opt/ai-core-system"
        exit 1
    fi
    
    print_status "Current directory: $(pwd)"
    print_status "Found docker-compose-ssl.yml"
}

# Function to stop all services
stop_services() {
    print_header "Stopping All Services"
    
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    
    print_status "Stopping services..."
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml down
    
    print_status "All services stopped"
}

# Function to rebuild and restart services
rebuild_and_restart() {
    print_header "Rebuilding and Restarting Services"
    
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    
    print_status "Rebuilding AI API container..."
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml build ai-api
    
    print_status "Starting services with SSL configuration..."
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml up -d
    
    print_status "Waiting for services to start..."
    sleep 20
    
    print_status "Checking service status..."
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml ps
}

# Function to test the API
test_api() {
    print_header "Testing API"
    
    print_status "Testing local health endpoint..."
    if curl -s -f http://localhost:8000/health >/dev/null 2>&1; then
        print_status "✅ Local API is working"
    else
        print_warning "⚠️  Local API is not responding yet (may need more time)"
        return 1
    fi
    
    print_status "Testing nginx proxy..."
    if curl -s -f http://localhost/health >/dev/null 2>&1; then
        print_status "✅ Nginx proxy is working"
    else
        print_warning "⚠️  Nginx proxy is not responding yet"
    fi
    
    print_status "Testing HTTPS endpoint..."
    if curl -s -f -k https://localhost/health >/dev/null 2>&1; then
        print_status "✅ HTTPS endpoint is working"
    else
        print_warning "⚠️  HTTPS endpoint is not responding yet"
    fi
}

# Function to show logs
show_logs() {
    print_header "Recent Logs"
    
    DOCKER_COMPOSE_CMD=$(get_docker_compose_cmd)
    
    print_status "AI API logs (last 15 lines):"
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml logs --tail=15 ai-api
    
    echo ""
    print_status "Nginx logs (last 10 lines):"
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml logs --tail=10 nginx
    
    echo ""
    print_status "Redis logs (last 5 lines):"
    $DOCKER_COMPOSE_CMD -f docker-compose-ssl.yml logs --tail=5 redis
}

# Function to check ports
check_ports() {
    print_header "Checking Ports"
    
    if netstat -tuln | grep -q ":80 "; then
        print_status "Port 80 is listening"
    else
        print_warning "Port 80 is not listening"
    fi
    
    if netstat -tuln | grep -q ":443 "; then
        print_status "Port 443 is listening"
    else
        print_warning "Port 443 is not listening"
    fi
    
    if netstat -tuln | grep -q ":8000 "; then
        print_status "Port 8000 is listening"
    else
        print_warning "Port 8000 is not listening (may be internal only)"
    fi
}

# Function to provide final information
provide_final_info() {
    print_header "Fix Complete"
    
    echo ""
    echo "Services have been rebuilt and restarted!"
    echo ""
    echo "Service Information:"
    echo "  - Local API: http://localhost:8000"
    echo "  - Local Health: http://localhost:8000/health"
    echo "  - Nginx Proxy: http://localhost"
    echo "  - HTTPS: https://localhost"
    echo ""
    echo "External Access:"
    echo "  - Domain: https://ai.cryptomaltese.com"
    echo "  - Health Check: https://ai.cryptomaltese.com/health"
    echo ""
    echo "If services are still not working:"
    echo "  1. Check logs: sudo docker compose -f docker-compose-ssl.yml logs"
    echo "  2. Test connectivity: curl -I https://ai.cryptomaltese.com/health"
    echo "  3. Check ports: sudo netstat -tuln | grep -E ':80|:443|:8000'"
    echo ""
}

# Main function
main() {
    check_root
    
    print_header "Simple Fix for AI Core System"
    echo ""
    
    # Check current directory
    check_current_directory
    echo ""
    
    # Stop services
    stop_services
    echo ""
    
    # Rebuild and restart services
    rebuild_and_restart
    echo ""
    
    # Check ports
    check_ports
    echo ""
    
    # Test the API
    if test_api; then
        print_status "✅ All tests passed!"
    else
        print_warning "⚠️  Some tests failed, checking logs..."
        echo ""
        show_logs
    fi
    
    echo ""
    provide_final_info
}

# Run main function
main "$@" 