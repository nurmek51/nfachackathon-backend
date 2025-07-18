#!/bin/bash

# Build script for TheLastCEO
# This script handles the Docker build process

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building TheLastCEO application...${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from env.example...${NC}"
    cp env.example .env
    echo -e "${YELLOW}Please edit .env file with your configuration before starting services${NC}"
fi

# Check if required directories exist
if [ ! -d "certbot" ]; then
    echo -e "${YELLOW}Creating certbot directories...${NC}"
    mkdir -p certbot/www
    mkdir -p certbot/conf
    chmod -R 755 certbot/
fi

if [ ! -d "nginx/conf.d" ]; then
    echo -e "${YELLOW}Creating nginx directories...${NC}"
    mkdir -p nginx/conf.d
    chmod -R 755 nginx/
fi

# Build the application
echo -e "${YELLOW}Building Docker images...${NC}"
if docker compose build; then
    echo -e "${GREEN}Build completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Edit .env file with your configuration"
    echo "2. Run: docker compose up -d"
    echo "3. Run: docker compose exec web python manage.py migrate"
    echo "4. Run: docker compose exec web python manage.py createsuperuser"
else
    echo -e "${RED}Build failed!${NC}"
    echo -e "${YELLOW}Troubleshooting tips:${NC}"
    echo "1. Check if Docker is running"
    echo "2. Check if you have enough disk space"
    echo "3. Try: docker system prune -f"
    echo "4. Check the error messages above"
    exit 1
fi 