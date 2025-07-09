#!/bin/bash

# SSL Setup Script for AI Core System using DNS Challenge
# This script sets up SSL certificates using DNS challenge (more reliable for cloud providers)

set -e

DOMAIN="cryptomaltese.com"
EMAIL="admin@cryptomaltese.com"  # Change this to your email

echo "Setting up SSL certificates for $DOMAIN using DNS challenge..."

# Create SSL directory
mkdir -p ssl

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo apt update
    sudo apt install -y certbot
fi

# Install DNS plugin for certbot (supports multiple providers)
echo "Installing certbot DNS plugins..."
sudo apt install -y python3-certbot-dns-cloudflare python3-certbot-dns-route53 python3-certbot-dns-google

echo "=========================================="
echo "DNS Challenge Setup"
echo "=========================================="
echo
echo "This method uses DNS challenge instead of HTTP challenge."
echo "It's more reliable for cloud providers like Infomaniak."
echo
echo "You have several options:"
echo "1. Manual DNS challenge (recommended for testing)"
echo "2. Cloudflare DNS (if you use Cloudflare)"
echo "3. Route53 DNS (if you use AWS)"
echo "4. Google Cloud DNS (if you use Google Cloud)"
echo

read -p "Choose your DNS provider (1-4) or press Enter for manual: " dns_choice

case $dns_choice in
    1|"")
        echo "Using manual DNS challenge..."
        setup_manual_dns
        ;;
    2)
        echo "Using Cloudflare DNS..."
        setup_cloudflare_dns
        ;;
    3)
        echo "Using Route53 DNS..."
        setup_route53_dns
        ;;
    4)
        echo "Using Google Cloud DNS..."
        setup_google_dns
        ;;
    *)
        echo "Invalid choice. Using manual DNS challenge..."
        setup_manual_dns
        ;;
esac

setup_manual_dns() {
    echo "=========================================="
    echo "Manual DNS Challenge Setup"
    echo "=========================================="
    echo
    echo "This will use manual DNS challenge verification."
    echo "You'll need to manually add TXT records to your DNS."
    echo
    
    # Get SSL certificate using manual DNS challenge
    echo "Requesting SSL certificate using DNS challenge..."
    sudo certbot certonly --manual \
        --preferred-challenges=dns \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN \
        -d www.$DOMAIN \
        -d ai.$DOMAIN
    
    copy_certificates
}

setup_cloudflare_dns() {
    echo "=========================================="
    echo "Cloudflare DNS Setup"
    echo "=========================================="
    echo
    echo "You'll need your Cloudflare API token."
    echo "Create one at: https://dash.cloudflare.com/profile/api-tokens"
    echo "Token needs: Zone:Zone:Read and Zone:DNS:Edit permissions"
    echo
    
    read -p "Enter your Cloudflare API token: " cf_token
    
    # Create Cloudflare credentials file
    cat > cloudflare.ini << EOF
dns_cloudflare_api_token = $cf_token
EOF
    
    chmod 600 cloudflare.ini
    
    # Get SSL certificate using Cloudflare DNS
    echo "Requesting SSL certificate using Cloudflare DNS..."
    sudo certbot certonly --dns-cloudflare \
        --dns-cloudflare-credentials cloudflare.ini \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN \
        -d www.$DOMAIN \
        -d ai.$DOMAIN
    
    # Clean up credentials
    rm cloudflare.ini
    
    copy_certificates
}

setup_route53_dns() {
    echo "=========================================="
    echo "Route53 DNS Setup"
    echo "=========================================="
    echo
    echo "You'll need your AWS access key and secret key."
    echo "The user needs Route53 permissions."
    echo
    
    read -p "Enter your AWS access key: " aws_key
    read -s -p "Enter your AWS secret key: " aws_secret
    echo
    
    # Create AWS credentials file
    cat > aws.ini << EOF
dns_route53_access_key = $aws_key
dns_route53_secret_access_key = $aws_secret
EOF
    
    chmod 600 aws.ini
    
    # Get SSL certificate using Route53 DNS
    echo "Requesting SSL certificate using Route53 DNS..."
    sudo certbot certonly --dns-route53 \
        --dns-route53-credentials aws.ini \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN \
        -d www.$DOMAIN \
        -d ai.$DOMAIN
    
    # Clean up credentials
    rm aws.ini
    
    copy_certificates
}

setup_google_dns() {
    echo "=========================================="
    echo "Google Cloud DNS Setup"
    echo "=========================================="
    echo
    echo "You'll need your Google Cloud service account key file."
    echo "The service account needs DNS Admin permissions."
    echo
    
    read -p "Enter path to your Google Cloud service account key file: " gcp_key_file
    
    # Get SSL certificate using Google Cloud DNS
    echo "Requesting SSL certificate using Google Cloud DNS..."
    sudo certbot certonly --dns-google \
        --dns-google-credentials $gcp_key_file \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN \
        -d www.$DOMAIN \
        -d ai.$DOMAIN
    
    copy_certificates
}

copy_certificates() {
    # Copy certificates to the ssl directory
    echo "Copying certificates..."
    sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/cert.pem
    sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/key.pem

    # Set proper permissions
    sudo chown -R $USER:$USER ssl/
    chmod 600 ssl/key.pem
    chmod 644 ssl/cert.pem

    # Start nginx with SSL
    echo "Starting nginx with SSL..."
    sudo docker compose up -d nginx

    echo "SSL setup complete!"
    echo "Your AI Core System is now accessible at:"
    echo "  - https://$DOMAIN"
    echo "  - https://www.$DOMAIN"
    echo "  - https://ai.$DOMAIN"

    # Set up automatic renewal
    echo "Setting up automatic certificate renewal..."
    sudo crontab -l 2>/dev/null | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet && sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/ai-core-system/Code-du-Travail-Neo/ai-core-system/ssl/cert.pem && sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/ai-core-system/Code-du-Travail-Neo/ai-core-system/ssl/key.pem && sudo docker compose restart nginx"; } | sudo crontab -

    echo "Certificate renewal has been scheduled to run daily at 12:00 PM"
}

# Run the appropriate setup function
if [ "$dns_choice" = "1" ] || [ -z "$dns_choice" ]; then
    setup_manual_dns
elif [ "$dns_choice" = "2" ]; then
    setup_cloudflare_dns
elif [ "$dns_choice" = "3" ]; then
    setup_route53_dns
elif [ "$dns_choice" = "4" ]; then
    setup_google_dns
fi 