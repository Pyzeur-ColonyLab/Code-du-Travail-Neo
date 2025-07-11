#!/bin/bash

# Comprehensive AI Core System Management Script
# This script handles models.json configuration, SSL certificates, and service management

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/ai-core-system"
CONFIG_FILE="$APP_DIR/config/models.json"
BACKUP_DIR="$APP_DIR/config/backups"
DOMAIN="ai.cryptomaltese.com"
EMAIL="admin@cryptomaltese.com"

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

# Function to backup current configuration
backup_current_config() {
    print_status "Backing up current models.json configuration..."
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    if [[ -f "$CONFIG_FILE" ]]; then
        BACKUP_FILE="$BACKUP_DIR/models.json.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CONFIG_FILE" "$BACKUP_FILE"
        print_status "Configuration backed up to: $BACKUP_FILE"
    else
        print_warning "No existing models.json found to backup"
    fi
}

# Function to create latest models configuration
create_latest_config() {
    print_status "Creating latest models.json configuration..."
    
    # Create config directory if it doesn't exist
    mkdir -p "$(dirname "$CONFIG_FILE")"
    
    cat > "$CONFIG_FILE" << EOF
{
  "models": {
    "tiny-llama": {
      "type": "transformers",
      "path": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
      "format": "safetensor",
      "device": "cpu",
      "quantization": "none",
      "max_memory": "2GB",
      "context_length": 2048,
      "temperature": 0.7,
      "top_p": 0.9,
      "max_tokens": 512
    },
    "phi-2": {
      "type": "transformers",
      "path": "microsoft/phi-2",
      "format": "safetensor",
      "device": "cpu",
      "quantization": "none",
      "max_memory": "4GB",
      "context_length": 2048,
      "temperature": 0.7,
      "top_p": 0.9,
      "max_tokens": 512
    },
    "mistral-7b-instruct": {
      "type": "transformers",
      "path": "mistralai/Mistral-7B-Instruct-v0.2",
      "format": "safetensor",
      "device": "cpu",
      "quantization": "none",
      "max_memory": "8GB",
      "context_length": 4096,
      "temperature": 0.7,
      "top_p": 0.9,
      "max_tokens": 512
    },
    "code-du-travail-mistral": {
      "type": "transformers",
      "path": "mistralai/Mistral-7B-Instruct-v0.2",
      "adapter": "Pyzeur/Code-du-Travail-mistral-finetune",
      "format": "safetensor",
      "device": "cpu",
      "quantization": "none",
      "max_memory": "8GB",
      "context_length": 4096,
      "temperature": 0.7,
      "top_p": 0.9,
      "max_tokens": 512,
      "requires_token": true,
      "trust_remote_code": true,
      "use_fast_tokenizer": false
    }
  },
  "default_model": "tiny-llama",
  "model_cache_dir": "/app/cache",
  "model_load_timeout": 300,
  "model_unload_timeout": 60
}
EOF
    
    print_status "Latest models.json configuration created"
}

# Function to validate JSON configuration
validate_config() {
    print_status "Validating models.json configuration..."
    
    if command_exists python3; then
        if python3 -m json.tool "$CONFIG_FILE" > /dev/null 2>&1; then
            print_status "JSON configuration is valid"
            return 0
        else
            print_error "JSON configuration is invalid"
            return 1
        fi
    elif command_exists jq; then
        if jq empty "$CONFIG_FILE" > /dev/null 2>&1; then
            print_status "JSON configuration is valid"
            return 0
        else
            print_error "JSON configuration is invalid"
            return 1
        fi
    else
        print_warning "No JSON validator available, skipping validation"
        return 0
    fi
}

# Function to check DNS resolution
check_dns() {
    print_status "Checking DNS resolution for $DOMAIN..."
    
    if nslookup "$DOMAIN" > /dev/null 2>&1; then
        print_status "DNS resolution successful for $DOMAIN"
        return 0
    else
        print_error "DNS resolution failed for $DOMAIN"
        print_warning "Please ensure DNS is properly configured before proceeding"
        return 1
    fi
}

# Function to backup SSL certificates
backup_ssl_certificates() {
    print_status "Backing up existing SSL certificates..."
    
    SSL_DIR="$APP_DIR/ssl"
    BACKUP_SSL_DIR="$APP_DIR/ssl/backups"
    
    if [[ -d "$SSL_DIR" ]]; then
        mkdir -p "$BACKUP_SSL_DIR"
        
        if [[ -f "$SSL_DIR/cert.pem" ]] || [[ -f "$SSL_DIR/key.pem" ]]; then
            BACKUP_NAME="ssl_backup_$(date +%Y%m%d_%H%M%S)"
            BACKUP_PATH="$BACKUP_SSL_DIR/$BACKUP_NAME"
            
            mkdir -p "$BACKUP_PATH"
            
            if [[ -f "$SSL_DIR/cert.pem" ]]; then
                cp "$SSL_DIR/cert.pem" "$BACKUP_PATH/"
                print_status "SSL certificate backed up"
            fi
            
            if [[ -f "$SSL_DIR/key.pem" ]]; then
                cp "$SSL_DIR/key.pem" "$BACKUP_PATH/"
                print_status "SSL private key backed up"
            fi
            
            print_status "SSL certificates backed up to: $BACKUP_PATH"
        else
            print_warning "No existing SSL certificates found to backup"
        fi
    else
        print_warning "SSL directory does not exist, creating it"
        mkdir -p "$SSL_DIR"
    fi
}

# Function to obtain SSL certificate
obtain_ssl_certificate() {
    print_status "Obtaining SSL certificate for $DOMAIN..."
    
    SSL_DIR="$APP_DIR/ssl"
    
    # Check if certbot is available
    if ! command_exists certbot; then
        print_status "Installing certbot..."
        apt-get update
        apt-get install -y certbot python3-certbot-nginx
    fi
    
    # Stop nginx temporarily to free port 80
    print_status "Stopping nginx temporarily for certificate verification..."
    cd "$APP_DIR"
    docker compose -f docker-compose-ssl.yml stop nginx || true
    
    # Wait a moment for port to be freed
    sleep 5
    
    # Obtain certificate
    if certbot certonly --standalone \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --domains "$DOMAIN" \
        --cert-path "$SSL_DIR/cert.pem" \
        --key-path "$SSL_DIR/key.pem"; then
        
        print_status "SSL certificate obtained successfully"
        
        # Set proper permissions
        chmod 644 "$SSL_DIR/cert.pem"
        chmod 600 "$SSL_DIR/key.pem"
        
        return 0
    else
        print_error "Failed to obtain SSL certificate"
        return 1
    fi
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images..."
    
    cd "$APP_DIR"
    
    # Check if SSL certificates exist to determine which compose file to use
    if [[ -f "ssl/cert.pem" ]] && [[ -f "ssl/key.pem" ]]; then
        print_status "SSL certificates found, building with SSL configuration..."
        docker compose -f docker-compose-ssl.yml build --no-cache
    else
        print_status "No SSL certificates found, building with HTTP configuration..."
        docker compose build --no-cache
    fi
    
    if [[ $? -eq 0 ]]; then
        print_status "Docker images built successfully"
        return 0
    else
        print_error "Docker build failed"
        return 1
    fi
}

# Function to check if rebuild is needed
check_rebuild_needed() {
    if [[ -f "requirements.txt" ]] && [[ -f ".last_build" ]]; then
        if [[ "requirements.txt" -nt ".last_build" ]]; then
            return 0  # Rebuild needed
        fi
    fi
    return 1  # No rebuild needed
}

# Function to rebuild and restart services
rebuild_and_restart() {
    print_header "Rebuilding and Restarting Services"
    echo ""
    
    check_root
    
    # Backup current configuration
    backup_current_config
    
    # Check if rebuild is actually needed
    if check_rebuild_needed; then
        print_status "Dependencies have changed, rebuilding images..."
    else
        print_warning "No dependency changes detected, but rebuilding anyway..."
    fi
    
    # Build images
    if build_images; then
        # Update last build timestamp
        touch .last_build
        
        # Restart services
        restart_services
        
        # Test configuration
        test_configuration
        
        print_status "Rebuild and restart completed successfully"
    else
        print_error "Rebuild failed"
        exit 1
    fi
}

# Function to restart services
restart_services() {
    print_status "Restarting services..."
    
    cd "$APP_DIR"
    
    # Check if SSL certificates exist
    if [[ -f "ssl/cert.pem" ]] && [[ -f "ssl/key.pem" ]]; then
        print_status "SSL certificates found, using SSL configuration..."
        docker compose -f docker-compose-ssl.yml down
        docker compose -f docker-compose-ssl.yml up -d
    else
        print_status "No SSL certificates found, using HTTP configuration..."
        docker compose down
        docker compose up -d
    fi
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    sleep 15
    
    print_status "Services restarted successfully"
}

# Function to test configuration
test_configuration() {
    print_status "Testing configuration..."
    
    # Wait a bit for services to be ready
    sleep 10
    
    # Test API health
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_status "API health check passed"
    else
        print_warning "API health check failed"
    fi
    
    # Test models endpoint
    if curl -s http://localhost:8000/api/v1/models > /dev/null 2>&1; then
        print_status "Models endpoint is accessible"
        
        # Check if custom model is present
        if curl -s http://localhost:8000/api/v1/models | grep -q "code-du-travail-mistral"; then
            print_status "Custom model 'code-du-travail-mistral' is configured"
        else
            print_warning "Custom model 'code-du-travail-mistral' not found in API response"
        fi
    else
        print_warning "Models endpoint is not accessible"
    fi
    
    # Test HTTPS if SSL is configured
    if [[ -f "$APP_DIR/ssl/cert.pem" ]] && [[ -f "$APP_DIR/ssl/key.pem" ]]; then
        print_status "Testing HTTPS access..."
        if curl -s -k https://localhost/health > /dev/null 2>&1; then
            print_status "HTTPS access working locally"
        else
            print_warning "HTTPS access not working locally"
        fi
    fi
}

# Function to show current configuration
show_current_config() {
    print_status "Current models.json configuration:"
    echo ""
    if [[ -f "$CONFIG_FILE" ]]; then
        cat "$CONFIG_FILE"
    else
        print_error "models.json file not found"
    fi
    echo ""
}

# Function to list available backups
list_backups() {
    print_status "Available configuration backups:"
    echo ""
    if [[ -d "$BACKUP_DIR" ]] && [[ -n "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]]; then
        ls -la "$BACKUP_DIR"/models.json.backup.* 2>/dev/null || print_warning "No backups found"
    else
        print_warning "No backups found"
    fi
    echo ""
}

# Function to restore from backup
restore_from_backup() {
    local backup_file="$1"
    
    if [[ -z "$backup_file" ]]; then
        print_error "Please specify a backup file to restore from"
        list_backups
        exit 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_status "Restoring configuration from backup: $backup_file"
    
    # Backup current config before restoring
    backup_current_config
    
    # Restore from backup
    cp "$backup_file" "$CONFIG_FILE"
    
    print_status "Configuration restored from backup"
    
    # Restart services
    restart_services
}

# Function to setup SSL certificates
setup_ssl() {
    print_header "Setting up SSL Certificates"
    echo ""
    
    check_root
    
    # Check DNS resolution
    if ! check_dns; then
        print_error "DNS resolution failed. Please fix DNS configuration first."
        exit 1
    fi
    
    # Backup existing certificates
    backup_ssl_certificates
    
    # Obtain new certificate
    if obtain_ssl_certificate; then
        # Restart services with SSL
        restart_services
        
        # Test configuration
        test_configuration
        
        print_status "SSL setup completed successfully"
        print_status "Your site should now be accessible at: https://$DOMAIN"
    else
        print_error "SSL setup failed"
        exit 1
    fi
}

# Function to renew SSL certificates
renew_ssl() {
    print_header "Renewing SSL Certificates"
    echo ""
    
    check_root
    
    SSL_DIR="$APP_DIR/ssl"
    
    if [[ ! -f "$SSL_DIR/cert.pem" ]] || [[ ! -f "$SSL_DIR/key.pem" ]]; then
        print_error "No SSL certificates found. Run 'ssl' command first."
        exit 1
    fi
    
    # Stop nginx temporarily
    print_status "Stopping nginx temporarily for certificate renewal..."
    cd "$APP_DIR"
    docker compose -f docker-compose-ssl.yml stop nginx || true
    
    sleep 5
    
    # Renew certificate
    if certbot renew --cert-path "$SSL_DIR/cert.pem" --key-path "$SSL_DIR/key.pem"; then
        print_status "SSL certificate renewed successfully"
        
        # Set proper permissions
        chmod 644 "$SSL_DIR/cert.pem"
        chmod 600 "$SSL_DIR/key.pem"
        
        # Restart services
        restart_services
        
        print_status "SSL renewal completed successfully"
    else
        print_error "SSL certificate renewal failed"
        exit 1
    fi
}

# Function to display help
show_help() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  update     Update models.json to latest configuration and restart services (default)"
    echo "  build      Build Docker images with latest dependencies"
    echo "  rebuild    Rebuild Docker images and restart services"
    echo "  ssl        Setup SSL certificates for $DOMAIN"
    echo "  renew      Renew existing SSL certificates"
    echo "  backup     Create backup of current configuration"
    echo "  restore    Restore configuration from backup"
    echo "  list       List available backups"
    echo "  show       Show current configuration"
    echo "  test       Test current configuration"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Update configuration and restart services"
    echo "  $0 build              # Build Docker images"
    echo "  $0 rebuild            # Rebuild images and restart services"
    echo "  $0 ssl                # Setup SSL certificates"
    echo "  $0 renew              # Renew SSL certificates"
    echo "  $0 backup             # Create backup"
    echo "  $0 restore /path/to/backup  # Restore from backup"
    echo "  $0 list               # List available backups"
    echo "  $0 show               # Show current configuration"
    echo "  $0 test               # Test configuration"
    echo ""
    echo "This script handles:"
    echo "  - Models configuration management"
    echo "  - Docker image building and rebuilding"
    echo "  - SSL certificate setup and renewal"
    echo "  - Service restart and testing"
    echo "  - Backup and restore functionality"
}

# Main function
main() {
    local action="${1:-update}"
    
    case "$action" in
        "update")
            check_root
            print_header "Updating Models Configuration and Services"
            echo ""
            backup_current_config
            create_latest_config
            if validate_config; then
                # Check if rebuild is needed (when requirements.txt changed)
                if [[ -f "requirements.txt" ]] && [[ -f ".last_build" ]]; then
                    if [[ "requirements.txt" -nt ".last_build" ]]; then
                        print_warning "Requirements.txt has changed, rebuilding images..."
                        build_images
                        touch .last_build
                    fi
                fi
                restart_services
                test_configuration
                print_status "Configuration update completed successfully"
            else
                print_error "Configuration update failed - invalid JSON"
                exit 1
            fi
            ;;
        "build")
            check_root
            print_header "Building Docker Images"
            echo ""
            build_images
            ;;
        "rebuild")
            rebuild_and_restart
            ;;
        "ssl")
            setup_ssl
            ;;
        "renew")
            renew_ssl
            ;;
        "backup")
            check_root
            print_header "Creating Configuration Backup"
            echo ""
            backup_current_config
            print_status "Backup completed"
            ;;
        "restore")
            check_root
            print_header "Restoring Configuration from Backup"
            echo ""
            restore_from_backup "$2"
            ;;
        "list")
            print_header "Available Backups"
            echo ""
            list_backups
            ;;
        "show")
            print_header "Current Configuration"
            echo ""
            show_current_config
            ;;
        "test")
            check_root
            print_header "Testing Configuration"
            echo ""
            test_configuration
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $action"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 