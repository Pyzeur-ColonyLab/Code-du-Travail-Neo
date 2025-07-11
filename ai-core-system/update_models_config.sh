#!/bin/bash

# Update Models Configuration Script
# This script ensures the models.json file is always up to date with the latest configuration

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

# Function to restart services to pick up new configuration
restart_services() {
    print_status "Restarting services to pick up new configuration..."
    
    cd "$APP_DIR"
    
    # Check if SSL is enabled
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
    sleep 10
    
    print_status "Services restarted successfully"
}

# Function to test configuration
test_configuration() {
    print_status "Testing configuration..."
    
    # Wait a bit for services to be ready
    sleep 5
    
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

# Function to display help
show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  update     Update models.json to latest configuration (default)"
    echo "  backup     Create backup of current configuration"
    echo "  restore    Restore configuration from backup"
    echo "  list       List available backups"
    echo "  show       Show current configuration"
    echo "  test       Test current configuration"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Update to latest configuration"
    echo "  $0 backup             # Create backup"
    echo "  $0 restore /path/to/backup  # Restore from backup"
    echo "  $0 list               # List available backups"
    echo "  $0 show               # Show current configuration"
    echo "  $0 test               # Test configuration"
}

# Main function
main() {
    local action="${1:-update}"
    
    case "$action" in
        "update")
            check_root
            print_header "Updating Models Configuration"
            echo ""
            backup_current_config
            create_latest_config
            if validate_config; then
                restart_services
                test_configuration
                print_status "Configuration update completed successfully"
            else
                print_error "Configuration update failed - invalid JSON"
                exit 1
            fi
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
            print_error "Unknown action: $action"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 