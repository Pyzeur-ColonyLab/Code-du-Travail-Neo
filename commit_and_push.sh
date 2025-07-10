#!/bin/bash

# Script to commit and push deployment script corrections
# Run this script from the root of the repository

echo "🚀 Committing and pushing domain change to ai.cryptomaltese.com..."

# Add all changes
git add .

# Commit with descriptive message
git commit -m "🌐 Change domain from ai-api.cryptomaltese.com to ai.cryptomaltese.com

- Updated deployment script to use ai.cryptomaltese.com
- Updated pre-deployment guide with new domain
- Updated nginx SSL configuration to include ai.cryptomaltese.com
- Updated all documentation and examples
- Updated DNS configuration instructions
- Updated testing and troubleshooting sections

This change uses the existing DNS record for ai.cryptomaltese.com
instead of creating a new ai-api subdomain."

# Push to remote repository
git push origin main

echo "✅ Domain change committed and pushed successfully!"
echo ""
echo "📋 Summary of changes:"
echo "- Changed domain to ai.cryptomaltese.com"
echo "- Updated deployment script configuration"
echo "- Updated nginx SSL configuration"
echo "- Updated documentation and examples"
echo "- Updated DNS setup instructions"
echo ""
echo "🎯 Next steps:"
echo "1. Pull the latest changes on your server"
echo "2. Run the deployment script again"
echo "3. SSL certificate should work with existing DNS record" 