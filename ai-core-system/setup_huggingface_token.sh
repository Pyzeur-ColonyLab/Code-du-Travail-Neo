#!/bin/bash

# Setup Hugging Face Token for AI Core System
# This script helps you configure the Hugging Face token for downloading custom models

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/ai-core-system"
ENV_FILE="$APP_DIR/.env"

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

# Function to check if .env file exists
check_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        print_error ".env file not found at $ENV_FILE"
        print_error "Please run the deployment script first"
        exit 1
    fi
    
    print_status "Found .env file at $ENV_FILE"
}

# Function to get Hugging Face token
get_hf_token() {
    print_header "Hugging Face Token Setup"
    
    echo ""
    echo "To download models from Hugging Face (like your custom model), you need a token."
    echo ""
    echo "To get your Hugging Face token:"
    echo "1. Go to https://huggingface.co/settings/tokens"
    echo "2. Click 'New token'"
    echo "3. Give it a name (e.g., 'ai-core-system')"
    echo "4. Select 'Read' permissions"
    echo "5. Copy the generated token"
    echo ""
    
    read -p "Enter your Hugging Face token (or press Enter to skip): " HF_TOKEN
    
    if [[ -n "$HF_TOKEN" ]]; then
        print_status "Token provided, will add to .env file"
        return 0
    else
        print_warning "No token provided - some models may not be accessible"
        return 1
    fi
}

# Function to update .env file
update_env_file() {
    local token="$1"
    
    print_header "Updating .env File"
    
    # Check if HUGGINGFACE_TOKEN already exists
    if grep -q "^HUGGINGFACE_TOKEN=" "$ENV_FILE"; then
        print_status "Updating existing HUGGINGFACE_TOKEN in .env file"
        # Update existing token
        sed -i "s/^HUGGINGFACE_TOKEN=.*/HUGGINGFACE_TOKEN=$token/" "$ENV_FILE"
    else
        print_status "Adding HUGGINGFACE_TOKEN to .env file"
        # Add new token at the end of the file
        echo "" >> "$ENV_FILE"
        echo "# Hugging Face Token for model downloads" >> "$ENV_FILE"
        echo "HUGGINGFACE_TOKEN=$token" >> "$ENV_FILE"
    fi
    
    print_status "Hugging Face token added to .env file"
}

# Function to test token
test_token() {
    local token="$1"
    
    print_header "Testing Hugging Face Token"
    
    print_status "Testing token with Hugging Face API..."
    
    # Test the token by making a request to the Hugging Face API
    RESPONSE=$(curl -s -H "Authorization: Bearer $token" \
        "https://huggingface.co/api/models/Pyzeur/Code-du-Travail-mistral-finetune" || echo "ERROR")
    
    if [[ "$RESPONSE" == "ERROR" ]]; then
        print_error "Failed to test token - network error"
        return 1
    elif echo "$RESPONSE" | grep -q "error"; then
        print_error "Token test failed - invalid token or insufficient permissions"
        return 1
    else
        print_status "✅ Token test successful - can access the model"
        return 0
    fi
}

# Function to restart services
restart_services() {
    print_header "Restarting Services"
    
    cd "$APP_DIR"
    
    print_status "Stopping services..."
    docker compose -f docker-compose-ssl.yml down
    
    print_status "Starting services with new configuration..."
    docker compose -f docker-compose-ssl.yml up -d
    
    print_status "Waiting for services to start..."
    sleep 10
    
    print_status "Services restarted successfully"
}

# Function to show next steps
show_next_steps() {
    print_header "Setup Complete"
    
    echo ""
    echo "🎉 Hugging Face token setup complete!"
    echo ""
    echo "Your custom model is now available:"
    echo "  - Model name: code-du-travail-mistral"
    echo "  - Path: Pyzeur/Code-du-Travail-mistral-finetune"
    echo ""
    echo "To use your custom model:"
    echo ""
    echo "1. Load the model:"
    echo "   curl -X POST https://ai.cryptomaltese.com/api/v1/models/code-du-travail-mistral/load"
    echo ""
    echo "2. Chat with the model:"
    echo "   curl -X POST https://ai.cryptomaltese.com/api/v1/chat \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"message\": \"Your question about French labor law\", \"model\": \"code-du-travail-mistral\"}'"
    echo ""
    echo "3. Or use the web interface:"
    echo "   https://ai.cryptomaltese.com/docs"
    echo ""
    echo "Note: The first time you load the model, it will download from Hugging Face"
    echo "This may take several minutes depending on your internet speed."
    echo ""
}

# Main function
main() {
    check_root
    
    print_header "Hugging Face Token Setup for AI Core System"
    echo ""
    
    # Check if .env file exists
    check_env_file
    echo ""
    
    # Get Hugging Face token
    if get_hf_token; then
        # Update .env file
        update_env_file "$HF_TOKEN"
        echo ""
        
        # Test token
        if test_token "$HF_TOKEN"; then
            echo ""
            # Restart services
            restart_services
            echo ""
            show_next_steps
        else
            print_warning "Token test failed, but continuing with setup"
            echo ""
            restart_services
            echo ""
            show_next_steps
        fi
    else
        print_warning "No token provided - continuing without Hugging Face token"
        echo ""
        show_next_steps
    fi
}

# Run main function
main "$@" 