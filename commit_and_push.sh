#!/bin/bash

# Script to commit and push deployment script corrections
# Run this script from the root of the repository

echo "🚀 Committing and pushing cron fix..."

# Add all changes
git add .

# Commit with descriptive message
git commit -m "🔧 Fix cron installation and scheduling in deployment script

- Added cron package to system installation
- Added configure_cron() function to ensure cron service is running
- Added error handling for crontab commands
- Added checks to prevent duplicate cron jobs
- Added fallback messages when crontab is not available
- Fixed backup script scheduling
- Fixed SSL certificate auto-renewal scheduling

This fixes the 'crontab: command not found' error during deployment."

# Push to remote repository
git push origin main

echo "✅ Cron fix committed and pushed successfully!"
echo ""
echo "📋 Summary of changes:"
echo "- Fixed cron installation issue"
echo "- Added robust error handling for crontab"
echo "- Added cron service configuration"
echo "- Prevented duplicate cron jobs"
echo ""
echo "🎯 Next steps:"
echo "1. Test the deployment script again on your server"
echo "2. Verify cron jobs are properly scheduled"
echo "3. Check that backup and SSL renewal work correctly" 