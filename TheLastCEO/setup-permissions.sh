#!/bin/bash

# Setup permissions script for TheLastCEO
# This script sets up proper permissions for Docker and SSL certificates

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up permissions for TheLastCEO...${NC}"

# Create necessary directories with proper permissions
echo -e "${YELLOW}Creating directories...${NC}"

# Create certbot directories
mkdir -p certbot/www
mkdir -p certbot/conf
mkdir -p nginx/conf.d

# Create media and static directories
mkdir -p media
mkdir -p staticfiles

# Set proper permissions
echo -e "${YELLOW}Setting permissions...${NC}"

# Set permissions for certbot directories (readable by Docker)
chmod -R 755 certbot/
chmod -R 755 nginx/

# Set permissions for media and static directories
chmod -R 755 media/
chmod -R 755 staticfiles/

# Set permissions for scripts
chmod +x *.sh 2>/dev/null || true

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from env.example...${NC}"
    cp env.example .env
    echo -e "${GREEN}Please edit .env file with your configuration${NC}"
fi

# Set proper ownership (if running as root or with sudo)
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Setting ownership...${NC}"
    # Get the current user who ran sudo
    ACTUAL_USER=${SUDO_USER:-$USER}
    chown -R $ACTUAL_USER:$ACTUAL_USER .
fi

echo -e "${GREEN}Permissions setup completed!${NC}"
echo -e "${YELLOW}You can now run: docker compose build${NC}" 