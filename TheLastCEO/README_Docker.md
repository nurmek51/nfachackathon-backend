# Docker Setup for TheLastCEO Backend

This document provides instructions for building and running the Django backend using Docker with Supabase database.

## Prerequisites

- Docker
- Docker Compose
- Google Cloud credentials file (`key.json`)
- Supabase database (already deployed)

## Environment Variables

The application uses environment variables for configuration. Copy `env.example` to `.env` and configure your settings:

```bash
cp env.example .env
```

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | `your-django-secret-key-here` |
| `DEBUG` | Django debug mode | `True` (dev) / `False` (prod) |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1,*` |

### Database Configuration (Supabase)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Full Supabase database connection string | `postgresql://user:pass@host:port/db` |

### Redis Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `REDIS_HOST` | Redis host | `127.0.0.1` |
| `REDIS_PORT` | Redis port | `6379` |

### Google Cloud Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT_ID` | Google Cloud project ID | `your-project-id` |
| `GOOGLE_CLOUD_BUCKET_NAME` | Google Cloud Storage bucket | `your-bucket-name` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to credentials file | `path/to/key.json` |

### Application Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `AVATAR_GENERATION_ENABLED` | Enable avatar generation | `True` |
| `AVATAR_CACHE_TIMEOUT` | Avatar cache timeout (seconds) | `3600` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000` |
| `JWT_ACCESS_TOKEN_LIFETIME` | JWT access token lifetime (minutes) | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME` | JWT refresh token lifetime (minutes) | `1440` |
| `TIME_ZONE` | Application timezone | `Asia/Almaty` |

## Quick Start

### Development Environment

1. **Copy environment file:**
   ```bash
   cp env.example .env
   ```

2. **Configure your .env file** with your specific values.

3. **Build and run the development environment:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Backend API: http://localhost:8000
   - Admin interface: http://localhost:8000/admin
   - Nginx proxy: http://localhost
   - Redis: localhost:6379

5. **Stop the services:**
   ```bash
   docker-compose down
   ```

### Production Environment

1. **Copy and configure environment file:**
   ```bash
   cp env.example .env
   # Edit .env with production values
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
- **Database:** Connected to Supabase PostgreSQL

### Redis
- **Port:** 6379
- **Data:** Persistent volume
- **Features:** WebSocket channels, caching, Celery broker

### Nginx
- **Port:** 80, 443
- **Features:** Reverse proxy, static file serving, rate limiting

### Celery Worker (Optional)
- **Features:** Background task processing
- **Dependencies:** Redis, Backend

## Database Setup

This setup uses Supabase as the database provider. The database is already deployed and configured.

### Connection Details
- **Host:** `db.hpovgribnyikmxgbxtww.supabase.co`
- **Database:** `postgres`
- **User:** `postgres`
- **Port:** `5432`

### Migration Commands
```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Load initial data
docker-compose exec backend python manage.py loaddata initial_data
```

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
   # Check if Supabase is accessible
   docker-compose exec backend python manage.py dbshell
   
   # View backend logs
   docker-compose logs backend
   ```

3. **Redis connection issues:**
   ```bash
   # Check if Redis is running
   docker-compose ps
   
   # View Redis logs
   docker-compose logs redis
   ```

4. **Permission issues:**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

5. **Environment variable issues:**
   ```bash
   # Check if .env file exists
   ls -la .env
   
   # Verify environment variables are loaded
   docker-compose exec backend env | grep -E "(DEBUG|DATABASE|REDIS)"
   ```

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs redis
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f backend
```

## Security Notes

1. **Never commit sensitive data** like `.env` files or `key.json`
2. **Use strong passwords** for Django admin
3. **Enable HTTPS** in production
4. **Regularly update** base images and dependencies
5. **Monitor logs** for suspicious activity
6. **Use environment variables** for all sensitive configuration
7. **Secure Supabase connection** with proper credentials

## Performance Optimization

1. **Use production Dockerfile** for better performance
2. **Enable gzip compression** (already configured in nginx)
3. **Use Redis caching** for frequently accessed data
4. **Optimize database queries** and add indexes
5. **Use CDN** for static files in production

---

## Game Quiz (Kahoot-style) — Реализация и API

### Как добавить вопросы для квиза

Для добавления/обновления вопросов второго этапа (квиз):

1. Отредактируйте management-команду `game/management/commands/create_quiz_questions.py` или добавьте свои вопросы в аналогичном формате.
2. Выполните команду:
   ```bash
   docker-compose exec backend python manage.py create_quiz_questions
   ```
   Это удалит старые и добавит новые вопросы в базу.

### Как работает квиз (реальное время, как Kahoot)
- Вопрос отправляется всем игрокам через WebSocket (`quiz_question`).
- Игроки отправляют ответы (через WebSocket, тип `quiz_answer`).
- Ответы принимаются и сразу отображаются всем (тип `quiz_answer_received`).
- После таймера показывается статистика по вопросу (тип `quiz_results`): сколько кто ответил, кто был прав.
- После всех вопросов — подсчет очков (учитывается скорость и правильность), переход к следующему этапу.

#### Пример правильных ответов:
1. Бахаудин (B)
2. АААхх (D)
3. Talapacademy (B)
4. Бахредин (A)
5. Это городская легенда (C)
6. Куока AI (A)

### API для квиза
- `GET /quiz/questions/` — получить 6 случайных вопросов (авторизация обязательна).
  - Ответ:
    ```json
    {
      "questions": [
        {
          "id": 1,
          "question_text": "Как пишется полное имя Бахи:",
          "options": {"A": "Баха", "B": "Бахаудин", "C": "Бахауддин", "D": "Бахардуино"},
          "difficulty": 2,
          "category": "incubator"
        },
        ...
      ],
      "total_questions": 6
    }
    ```

### WebSocket события для квиза
- `quiz_question` — новый вопрос
- `quiz_answer_received` — кто-то ответил (реалтайм)
- `quiz_results` — статистика по вопросу

### Пример работы квиза (flow)
1. Сервер отправляет событие `quiz_question` с вопросом и вариантами.
2. Клиенты отправляют ответы через WebSocket (`quiz_answer`).
3. Сервер в реальном времени рассылает событие `quiz_answer_received` для каждого ответа.
4. По истечении времени — сервер отправляет событие `quiz_results` с правильным ответом и статистикой.
5. После всех вопросов — переход к следующему этапу игры.

--- 