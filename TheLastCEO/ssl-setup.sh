#!/bin/bash

# SSL Setup Script for Django + Nginx + Certbot
# Usage: ./ssl-setup.sh yourdomain.com your@email.com

DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: $0 <domain> <email>"
    echo "Example: $0 example.com your@email.com"
    exit 1
fi

echo "🔐 Setting up SSL for domain: $DOMAIN"
echo "📧 Email: $EMAIL"

# Create directories if they don't exist
mkdir -p certbot/www certbot/conf

# Update nginx config with your domain
sed -i "s/yourdomain.com/$DOMAIN/g" nginx/conf.d/default.conf

# Start nginx and web services
echo "🚀 Starting services..."
docker-compose up -d nginx web

# Wait for nginx to start
echo "⏳ Waiting for nginx to start..."
sleep 10

# Get SSL certificate
echo "📜 Getting SSL certificate..."
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

if [ $? -eq 0 ]; then
    echo "✅ SSL certificate obtained successfully!"
    
    # Uncomment HTTPS server in nginx config
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
    echo "🔄 Reloading nginx..."
    docker-compose exec nginx nginx -s reload
    
    echo "🎉 SSL setup completed!"
    echo "🌐 Your site is now available at: https://$DOMAIN"
else
    echo "❌ Failed to obtain SSL certificate"
    echo "💡 Make sure your domain points to this server and port 80 is accessible"
    exit 1
fi 