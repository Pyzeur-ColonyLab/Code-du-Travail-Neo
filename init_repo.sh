#!/bin/bash

# Code du Travail Neo - Git Repository Initialization Script
# =========================================================

echo "🚀 Initializing Code du Travail Neo Git Repository"
echo "=================================================="

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Initialize git repository
echo "📁 Initializing git repository..."
git init

# Add all files
echo "📝 Adding files to repository..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: Code du Travail Neo specifications

- Main AI Core System specification
- Telegram Service specification  
- Mail Service specification
- Deployment guide and documentation
- License and gitignore files

This repository contains comprehensive specifications for building
a modern, scalable AI system architecture with three microservices."

# Set up remote repository (optional)
echo ""
echo "🌐 Remote Repository Setup (Optional)"
echo "====================================="
echo "To connect to a remote repository (GitHub, GitLab, etc.), run:"
echo ""
echo "git remote add origin https://github.com/Pyzeur-ColonyLab/Code-du-Travail-Neo.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""

# Display repository status
echo "📊 Repository Status:"
echo "===================="
git status

echo ""
echo "✅ Repository initialization complete!"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Review the specifications in the .txt files"
echo "2. Set up your remote repository (GitHub/GitLab)"
echo "3. Follow the DEPLOYMENT_GUIDE.md for deployment"
echo "4. Start with the Main AI Core System (Phase 1)"
echo ""
echo "🎯 Happy coding!" 