#!/bin/bash

# SSL Troubleshooting Script for AI Core System
# This script helps diagnose SSL certificate issues

set -e

DOMAIN="cryptomaltese.com"
SERVER_IP=$(curl -s ifconfig.me)

echo "=========================================="
echo "SSL Certificate Troubleshooting"
echo "=========================================="
echo

echo "1. Checking server IP address..."
echo "   Server IP: $SERVER_IP"
echo

echo "2. Checking DNS resolution..."
for domain in $DOMAIN www.$DOMAIN ai.$DOMAIN; do
    echo "   Checking $domain..."
    if nslookup $domain >/dev/null 2>&1; then
        resolved_ip=$(nslookup $domain | grep -A1 "Name:" | tail -1 | awk '{print $2}')
        echo "   ✓ $domain resolves to: $resolved_ip"
        if [ "$resolved_ip" = "$SERVER_IP" ]; then
            echo "   ✓ IP matches server IP"
        else
            echo "   ✗ IP does not match server IP ($SERVER_IP)"
        fi
    else
        echo "   ✗ $domain does not resolve"
    fi
    echo
done

echo "3. Checking port availability..."
echo "   Checking port 80..."
if sudo netstat -tlnp | grep :80 >/dev/null 2>&1; then
    echo "   ✗ Port 80 is in use:"
    sudo netstat -tlnp | grep :80
else
    echo "   ✓ Port 80 is available"
fi

echo "   Checking port 443..."
if sudo netstat -tlnp | grep :443 >/dev/null 2>&1; then
    echo "   ✗ Port 443 is in use:"
    sudo netstat -tlnp | grep :443
else
    echo "   ✓ Port 443 is available"
fi
echo

echo "4. Checking firewall status..."
if command -v ufw &> /dev/null; then
    echo "   UFW status:"
    sudo ufw status
elif command -v iptables &> /dev/null; then
    echo "   iptables rules for ports 80 and 443:"
    sudo iptables -L -n | grep -E "(80|443)"
else
    echo "   No firewall detected"
fi
echo

echo "5. Testing external connectivity..."
echo "   Testing if port 80 is reachable from internet..."
if curl -s --connect-timeout 10 http://$SERVER_IP >/dev/null 2>&1; then
    echo "   ✓ Port 80 is reachable from internet"
else
    echo "   ✗ Port 80 is not reachable from internet"
fi

echo "   Testing if port 443 is reachable from internet..."
if curl -s --connect-timeout 10 https://$SERVER_IP >/dev/null 2>&1; then
    echo "   ✓ Port 443 is reachable from internet"
else
    echo "   ✗ Port 443 is not reachable from internet"
fi
echo

echo "6. Checking Docker containers..."
echo "   Container status:"
sudo docker compose ps
echo

echo "7. Checking nginx logs..."
echo "   Recent nginx logs:"
sudo docker compose logs --tail=20 nginx
echo

echo "=========================================="
echo "Troubleshooting Summary"
echo "=========================================="
echo

echo "Common solutions:"
echo "1. If DNS doesn't resolve correctly:"
echo "   - Update your DNS records to point to $SERVER_IP"
echo "   - Wait for DNS propagation (can take up to 24 hours)"
echo

echo "2. If ports are blocked by firewall:"
echo "   - Contact Infomaniak support to open ports 80 and 443"
echo "   - Or configure your firewall to allow these ports"
echo

echo "3. If ports are in use by other services:"
echo "   - Stop conflicting services"
echo "   - Or use different ports and configure reverse proxy"
echo

echo "4. For Infomaniak specific issues:"
echo "   - Check Infomaniak control panel for port restrictions"
echo "   - Contact Infomaniak support for port 80/443 access"
echo "   - Consider using Infomaniak's built-in SSL certificate service"
echo

echo "5. Alternative SSL setup:"
echo "   - Use Infomaniak's SSL certificate service"
echo "   - Or use DNS challenge instead of HTTP challenge"
echo 