#!/bin/bash

# SSL Troubleshooting Script for AI Core System
# This script helps diagnose SSL certificate issues

set -e

DOMAIN="cryptomaltese.com"

echo "=========================================="
echo "SSL Certificate Troubleshooting"
echo "=========================================="
echo

echo "1. Checking server IP addresses..."
echo "   IPv4 address:"
if command -v curl &> /dev/null; then
    IPV4=$(curl -s -4 ifconfig.me 2>/dev/null || echo "Not available")
    echo "   $IPV4"
else
    echo "   curl not available"
fi

echo "   IPv6 address:"
if command -v curl &> /dev/null; then
    IPV6=$(curl -s -6 ifconfig.me 2>/dev/null || echo "Not available")
    echo "   $IPV6"
else
    echo "   curl not available"
fi

echo "   Local IP addresses:"
if command -v ip &> /dev/null; then
    echo "   $(ip route get 1.1.1.1 | awk '{print $7; exit}')"
else
    echo "   ip command not available"
fi
echo

echo "2. Checking DNS resolution..."
for domain in $DOMAIN www.$DOMAIN ai.$DOMAIN; do
    echo "   Checking $domain..."
    if nslookup $domain >/dev/null 2>&1; then
        resolved_ip=$(nslookup $domain | grep -A1 "Name:" | tail -1 | awk '{print $2}')
        echo "   ✓ $domain resolves to: $resolved_ip"
        
        # Check if it's IPv4 or IPv6
        if [[ $resolved_ip =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            echo "   ✓ IPv4 address detected"
        elif [[ $resolved_ip =~ ^[0-9a-fA-F:]+$ ]]; then
            echo "   ✓ IPv6 address detected"
        fi
    else
        echo "   ✗ $domain does not resolve"
    fi
    echo
done

echo "3. Checking port availability..."
echo "   Checking port 80..."
if command -v ss &> /dev/null; then
    if sudo ss -tlnp | grep :80 >/dev/null 2>&1; then
        echo "   ✗ Port 80 is in use:"
        sudo ss -tlnp | grep :80
    else
        echo "   ✓ Port 80 is available"
    fi
elif command -v netstat &> /dev/null; then
    if sudo netstat -tlnp | grep :80 >/dev/null 2>&1; then
        echo "   ✗ Port 80 is in use:"
        sudo netstat -tlnp | grep :80
    else
        echo "   ✓ Port 80 is available"
    fi
else
    echo "   ⚠️  Cannot check port availability (ss/netstat not available)"
fi

echo "   Checking port 443..."
if command -v ss &> /dev/null; then
    if sudo ss -tlnp | grep :443 >/dev/null 2>&1; then
        echo "   ✗ Port 443 is in use:"
        sudo ss -tlnp | grep :443
    else
        echo "   ✓ Port 443 is available"
    fi
elif command -v netstat &> /dev/null; then
    if sudo netstat -tlnp | grep :443 >/dev/null 2>&1; then
        echo "   ✗ Port 443 is in use:"
        sudo netstat -tlnp | grep :443
    else
        echo "   ✓ Port 443 is available"
    fi
else
    echo "   ⚠️  Cannot check port availability (ss/netstat not available)"
fi
echo

echo "4. Checking firewall status..."
if command -v ufw &> /dev/null; then
    echo "   UFW status:"
    sudo ufw status
elif command -v iptables &> /dev/null; then
    echo "   iptables rules for ports 80 and 443:"
    sudo iptables -L -n | grep -E "(80|443)" || echo "   No specific rules found"
else
    echo "   No firewall detected"
fi
echo

echo "5. Testing external connectivity..."
if [ "$IPV4" != "Not available" ] && [ "$IPV4" != "" ]; then
    echo "   Testing IPv4 connectivity on port 80..."
    if curl -s --connect-timeout 10 --max-time 15 http://$IPV4 >/dev/null 2>&1; then
        echo "   ✓ IPv4 port 80 is reachable from internet"
    else
        echo "   ✗ IPv4 port 80 is not reachable from internet"
    fi

    echo "   Testing IPv4 connectivity on port 443..."
    if curl -s --connect-timeout 10 --max-time 15 https://$IPV4 >/dev/null 2>&1; then
        echo "   ✓ IPv4 port 443 is reachable from internet"
    else
        echo "   ✗ IPv4 port 443 is not reachable from internet"
    fi
else
    echo "   ⚠️  Cannot test IPv4 connectivity (no IPv4 address detected)"
fi

if [ "$IPV6" != "Not available" ] && [ "$IPV6" != "" ]; then
    echo "   Testing IPv6 connectivity on port 80..."
    if curl -s --connect-timeout 10 --max-time 15 http://[$IPV6] >/dev/null 2>&1; then
        echo "   ✓ IPv6 port 80 is reachable from internet"
    else
        echo "   ✗ IPv6 port 80 is not reachable from internet"
    fi

    echo "   Testing IPv6 connectivity on port 443..."
    if curl -s --connect-timeout 10 --max-time 15 https://[$IPV6] >/dev/null 2>&1; then
        echo "   ✓ IPv6 port 443 is reachable from internet"
    else
        echo "   ✗ IPv6 port 443 is not reachable from internet"
    fi
else
    echo "   ⚠️  Cannot test IPv6 connectivity (no IPv6 address detected)"
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

echo "IP Address Analysis:"
if [ "$IPV4" != "Not available" ] && [ "$IPV4" != "" ]; then
    echo "✓ IPv4 address detected: $IPV4"
    echo "  - Add A records pointing to this address"
else
    echo "✗ No IPv4 address detected"
    echo "  - Your server may be IPv6-only"
    echo "  - Add AAAA records pointing to your IPv6 address"
fi

if [ "$IPV6" != "Not available" ] && [ "$IPV6" != "" ]; then
    echo "✓ IPv6 address detected: $IPV6"
    echo "  - Add AAAA records pointing to this address"
else
    echo "✗ No IPv6 address detected"
fi
echo

echo "DNS Configuration Recommendations:"
echo "1. For IPv4-only setup:"
echo "   cryptomaltese.com     A    $IPV4"
echo "   www.cryptomaltese.com A    $IPV4"
echo "   ai.cryptomaltese.com  A    $IPV4"
echo

echo "2. For IPv6-only setup:"
echo "   cryptomaltese.com     AAAA $IPV6"
echo "   www.cryptomaltese.com AAAA $IPV6"
echo "   ai.cryptomaltese.com  AAAA $IPV6"
echo

echo "3. For dual-stack setup (recommended):"
echo "   cryptomaltese.com     A    $IPV4"
echo "   cryptomaltese.com     AAAA $IPV6"
echo "   www.cryptomaltese.com A    $IPV4"
echo "   www.cryptomaltese.com AAAA $IPV6"
echo "   ai.cryptomaltese.com  A    $IPV4"
echo "   ai.cryptomaltese.com  AAAA $IPV6"
echo

echo "Common solutions:"
echo "1. If DNS doesn't resolve correctly:"
if [ "$IPV4" != "Not available" ] && [ "$IPV4" != "" ]; then
    echo "   - Update your DNS A records to point to $IPV4"
fi
if [ "$IPV6" != "Not available" ] && [ "$IPV6" != "" ]; then
    echo "   - Update your DNS AAAA records to point to $IPV6"
fi
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