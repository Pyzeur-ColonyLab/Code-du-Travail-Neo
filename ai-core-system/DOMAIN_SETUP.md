# Domain Setup Guide for AI Core System

This guide will help you set up your AI Core System to be accessible through your `cryptomaltese.com` domain.

## Prerequisites

1. **Domain Control**: You must have control over the `cryptomaltese.com` domain
2. **DNS Access**: Ability to modify DNS records
3. **Server Access**: Root access to your Infomaniak server
4. **Ports Available**: Ports 80 and 443 must be available on your server

## Step 1: DNS Configuration

First, you need to configure your DNS to point to your server. Add these DNS records:

### A Records
```
cryptomaltese.com     A    YOUR_SERVER_IP
www.cryptomaltese.com A    YOUR_SERVER_IP
ai.cryptomaltese.com  A    YOUR_SERVER_IP
```

### CNAME Records (Optional)
```
api.cryptomaltese.com CNAME cryptomaltese.com
```

Replace `YOUR_SERVER_IP` with your actual server IP address.

## Step 2: Update Configuration Files

The configuration files have been updated to support your domain:

- ✅ `nginx/nginx.conf` - Updated for domain support
- ✅ `docker-compose.yml` - Updated to expose ports 80 and 443
- ✅ `scripts/setup_ssl.sh` - SSL certificate setup script

## Step 3: Deploy Updated Configuration

On your server, run these commands:

```bash
cd /opt/ai-core-system/Code-du-Travail-Neo/ai-core-system

# Pull the latest changes
git pull origin main

# Stop current containers
sudo docker compose down

# Create SSL directory
mkdir -p ssl

# Start containers with new configuration
sudo docker compose up -d
```

## Step 4: Set Up SSL Certificates

Run the SSL setup script:

```bash
# Make the script executable
chmod +x scripts/setup_ssl.sh

# Run the SSL setup
./scripts/setup_ssl.sh
```

**Note**: Before running this script, make sure:
1. Your DNS records are properly configured and propagated
2. Port 80 is available (the script will temporarily stop nginx)
3. You have a valid email address for Let's Encrypt notifications

## Step 5: Verify Setup

After the SSL setup is complete, test your endpoints:

```bash
# Test health endpoint
curl https://cryptomaltese.com/health

# Test API documentation
curl https://cryptomaltese.com/docs

# Test OpenAPI spec
curl https://cryptomaltese.com/openapi.json
```

## Step 6: Test Chat Functionality

Test the AI chat functionality:

```bash
curl -X POST https://cryptomaltese.com/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "model": "code-du-travail-mistral"
  }'
```

## Available URLs

Once set up, your AI Core System will be accessible at:

- **Main API**: `https://cryptomaltese.com`
- **API Documentation**: `https://cryptomaltese.com/docs`
- **Health Check**: `https://cryptomaltese.com/health`
- **OpenAPI Spec**: `https://cryptomaltese.com/openapi.json`
- **API Endpoints**: `https://cryptomaltese.com/api/v1/*`

Alternative domains:
- `https://www.cryptomaltese.com`
- `https://ai.cryptomaltese.com`

## Troubleshooting

### SSL Certificate Issues

If SSL setup fails:

1. **Check DNS propagation**:
   ```bash
   nslookup cryptomaltese.com
   ```

2. **Verify port 80 is available**:
   ```bash
   sudo netstat -tlnp | grep :80
   ```

3. **Check Let's Encrypt logs**:
   ```bash
   sudo tail -f /var/log/letsencrypt/letsencrypt.log
   ```

### Nginx Issues

If nginx fails to start:

1. **Check nginx configuration**:
   ```bash
   sudo docker exec ai-core-nginx nginx -t
   ```

2. **Check nginx logs**:
   ```bash
   sudo docker compose logs nginx
   ```

### Certificate Renewal

Certificates are automatically renewed daily. To manually renew:

```bash
sudo certbot renew
sudo docker compose restart nginx
```

## Security Considerations

1. **Firewall**: Ensure only necessary ports are open
2. **Rate Limiting**: Already configured in nginx
3. **Security Headers**: HTTPS and security headers are enabled
4. **Certificate Renewal**: Automatic renewal is configured

## Monitoring

Monitor your system with:

```bash
# Check container status
sudo docker compose ps

# Check logs
sudo docker compose logs -f

# Check SSL certificate expiration
sudo certbot certificates
```

## Support

If you encounter issues:

1. Check the logs: `sudo docker compose logs`
2. Verify DNS propagation
3. Ensure ports 80 and 443 are available
4. Check SSL certificate status

Your AI Core System should now be fully accessible through your domain with secure HTTPS connections! 