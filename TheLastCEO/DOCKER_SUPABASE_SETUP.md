# Docker Setup with Supabase Database

## Quick Start

### 1. Setup Environment
```bash
# Copy environment file
cp env.example .env

# Edit .env if needed (should work with default Supabase settings)
nano .env
```

### 2. Start Services
```bash
# Development
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up --build
```

### 3. Access Application
- **Backend API:** http://localhost:8000
- **Nginx Proxy:** http://localhost
- **Admin Interface:** http://localhost:8000/admin

## Services

| Service | Port | Purpose |
|---------|------|---------|
| **Backend** | 8000 | Django application |
| **Redis** | 6379 | WebSocket channels & caching |
| **Nginx** | 80, 443 | Reverse proxy & static files |
| **Celery** | - | Background tasks (optional) |

## Database

- **Provider:** Supabase (PostgreSQL)
- **Host:** `db.hpovgribnyikmxgbxtww.supabase.co`
- **Database:** `postgres`
- **Connection:** Via `DATABASE_URL` environment variable

## Key Commands

```bash
# View logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Add quiz questions
docker-compose exec backend python manage.py create_quiz_questions

# Stop services
docker-compose down
```

## Environment Variables

The main variables you need to configure:

```bash
# Required
SECRET_KEY=your-secret-key
DEBUG=True  # False for production

# Database (Supabase)
DATABASE_URL=postgresql://postgres:123123123qwe!@db.hpovgribnyikmxgbxtww.supabase.co:5432/postgres

# Google Cloud
GOOGLE_CLOUD_PROJECT_ID=manifest-stream-462605-q8
GOOGLE_CLOUD_BUCKET_NAME=nfachahaton
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# Redis
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_PORT=6379
```

## Troubleshooting

### Database Connection Issues
```bash
# Test database connection
docker-compose exec backend python manage.py dbshell

# Check backend logs
docker-compose logs backend
```

### Redis Issues
```bash
# Check Redis status
docker-compose ps redis

# View Redis logs
docker-compose logs redis
```

### Port Conflicts
```bash
# Check what's using port 8000
lsof -i :8000

# Change ports in docker-compose.yml if needed
```

## Production Deployment

1. **Set production environment variables:**
   ```bash
   DEBUG=False
   SECRET_KEY=your-production-secret-key
   ```

2. **Use production compose file:**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

3. **Monitor logs:**
   ```bash
   docker-compose -f docker-compose.prod.yml logs -f
   ```

## Security Notes

- ✅ Never commit `.env` files
- ✅ Use strong `SECRET_KEY` in production
- ✅ Set `DEBUG=False` in production
- ✅ Secure your Supabase credentials
- ✅ Use HTTPS in production

## Architecture

```
Internet → Nginx (80/443) → Backend (8000) → Supabase Database
                    ↓
                Redis (6379) ← Backend (WebSocket/Caching)
```

This setup provides a clean, scalable architecture with:
- **Nginx** handling reverse proxy and static files
- **Django Backend** serving the API and WebSocket connections
- **Redis** managing real-time communication and caching
- **Supabase** providing the PostgreSQL database
- **Celery** (optional) for background task processing 