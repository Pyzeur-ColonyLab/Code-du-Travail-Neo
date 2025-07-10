#!/bin/bash

# Script to commit and push deployment script corrections
# Run this script from the root of the repository

echo "🚀 Committing and pushing DNS tool fixes..."

# Add all changes
git add .

# Commit with descriptive message
git commit -m "🔧 Fix DNS resolution tools and add fallbacks

- Added dnsutils package to system installation
- Updated DNS resolution check to use dig instead of nslookup
- Added fallback to host command if dig is not available
- Added automatic installation of dnsutils if no DNS tools found
- Updated pre-deployment guide to use dig and host commands
- Added IP validation regex to ensure valid IP addresses
- Improved error handling for DNS resolution failures

This fixes the 'nslookup: command not found' error and provides
better DNS resolution checking across different systems."

# Push to remote repository
git push origin main

echo "✅ DNS tool fixes committed and pushed successfully!"
echo ""
echo "📋 Summary of changes:"
echo "- Added dnsutils package installation"
echo "- Updated DNS resolution to use dig with fallbacks"
echo "- Added automatic DNS tool installation"
echo "- Updated documentation to use dig/host commands"
echo "- Added IP validation for DNS results"
echo ""
echo "🎯 Next steps:"
echo "1. Pull the latest changes on your server"
echo "2. Run the deployment script again"
echo "3. DNS resolution should now work properly" 