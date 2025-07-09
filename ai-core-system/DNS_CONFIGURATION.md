# DNS Configuration Guide for AI Core System

This guide will help you configure your DNS records correctly for your AI Core System, whether you have IPv4, IPv6, or both.

## Quick DNS Setup

Based on your server configuration, you need to add the following DNS records to your domain registrar:

### For IPv6-Only Setup (Your Current Situation)

Since your server is returning an IPv6 address (`2001:1600:16:10::66b`), add these **AAAA records**:

```
cryptomaltese.com     AAAA 2001:1600:16:10::66b
www.cryptomaltese.com AAAA 2001:1600:16:10::66b
ai.cryptomaltese.com  AAAA 2001:1600:16:10::66b
```

### For Dual-Stack Setup (Recommended)

If you also have an IPv4 address, add both A and AAAA records:

```
cryptomaltese.com     A    YOUR_IPV4_ADDRESS
cryptomaltese.com     AAAA 2001:1600:16:10::66b
www.cryptomaltese.com A    YOUR_IPV4_ADDRESS
www.cryptomaltese.com AAAA 2001:1600:16:10::66b
ai.cryptomaltese.com  A    YOUR_IPV4_ADDRESS
ai.cryptomaltese.com  AAAA 2001:1600:16:10::66b
```

## How to Add DNS Records

### Step 1: Find Your Domain Registrar

Log into your domain registrar (where you purchased `cryptomaltese.com`). Common registrars include:
- Namecheap
- GoDaddy
- Google Domains
- Cloudflare
- Infomaniak
- OVH

### Step 2: Access DNS Management

Look for:
- "DNS Management"
- "DNS Settings"
- "Zone Editor"
- "DNS Records"

### Step 3: Add the Records

For each domain, add the appropriate record type:

#### AAAA Records (for IPv6)
- **Type**: AAAA
- **Name**: `cryptomaltese.com` (or leave blank for root domain)
- **Value**: `2001:1600:16:10::66b`
- **TTL**: 300 (or default)

#### A Records (for IPv4, if available)
- **Type**: A
- **Name**: `cryptomaltese.com` (or leave blank for root domain)
- **Value**: Your IPv4 address
- **TTL**: 300 (or default)

### Step 4: Verify Configuration

After adding the records, wait a few minutes and test:

```bash
# Test DNS resolution
nslookup cryptomaltese.com
nslookup www.cryptomaltese.com
nslookup ai.cryptomaltese.com
```

## Common DNS Record Types

| Type | Purpose | Example |
|------|---------|---------|
| A | IPv4 address | `192.168.1.1` |
| AAAA | IPv6 address | `2001:1600:16:10::66b` |
| CNAME | Alias to another domain | `api.cryptomaltese.com CNAME cryptomaltese.com` |
| MX | Mail server | `cryptomaltese.com MX 10 mail.cryptomaltese.com` |
| TXT | Text records (for SSL verification) | `_acme-challenge.cryptomaltese.com TXT "abc123"` |

## DNS Propagation

After adding DNS records:
- **Local propagation**: 5-10 minutes
- **Global propagation**: Up to 24 hours
- **Some ISPs**: Up to 48 hours

## Testing DNS Configuration

### Using nslookup
```bash
nslookup cryptomaltese.com
nslookup www.cryptomaltese.com
nslookup ai.cryptomaltese.com
```

### Using dig (if available)
```bash
dig cryptomaltese.com A
dig cryptomaltese.com AAAA
```

### Using online tools
- [whatsmydns.net](https://whatsmydns.net)
- [dnschecker.org](https://dnschecker.org)
- [mxtoolbox.com](https://mxtoolbox.com)

## Troubleshooting DNS Issues

### Problem: Domain doesn't resolve
**Solutions**:
1. Check if DNS records are added correctly
2. Wait for DNS propagation
3. Clear your local DNS cache
4. Try from a different network

### Problem: Only IPv6 resolves
**Solutions**:
1. Add AAAA records for IPv6
2. Ensure your server supports IPv6
3. Check if your network supports IPv6

### Problem: Only IPv4 resolves
**Solutions**:
1. Add A records for IPv4
2. Check if your server has an IPv4 address
3. Ensure your network supports IPv4

### Problem: SSL certificate fails
**Solutions**:
1. Ensure DNS resolves to the correct IP
2. Wait for DNS propagation
3. Use DNS challenge instead of HTTP challenge

## Special Considerations for Cloud Providers

### Infomaniak
- Supports both IPv4 and IPv6
- May require specific DNS configuration
- Check Infomaniak's DNS documentation

### Other Cloud Providers
- AWS: Use Route 53 for DNS management
- Google Cloud: Use Cloud DNS
- Azure: Use Azure DNS
- DigitalOcean: Use their DNS service

## Security Considerations

### DNSSEC
Consider enabling DNSSEC for additional security:
- Prevents DNS spoofing
- Ensures DNS record integrity
- Supported by most modern registrars

### DNS Security Extensions
- DNS over HTTPS (DoH)
- DNS over TLS (DoT)
- DNS filtering

## Monitoring DNS Health

### Regular Checks
```bash
# Check DNS resolution
nslookup cryptomaltese.com

# Check SSL certificate
openssl s_client -connect cryptomaltese.com:443 -servername cryptomaltese.com

# Check website availability
curl -I https://cryptomaltese.com
```

### Automated Monitoring
Consider setting up monitoring for:
- DNS resolution
- SSL certificate expiration
- Website availability
- Response times

## Next Steps

After configuring DNS:

1. **Wait for propagation** (up to 24 hours)
2. **Run the troubleshooting script**:
   ```bash
   ./scripts/troubleshoot_ssl.sh
   ```
3. **Set up SSL certificates**:
   ```bash
   ./scripts/setup_ssl_dns.sh
   ```
4. **Test your endpoints**:
   ```bash
   curl https://cryptomaltese.com/health
   ```

Your AI Core System should be accessible once DNS is properly configured and propagated! 