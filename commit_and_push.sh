#!/bin/bash

# Script to commit and push deployment script corrections
# Run this script from the root of the repository

echo "🚀 Committing and pushing docker compose command fix..."

# Add all changes
git add .

# Commit with descriptive message
git commit -m "🔧 Fix docker compose command detection and usage

- Added get_docker_compose_cmd() function to detect correct command
- Updated all docker-compose references to use detected command
- Added support for both 'docker compose' (newer) and 'docker-compose' (older)
- Fixed backup script generation to use correct command
- Fixed systemd service to use correct command
- Fixed deploy_application function to use correct command
- Fixed SSL setup to use correct command
- Added DOCKER_COMPOSE_CMD variable throughout script

This fixes the 'docker-compose: command not found' error during deployment."

# Push to remote repository
git push origin main

echo "✅ Docker compose command fix committed and pushed successfully!"
echo ""
echo "📋 Summary of changes:"
echo "- Added docker compose command detection"
echo "- Updated all docker-compose references"
echo "- Added support for both command formats"
echo "- Fixed backup script generation"
echo "- Fixed systemd service configuration"
echo ""
echo "🎯 Next steps:"
echo "1. Test the deployment script again on your server"
echo "2. Verify docker compose commands work correctly"
echo "3. Check that all services start properly" 