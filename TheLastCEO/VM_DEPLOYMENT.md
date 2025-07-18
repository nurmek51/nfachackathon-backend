# VM Server Deployment Guide

This guide will help you deploy TheLastCEO game on a VM server with PostgreSQL database and WebSocket support.

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Domain name (for SSL certificates)
- Ports 80, 443, 5432, 6379 available

## 1. Server Setup

### Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes to take effect
```

### Clone the Repository

```bash
git clone <your-repository-url>
cd TheLastCEO
```

## 2. Environment Configuration

### Create Environment File

```bash
cp env.example .env
nano .env
```

### Configure Environment Variables

```bash
# Django Settings
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration (PostgreSQL)
POSTGRES_DB=thelastceo
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-very-secure-database-password

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Google Cloud Configuration (Optional)
GOOGLE_CLOUD_PROJECT_ID=your-google-cloud-project-id
GOOGLE_CLOUD_BUCKET_NAME=your-google-cloud-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/app/key.json

# SSL Certificate Domain
DOMAIN=yourdomain.com
```

## 3. SSL Certificate Setup

### Create Required Directories

```bash
mkdir -p certbot/www
mkdir -p certbot/conf
mkdir -p nginx/conf.d
```

### Generate SSL Certificate

```bash
# Make SSL setup script executable
chmod +x ssl-setup.sh

# Run SSL setup (replace with your domain)
./ssl-setup.sh yourdomain.com
```

## 4. Database Initialization

### Start Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### Initialize Database

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## 5. WebSocket Configuration

The application uses Django Channels with Redis for WebSocket support:

- **Redis**: Handles WebSocket message routing
- **Nginx**: Proxies WebSocket connections
- **Django Channels**: Manages WebSocket consumers

### Verify WebSocket Setup

```bash
# Check Redis connection
docker-compose exec redis redis-cli ping

# Check WebSocket consumer
docker-compose exec web python manage.py shell
```

In Django shell:
```python
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()
print("WebSocket setup is working!")
```

## 6. Production Deployment

### Use Production Configuration

```bash
# Stop development services
docker-compose down

# Start production services
docker-compose -f docker-compose.prod.yml up -d
```

### Production Environment Variables

For production, ensure these settings:

```bash
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SECRET_KEY=very-long-random-string
POSTGRES_PASSWORD=very-secure-password
```

## 7. Monitoring and Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
docker-compose logs -f redis
```

### Database Backup

```bash
# Create backup
docker-compose exec db pg_dump -U postgres thelastceo > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose exec -T db psql -U postgres thelastceo < backup_file.sql
```

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate
```

## 8. Security Considerations

### Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Database Security

- Use strong passwords
- Don't expose database port externally
- Regular backups
- Monitor access logs

### SSL Certificate Renewal

```bash
# Add to crontab for automatic renewal
0 12 * * * /path/to/your/project/ssl-setup.sh yourdomain.com >> /var/log/certbot-renew.log 2>&1
```

## 9. Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   docker-compose logs db
   docker-compose exec web python manage.py check --database default
   ```

2. **WebSocket Not Working**
   ```bash
   docker-compose logs redis
   docker-compose exec web python manage.py shell
   # Test channel layer
   ```

3. **SSL Certificate Issues**
   ```bash
   docker-compose logs nginx
   docker-compose logs certbot
   ```

4. **Static Files Not Loading**
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput
   docker-compose restart nginx
   ```

### Health Checks

```bash
# Check all services
docker-compose ps

# Test database connection
docker-compose exec web python health_check.py

# Test WebSocket
curl -I http://yourdomain.com/ws/game/
```

## 10. Performance Optimization

### Database Optimization

```bash
# Add to PostgreSQL configuration
docker-compose exec db psql -U postgres -c "ALTER SYSTEM SET shared_buffers = '256MB';"
docker-compose exec db psql -U postgres -c "ALTER SYSTEM SET effective_cache_size = '1GB';"
docker-compose restart db
```

### Redis Optimization

```bash
# Monitor Redis memory usage
docker-compose exec redis redis-cli info memory
```

### Nginx Optimization

The nginx configuration includes:
- Gzip compression
- Static file caching
- WebSocket proxy support
- SSL optimization

## 11. Backup Strategy

### Automated Backup Script

Create `backup.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Database backup
docker-compose exec -T db pg_dump -U postgres thelastceo > $BACKUP_DIR/db_backup_$DATE.sql

# Media files backup
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz media/

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

Make it executable and add to crontab:
```bash
chmod +x backup.sh
crontab -e
# Add: 0 2 * * * /path/to/backup.sh
```

## 12. Monitoring

### Basic Monitoring Commands

```bash
# System resources
htop
df -h
free -h

# Docker resources
docker stats

# Application logs
docker-compose logs --tail=100 -f
```

### Log Rotation

Add to `/etc/logrotate.d/docker`:
```
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size=1M
    missingok
    delaycompress
    copytruncate
}
```

## Support

For issues and questions:
1. Check the logs: `docker-compose logs`
2. Verify environment variables
3. Test individual services
4. Check network connectivity
5. Review SSL certificate status

The application is now ready for production use with PostgreSQL database and WebSocket support! 