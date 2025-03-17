#!/bin/bash
set -e  # Exit if any command fails

# 🛠️ Configurable Variables
GITHUB_USERNAME="your-username"     # Change this
GITHUB_REPO="your-repo-name"        # Change this
GITHUB_TOKEN="your-personal-access-token"  # Use a GitHub token with read access
BACKUP_DIR="$HOME/github_backups"
BACKUP_FILE="${GITHUB_REPO}_backup_$(date +%Y%m%d_%H%M%S).tar.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Full mirror clone (GitHub official method)
git clone --mirror "https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/${GITHUB_USERNAME}/${GITHUB_REPO}.git" "$BACKUP_DIR/$GITHUB_REPO"

# Compress backup (best practice for efficient storage)
tar -czf "$BACKUP_DIR/$BACKUP_FILE" -C "$BACKUP_DIR" "$GITHUB_REPO"

# Cleanup
rm -rf "$BACKUP_DIR/$GITHUB_REPO"

echo "✅ GitHub backup completed: $BACKUP_DIR/$BACKUP_FILE"
