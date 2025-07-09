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

copy_certificates() {
    # Copy certificates to the ssl directory
    echo "Copying certificates..."
    sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem ssl/cert.pem
    sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem ssl/key.pem

    # Set proper permissions
    sudo chown -R $USER:$USER ssl/
    chmod 600 ssl/key.pem
    chmod 644 ssl/cert.pem

    # Update docker-compose to use SSL
    echo "Updating docker-compose configuration for SSL..."
    
    # Backup current docker-compose
    cp docker-compose.yml docker-compose.yml.backup
    
    # Switch to SSL docker-compose configuration
    cp docker-compose-ssl.yml docker-compose.yml

    # Switch to SSL nginx configuration
    echo "Switching to SSL nginx configuration..."
    cp nginx/nginx-ssl.conf nginx/nginx.conf

    # Restart containers with SSL
    echo "Restarting containers with SSL..."
    sudo docker compose down
    sudo docker compose up -d

    echo "SSL setup complete!"
    echo "Your AI Core System is now accessible at:"
    echo "  - https://$DOMAIN"
    echo "  - https://www.$DOMAIN"

    # Set up automatic renewal
    echo "Setting up automatic certificate renewal..."
    (sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet && sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/ai-core-system/Code-du-Travail-Neo/ai-core-system/ssl/cert.pem && sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/ai-core-system/Code-du-Travail-Neo/ai-core-system/ssl/key.pem && cd /opt/ai-core-system/Code-du-Travail-Neo/ai-core-system && sudo docker compose restart nginx") | sudo crontab -

    echo "Certificate renewal has been scheduled to run daily at 12:00 PM"
}

setup_manual_dns() {
    echo "=========================================="
    echo "Manual DNS Challenge Setup"
    echo "=========================================="
    echo
    echo "This will use manual DNS challenge verification."
    echo "You'll need to manually add TXT records to your DNS."
    echo "This is the most reliable method for Infomaniak servers."
    echo
    
    # Get SSL certificate using manual DNS challenge
    echo "Requesting SSL certificate using DNS challenge..."
    echo "You will be prompted to add TXT records to your DNS."
    echo "Please have your DNS management interface ready."
    echo
    read -p "Press Enter to continue..."
    
    sudo certbot certonly --manual \
        --preferred-challenges=dns \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN \
        -d www.$DOMAIN
    
    copy_certificates
}

# Run the manual DNS setup
setup_manual_dns 