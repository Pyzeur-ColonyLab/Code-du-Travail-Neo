#!/bin/bash

# AI Core System - SSL Certificate Setup Script
# This script sets up SSL certificates using Let's Encrypt

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
WEBROOT="/var/www/html"

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

# Function to check domain resolution
check_domain() {
    local domain="$1"
    
    print_status "Checking domain resolution for $domain..."
    
    if nslookup "$domain" >/dev/null 2>&1; then
        print_success "Domain $domain resolves correctly"
        return 0
    else
        print_error "Domain $domain does not resolve. Please check DNS settings."
        return 1
    fi
}

# Function to install certbot
install_certbot() {
    print_status "Installing certbot..."
    
    # Update system
    apt-get update
    
    # Install certbot and nginx plugin
    apt-get install -y certbot python3-certbot-nginx
    
    # Verify installation
    if command_exists certbot; then
        print_success "Certbot installed successfully"
        certbot --version
    else
        print_error "Failed to install certbot"
        exit 1
    fi
}

# Function to setup webroot for ACME challenge
setup_webroot() {
    print_status "Setting up webroot for ACME challenge..."
    
    # Create webroot directory
    mkdir -p "$WEBROOT/.well-known/acme-challenge"
    
    # Set permissions
    chown -R www-data:www-data "$WEBROOT"
    chmod -R 755 "$WEBROOT"
    
    # Add location block to nginx for ACME challenge
    cat > /etc/nginx/sites-available/acme-challenge << 'EOF'
server {
    listen 80;
    server_name _;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/acme-challenge /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    nginx -t
    
    # Reload nginx
    systemctl reload nginx
    
    print_success "Webroot setup completed"
}

# Function to obtain SSL certificate
obtain_certificate() {
    local domain="$1"
    local email="$2"
    
    print_status "Obtaining SSL certificate for $domain..."
    
    # Stop nginx temporarily to free port 80
    systemctl stop nginx
    
    # Obtain certificate using standalone mode
    certbot certonly \
        --standalone \
        --email "$email" \
        --agree-tos \
        --no-eff-email \
        --domains "$domain" \
        --pre-hook "systemctl stop nginx" \
        --post-hook "systemctl start nginx"
    
    # Check if certificate was obtained
    if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
        print_success "SSL certificate obtained successfully"
        return 0
    else
        print_error "Failed to obtain SSL certificate"
        return 1
    fi
}

# Function to setup nginx with SSL
setup_nginx_ssl() {
    local domain="$1"
    
    print_status "Setting up Nginx with SSL..."
    
    # Create SSL configuration
    cat > /etc/nginx/sites-available/ai-core-ssl << EOF
# Upstream for AI API
upstream ai_api {
    server ai-api:8000;
    keepalive 32;
}

# HTTP server (redirect to HTTPS)
server {
    listen 80;
    server_name $domain;
    
    # ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Health check endpoint (no redirect)
    location /health {
        proxy_pass http://ai_api;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        access_log off;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $domain;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/$domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Health check endpoint
    location /health {
        proxy_pass http://ai_api;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        access_log off;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://ai_api;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
        proxy_http_version 1.1;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }

    # Documentation
    location /docs {
        proxy_pass http://ai_api;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # OpenAPI spec
    location /openapi.json {
        proxy_pass http://ai_api;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Root endpoint
    location / {
        proxy_pass http://ai_api;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Enable SSL site
    ln -sf /etc/nginx/sites-available/ai-core-ssl /etc/nginx/sites-enabled/
    
    # Test nginx configuration
    nginx -t
    
    # Reload nginx
    systemctl reload nginx
    
    print_success "Nginx SSL configuration completed"
}

# Function to setup certificate renewal
setup_renewal() {
    print_status "Setting up certificate renewal..."
    
    # Create renewal script
    cat > /usr/local/bin/renew-ssl.sh << 'EOF'
#!/bin/bash

# Renew SSL certificates
certbot renew --quiet

# Reload nginx if certificates were renewed
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "$(date): SSL certificates renewed successfully" >> /var/log/ssl-renewal.log
else
    echo "$(date): SSL certificate renewal failed" >> /var/log/ssl-renewal.log
fi
EOF
    
    # Make script executable
    chmod +x /usr/local/bin/renew-ssl.sh
    
    # Add cron job for automatic renewal
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/local/bin/renew-ssl.sh") | crontab -
    
    print_success "Certificate renewal setup completed"
}

# Function to test SSL configuration
test_ssl() {
    local domain="$1"
    
    print_status "Testing SSL configuration..."
    
    # Test HTTPS connection
    if curl -s -I "https://$domain" >/dev/null 2>&1; then
        print_success "HTTPS connection successful"
    else
        print_error "HTTPS connection failed"
        return 1
    fi
    
    # Test certificate validity
    if openssl s_client -connect "$domain:443" -servername "$domain" < /dev/null 2>/dev/null | openssl x509 -noout -dates; then
        print_success "SSL certificate is valid"
    else
        print_error "SSL certificate validation failed"
        return 1
    fi
    
    # Test security headers
    if curl -s -I "https://$domain" | grep -q "Strict-Transport-Security"; then
        print_success "Security headers are properly configured"
    else
        print_warning "Security headers may not be configured correctly"
    fi
}

# Function to show certificate information
show_cert_info() {
    local domain="$1"
    
    print_status "Certificate information for $domain:"
    
    if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
        echo "Certificate file: /etc/letsencrypt/live/$domain/fullchain.pem"
        echo "Private key file: /etc/letsencrypt/live/$domain/privkey.pem"
        echo
        
        echo "Certificate details:"
        openssl x509 -in "/etc/letsencrypt/live/$domain/fullchain.pem" -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:)"
        echo
        
        echo "Certificate expiration:"
        openssl x509 -in "/etc/letsencrypt/live/$domain/fullchain.pem" -noout -dates
    else
        print_error "Certificate files not found"
    fi
}

# Main function
main() {
    echo "=========================================="
    echo "AI Core System - SSL Certificate Setup"
    echo "=========================================="
    echo
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root"
        exit 1
    fi
    
    # Get configuration
    DOMAIN=$(get_input "Enter domain name" "$DOMAIN")
    EMAIL=$(get_input "Enter admin email" "$EMAIL")
    
    # Check domain resolution
    if ! check_domain "$DOMAIN"; then
        print_error "Domain check failed. Please fix DNS settings and try again."
        exit 1
    fi
    
    # Confirm setup
    echo
    print_warning "SSL Setup Configuration:"
    echo "  Domain: $DOMAIN"
    echo "  Email: $EMAIL"
    echo
    
    read -p "Proceed with SSL setup? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_status "SSL setup cancelled"
        exit 0
    fi
    
    # Start setup
    print_status "Starting SSL certificate setup..."
    
    # Install certbot
    install_certbot
    
    # Setup webroot
    setup_webroot
    
    # Obtain certificate
    if obtain_certificate "$DOMAIN" "$EMAIL"; then
        # Setup nginx with SSL
        setup_nginx_ssl "$DOMAIN"
        
        # Setup renewal
        setup_renewal
        
        # Test configuration
        test_ssl "$DOMAIN"
        
        # Show certificate information
        show_cert_info "$DOMAIN"
        
        print_success "SSL certificate setup completed successfully!"
        echo
        echo "Your AI Core System is now accessible at:"
        echo "  https://$DOMAIN"
        echo "  https://$DOMAIN/docs"
        echo "  https://$DOMAIN/health"
        echo
        echo "Certificate will be automatically renewed every 60 days."
    else
        print_error "SSL certificate setup failed"
        exit 1
    fi
}

# Run main function
main "$@" 