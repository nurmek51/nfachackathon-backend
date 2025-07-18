#!/bin/bash

# Production Deployment Script for TheLastCEO
# Usage: ./deploy.sh yourdomain.com

DOMAIN=$1

if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <domain>"
    echo "Example: $0 example.com"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting production deployment for $DOMAIN...${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Please don't run this script as root${NC}"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

# Create production environment file
echo -e "${YELLOW}📝 Creating production environment file...${NC}"
if [ ! -f .env ]; then
    cp env.production .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your actual values before continuing${NC}"
    echo -e "${YELLOW}   - Change SECRET_KEY${NC}"
    echo -e "${YELLOW}   - Change POSTGRES_PASSWORD${NC}"
    echo -e "${YELLOW}   - Update ALLOWED_HOSTS with your domain${NC}"
    echo -e "${YELLOW}   - Update CORS_ALLOWED_ORIGINS${NC}"
    read -p "Press Enter after editing .env file..."
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Update nginx configuration with domain
echo -e "${YELLOW}🔧 Updating nginx configuration...${NC}"
sed -i "s/yourdomain.com/$DOMAIN/g" nginx/conf.d/default.conf

# Create necessary directories
echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p certbot/www
mkdir -p certbot/conf
mkdir -p nginx/conf.d
mkdir -p media
mkdir -p staticfiles

# Set proper permissions
echo -e "${YELLOW}🔐 Setting permissions...${NC}"
chmod -R 755 certbot/
chmod -R 755 nginx/
chmod -R 755 media/
chmod -R 755 staticfiles/
chmod +x *.sh

# Build and start services
echo -e "${YELLOW}🏗️  Building Docker images...${NC}"
if docker-compose build; then
    echo -e "${GREEN}✅ Build completed successfully${NC}"
else
    echo -e "${RED}❌ Build failed${NC}"
    exit 1
fi

# Start services
echo -e "${YELLOW}🚀 Starting services...${NC}"
if docker-compose up -d; then
    echo -e "${GREEN}✅ Services started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start services${NC}"
    exit 1
fi

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 30

# Run database migrations
echo -e "${YELLOW}🗄️  Running database migrations...${NC}"
if docker-compose exec -T web python manage.py migrate; then
    echo -e "${GREEN}✅ Migrations completed${NC}"
else
    echo -e "${RED}❌ Migrations failed${NC}"
    exit 1
fi

# Collect static files
echo -e "${YELLOW}📦 Collecting static files...${NC}"
if docker-compose exec -T web python manage.py collectstatic --noinput; then
    echo -e "${GREEN}✅ Static files collected${NC}"
else
    echo -e "${RED}❌ Failed to collect static files${NC}"
    exit 1
fi

# Create superuser if needed
echo -e "${YELLOW}👤 Do you want to create a superuser? (y/n)${NC}"
read -p "" create_superuser
if [[ $create_superuser =~ ^[Yy]$ ]]; then
    docker-compose exec -T web python manage.py createsuperuser
fi

# Setup SSL certificate
echo -e "${YELLOW}🔐 Setting up SSL certificate...${NC}"
echo -e "${YELLOW}📧 Enter your email for SSL certificate:${NC}"
read -p "" email

if [ ! -z "$email" ]; then
    # Get SSL certificate
    docker-compose run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email $email \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN \
        -d www.$DOMAIN

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ SSL certificate obtained successfully${NC}"
        
        # Enable HTTPS in nginx
        sed -i 's/# server {/server {/g' nginx/conf.d/default.conf
        sed -i 's/#     listen 443/    listen 443/g' nginx/conf.d/default.conf
        sed -i 's/#     server_name/    server_name/g' nginx/conf.d/default.conf
        sed -i 's/#     ssl_certificate/    ssl_certificate/g' nginx/conf.d/default.conf
        sed -i 's/#     ssl_certificate_key/    ssl_certificate_key/g' nginx/conf.d/default.conf
        sed -i 's/#     ssl_protocols/    ssl_protocols/g' nginx/conf.d/default.conf
        sed -i 's/#     ssl_ciphers/    ssl_ciphers/g' nginx/conf.d/default.conf
        sed -i 's/#     ssl_prefer_server_ciphers/    ssl_prefer_server_ciphers/g' nginx/conf.d/default.conf
        sed -i 's/#     ssl_session_cache/    ssl_session_cache/g' nginx/conf.d/default.conf
        sed -i 's/#     ssl_session_timeout/    ssl_session_timeout/g' nginx/conf.d/default.conf
        sed -i 's/#     location \/static\//    location \/static\//g' nginx/conf.d/default.conf
        sed -i 's/#         alias/        alias/g' nginx/conf.d/default.conf
        sed -i 's/#         expires/        expires/g' nginx/conf.d/default.conf
        sed -i 's/#         add_header/        add_header/g' nginx/conf.d/default.conf
        sed -i 's/#     location \/media\//    location \/media\//g' nginx/conf.d/default.conf
        sed -i 's/#         alias/        alias/g' nginx/conf.d/default.conf
        sed -i 's/#         expires/        expires/g' nginx/conf.d/default.conf
        sed -i 's/#         add_header/        add_header/g' nginx/conf.d/default.conf
        sed -i 's/#     location \//    location \//g' nginx/conf.d/default.conf
        sed -i 's/#         proxy_pass/        proxy_pass/g' nginx/conf.d/default.conf
        sed -i 's/#         proxy_set_header/        proxy_set_header/g' nginx/conf.d/default.conf
        sed -i 's/#         proxy_redirect/        proxy_redirect/g' nginx/conf.d/default.conf
        sed -i 's/#         proxy_http_version/        proxy_http_version/g' nginx/conf.d/default.conf
        sed -i 's/#         proxy_set_header Upgrade/        proxy_set_header Upgrade/g' nginx/conf.d/default.conf
        sed -i 's/#         proxy_set_header Connection/        proxy_set_header Connection/g' nginx/conf.d/default.conf
        sed -i 's/# }/}/g' nginx/conf.d/default.conf
        
        # Reload nginx
        docker-compose exec nginx nginx -s reload
        echo -e "${GREEN}✅ HTTPS enabled${NC}"
    else
        echo -e "${YELLOW}⚠️  SSL certificate setup failed, continuing with HTTP${NC}"
    fi
fi

# Final status check
echo -e "${YELLOW}🔍 Checking service status...${NC}"
docker-compose ps

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}🌐 Your application is available at:${NC}"
echo -e "${GREEN}   HTTP:  http://$DOMAIN${NC}"
echo -e "${GREEN}   HTTPS: https://$DOMAIN (if SSL was configured)${NC}"
echo ""
echo -e "${YELLOW}📋 Useful commands:${NC}"
echo -e "${YELLOW}   View logs: docker-compose logs -f${NC}"
echo -e "${YELLOW}   Stop services: docker-compose down${NC}"
echo -e "${YELLOW}   Restart services: docker-compose restart${NC}"
echo -e "${YELLOW}   Update application: git pull && docker-compose build && docker-compose up -d${NC}"
echo ""
echo -e "${YELLOW}🔐 Don't forget to:${NC}"
echo -e "${YELLOW}   - Change default passwords in .env${NC}"
echo -e "${YELLOW}   - Set up SSL certificate renewal${NC}"
echo -e "${YELLOW}   - Configure firewall rules${NC}"
echo -e "${YELLOW}   - Set up monitoring and backups${NC}" 