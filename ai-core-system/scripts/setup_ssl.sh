#!/bin/bash

# SSL Setup Script for AI Core System
# This script sets up SSL certificates using Let's Encrypt

set -e

DOMAIN="cryptomaltese.com"
EMAIL="admin@cryptomaltese.com"  # Change this to your email

echo "Setting up SSL certificates for $DOMAIN..."

# Create SSL directory
mkdir -p ssl

# Install certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo apt update
    sudo apt install -y certbot
fi

# Stop nginx temporarily to free up port 80
echo "Stopping nginx temporarily..."
sudo docker compose stop nginx

# Get SSL certificate
echo "Requesting SSL certificate from Let's Encrypt..."
sudo certbot certonly --standalone \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN \
    -d ai.$DOMAIN

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