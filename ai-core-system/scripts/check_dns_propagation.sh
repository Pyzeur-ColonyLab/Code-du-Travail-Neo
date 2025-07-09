#!/bin/bash

# DNS Propagation Checker for AI Core System
# This script checks DNS propagation from multiple locations

set -e

DOMAIN="cryptomaltese.com"
IPV4="84.234.31.196"
IPV6="2001:1600:16:10::66b"

echo "=========================================="
echo "DNS Propagation Checker"
echo "=========================================="
echo

echo "Checking DNS propagation for $DOMAIN..."
echo "Expected IPv4: $IPV4"
echo "Expected IPv6: $IPV6"
echo

# Function to check DNS resolution
check_dns() {
    local domain=$1
    local record_type=$2
    local expected_ip=$3
    
    echo "Checking $record_type record for $domain..."
    
    # Local check
    if command -v nslookup &> /dev/null; then
        local_result=$(nslookup $domain 2>/dev/null | grep -A1 "Name:" | tail -1 | awk '{print $2}' || echo "Failed")
        echo "  Local: $local_result"
        
        if [ "$local_result" = "$expected_ip" ]; then
            echo "  ✓ Local resolution matches expected IP"
        else
            echo "  ✗ Local resolution does not match expected IP"
        fi
    else
        echo "  ⚠️  nslookup not available"
    fi
    
    # Online check using external services
    echo "  Checking from external services..."
    
    # Using online DNS checker
    if command -v curl &> /dev/null; then
        # Check from multiple locations
        echo "  - From Google DNS (8.8.8.8):"
        google_result=$(dig +short @8.8.8.8 $domain $record_type 2>/dev/null | head -1 || echo "Failed")
        echo "    $google_result"
        
        echo "  - From Cloudflare DNS (1.1.1.1):"
        cloudflare_result=$(dig +short @1.1.1.1 $domain $record_type 2>/dev/null | head -1 || echo "Failed")
        echo "    $cloudflare_result"
        
        echo "  - From OpenDNS (208.67.222.222):"
        opendns_result=$(dig +short @208.67.222.222 $domain $record_type 2>/dev/null | head -1 || echo "Failed")
        echo "    $opendns_result"
    else
        echo "  ⚠️  curl not available for external checks"
    fi
    
    echo
}

# Check A records (IPv4)
check_dns $DOMAIN "A" $IPV4
check_dns "www.$DOMAIN" "A" $IPV4
check_dns "ai.$DOMAIN" "A" $IPV4

# Check AAAA records (IPv6)
check_dns $DOMAIN "AAAA" $IPV6
check_dns "www.$DOMAIN" "AAAA" $IPV6
check_dns "ai.$DOMAIN" "AAAA" $IPV6

echo "=========================================="
echo "DNS Propagation Status"
echo "=========================================="
echo

echo "If DNS is not propagating correctly:"
echo "1. Verify DNS records are added correctly in your registrar"
echo "2. Wait for propagation (can take up to 24 hours)"
echo "3. Check from different networks/locations"
echo "4. Use online tools:"
echo "   - https://whatsmydns.net"
echo "   - https://dnschecker.org"
echo "   - https://mxtoolbox.com"
echo

echo "Expected DNS Records:"
echo "cryptomaltese.com     A    $IPV4"
echo "cryptomaltese.com     AAAA $IPV6"
echo "www.cryptomaltese.com A    $IPV4"
echo "www.cryptomaltese.com AAAA $IPV6"
echo "ai.cryptomaltese.com  A    $IPV4"
echo "ai.cryptomaltese.com  AAAA $IPV6"
echo

echo "Testing connectivity once DNS resolves:"
echo "curl -I http://$DOMAIN"
echo "curl -I https://$DOMAIN"
echo "curl -I http://[$IPV6]"
echo "curl -I https://[$IPV6]" 