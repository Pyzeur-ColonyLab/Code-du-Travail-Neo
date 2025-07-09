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
- ✅ `scripts/setup_ssl.sh` - SSL certificate setup script (HTTP challenge)
- ✅ `scripts/setup_ssl_dns.sh` - SSL certificate setup script (DNS challenge)
- ✅ `scripts/troubleshoot_ssl.sh` - Troubleshooting script

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

## Step 4: Troubleshoot SSL Issues

If you encounter SSL certificate issues (common with cloud providers), run the troubleshooting script:

```bash
# Make the script executable
chmod +x scripts/troubleshoot_ssl.sh

# Run the troubleshooting script
./scripts/troubleshoot_ssl.sh
```

This will help identify common issues like:
- DNS resolution problems
- Port availability issues
- Firewall restrictions
- Container status problems

## Step 5: Set Up SSL Certificates

### Option A: HTTP Challenge (Standard Method)

If ports 80 and 443 are accessible from the internet:

```bash
# Make the script executable
chmod +x scripts/setup_ssl.sh

# Run the SSL setup
./scripts/setup_ssl.sh
```

### Option B: DNS Challenge (Recommended for Cloud Providers)

If HTTP challenge fails (common with Infomaniak), use DNS challenge:

```bash
# Make the script executable
chmod +x scripts/setup_ssl_dns.sh

# Run the DNS challenge SSL setup
./scripts/setup_ssl_dns.sh
```

This method supports:
- Manual DNS challenge (you add TXT records manually)
- Cloudflare DNS (automatic)
- Route53 DNS (automatic)
- Google Cloud DNS (automatic)

### Option C: Infomaniak SSL Service

If you're using Infomaniak, you can also use their built-in SSL certificate service:

1. Go to your Infomaniak control panel
2. Navigate to your domain settings
3. Enable SSL certificate service
4. Download the certificates and place them in the `ssl/` directory

## Step 6: Verify Setup

After the SSL setup is complete, test your endpoints:

```bash
# Test health endpoint
curl https://cryptomaltese.com/health

# Test API documentation
curl https://cryptomaltese.com/docs

# Test OpenAPI spec
curl https://cryptomaltese.com/openapi.json
```

## Step 7: Test Chat Functionality

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

## Common Issues and Solutions

### 1. SSL Certificate Issues

**Problem**: "Timeout during connect (likely firewall problem)"

**Solutions**:
- Use DNS challenge instead of HTTP challenge
- Contact Infomaniak support to open ports 80/443
- Use Infomaniak's built-in SSL service
- Check if another service is using port 80

### 2. DNS Resolution Issues

**Problem**: Domains don't resolve to your server

**Solutions**:
- Verify DNS records are correct
- Wait for DNS propagation (up to 24 hours)
- Use `nslookup` to check resolution
- Contact your DNS provider

### 3. Port Availability Issues

**Problem**: Ports 80 or 443 are already in use

**Solutions**:
- Stop conflicting services: `sudo netstat -tlnp | grep :80`
- Use different ports and configure reverse proxy
- Contact Infomaniak support

### 4. Firewall Issues

**Problem**: External connections are blocked

**Solutions**:
- Check UFW status: `sudo ufw status`
- Allow ports: `sudo ufw allow 80` and `sudo ufw allow 443`
- Contact Infomaniak support for firewall configuration

## Troubleshooting Commands

```bash
# Check DNS resolution
nslookup cryptomaltese.com

# Check port availability
sudo netstat -tlnp | grep -E "(80|443)"

# Check container status
sudo docker compose ps

# Check nginx logs
sudo docker compose logs nginx

# Check SSL certificate status
sudo certbot certificates

# Test external connectivity
curl -I http://YOUR_SERVER_IP
curl -I https://YOUR_SERVER_IP
```

## Security Considerations

1. **Firewall**: Ensure only necessary ports are open
2. **Rate Limiting**: Already configured in nginx
3. **Security Headers**: HTTPS and security headers are enabled
4. **Certificate Renewal**: Automatic renewal is configured
5. **DNS Security**: Consider using DNSSEC

## Monitoring

Monitor your system with:

```bash
# Check container status
sudo docker compose ps

# Check logs
sudo docker compose logs -f

# Check SSL certificate expiration
sudo certbot certificates

# Monitor system resources
htop
```

## Support

If you encounter issues:

1. Run the troubleshooting script: `./scripts/troubleshoot_ssl.sh`
2. Check the logs: `sudo docker compose logs`
3. Verify DNS propagation
4. Ensure ports 80 and 443 are available
5. Check SSL certificate status
6. Contact Infomaniak support if needed

## Alternative Setup Methods

### Using Infomaniak's Built-in Services

If you're having trouble with Let's Encrypt, consider using Infomaniak's services:

1. **Infomaniak SSL**: Use their built-in SSL certificate service
2. **Infomaniak Proxy**: Use their reverse proxy service
3. **Infomaniak Load Balancer**: Use their load balancing service

### Using Cloudflare

If you use Cloudflare for DNS:

1. Point your domain to Cloudflare
2. Use the Cloudflare DNS challenge method
3. Enable Cloudflare's SSL/TLS encryption

Your AI Core System should now be fully accessible through your domain with secure HTTPS connections! 