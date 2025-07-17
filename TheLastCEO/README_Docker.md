# Docker Setup for TheLastCEO Backend

This document provides instructions for building and running the Django backend using Docker.

## Prerequisites

- Docker
- Docker Compose
- Google Cloud credentials file (`key.json`)

## Quick Start

### Development Environment

1. **Build and run the development environment:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Backend API: http://localhost:8000
   - Admin interface: http://localhost:8000/admin
   - PostgreSQL: localhost:5432
   - Redis: localhost:6379

3. **Stop the services:**
   ```bash
   docker-compose down
   ```

### Production Environment

1. **Create a `.env` file with your production settings:**
   ```bash
   # Database
   DATABASE_URL=postgresql://user:password@host:port/dbname
   POSTGRES_DB=your_db_name
   POSTGRES_USER=your_db_user
   POSTGRES_PASSWORD=your_secure_password
   
   # Django
   SECRET_KEY=your_django_secret_key
   DEBUG=False
   
   # Google Cloud
   GOOGLE_CLOUD_PROJECT_ID=your_project_id
   GOOGLE_CLOUD_BUCKET_NAME=your_bucket_name
   
   # Redis
   REDIS_URL=redis://redis:6379/0
   ```

2. **Build and run the production environment:**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build
   ```

3. **Access the application:**
   - Backend API: http://localhost
   - Admin interface: http://localhost/admin

## Docker Commands

### Development

```bash
# Build and start all services
docker-compose up --build

# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild a specific service
docker-compose build backend

# Run Django management commands
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py collectstatic
```

### Production

```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up --build

# Start in background
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Stop services
docker-compose -f docker-compose.prod.yml down
```

## Individual Docker Commands

### Build the image
```bash
# Development
docker build -t thelastceo-backend .

# Production
docker build -f Dockerfile.prod -t thelastceo-backend:prod .
```

### Run the container
```bash
# Development
docker run -p 8000:8000 -v $(pwd):/app thelastceo-backend

# Production
docker run -p 8000:8000 thelastceo-backend:prod
```

## Services

### Backend (Django)
- **Port:** 8000
- **Environment:** Development/Production
- **Features:** API endpoints, admin interface, WebSocket support

### Database (PostgreSQL)
- **Port:** 5432
- **Data:** Persistent volume
- **Features:** User data, game sessions, statistics

### Redis
- **Port:** 6379
- **Data:** Persistent volume
- **Features:** WebSocket channels, caching, Celery broker

### Nginx (Production only)
- **Port:** 80, 443
- **Features:** Reverse proxy, static file serving, rate limiting

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DEBUG` | Django debug mode | `True` (dev) / `False` (prod) |
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `SECRET_KEY` | Django secret key | - |
| `GOOGLE_CLOUD_PROJECT_ID` | Google Cloud project ID | - |
| `GOOGLE_CLOUD_BUCKET_NAME` | Google Cloud Storage bucket | - |

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Kill the process or change the port in docker-compose.yml
   ```

2. **Database connection issues:**
   ```bash
   # Check if database is running
   docker-compose ps
   
   # View database logs
   docker-compose logs db
   ```

3. **Permission issues:**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

4. **Build cache issues:**
   ```bash
   # Clear Docker build cache
   docker builder prune
   
   # Rebuild without cache
   docker-compose build --no-cache
   ```

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs db
docker-compose logs redis

# Follow logs in real-time
docker-compose logs -f backend
```

## Security Notes

1. **Never commit sensitive data** like `.env` files or `key.json`
2. **Use strong passwords** for database and Django admin
3. **Enable HTTPS** in production
4. **Regularly update** base images and dependencies
5. **Monitor logs** for suspicious activity

## Performance Optimization

1. **Use production Dockerfile** for better performance
2. **Enable gzip compression** (already configured in nginx)
3. **Use Redis caching** for frequently accessed data
4. **Optimize database queries** and add indexes
5. **Use CDN** for static files in production 