# Environment Variables Setup

This document describes the environment variable configuration for TheLastCEO Django project.

## Overview

The project has been refactored to use environment variables for all configuration settings, making it more secure and flexible for different deployment environments.

## Files Modified

### 1. `config/settings.py`
- Added `python-dotenv` import and `load_dotenv()` call
- Replaced hardcoded values with `os.getenv()` calls
- Added fallback default values for all environment variables
- Updated database configuration to support both `DATABASE_URL` and individual settings
- Added Redis configuration variables
- Updated JWT settings to use environment variables
- Added static and media file configuration

### 2. `requirements.txt`
- Added `python-dotenv==1.0.0`
- Added `dj-database-url==2.1.0`

### 3. `game/avatar_service.py`
- Updated to use environment variables from Django settings
- Removed hardcoded Google Cloud configuration

### 4. `docker-compose.yml`
- Added `env_file: - .env` to all services
- Updated environment variables to use Docker variable substitution
- Made database and Redis configuration dynamic

### 5. `docker-compose.prod.yml`
- Added `env_file: - .env` to all services
- Updated environment variables to use Docker variable substitution

### 6. `env.example`
- Created comprehensive example file with all required environment variables
- Added detailed comments and examples for each variable

### 7. `README_Docker.md`
- Added comprehensive environment variables documentation
- Updated setup instructions to include .env configuration
- Added troubleshooting section for environment variable issues

## Environment Variables

### Required Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Django secret key | `your-django-secret-key-here` | Yes |
| `DEBUG` | Django debug mode | `True` (dev) / `False` (prod) | Yes |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1,*` | Yes |

### Database Configuration

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | Full database connection string | `postgresql://user:pass@host:port/db` | No* |
| `DB_NAME` | Database name | `postgres` | Yes** |
| `DB_USER` | Database user | `postgres` | Yes** |
| `DB_PASSWORD` | Database password | `your-password` | Yes** |
| `DB_HOST` | Database host | `localhost` | Yes** |
| `DB_PORT` | Database port | `5432` | Yes** |

*If `DATABASE_URL` is provided, individual DB_* variables are not needed
**Required if `DATABASE_URL` is not provided

### Redis Configuration

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` | No |
| `REDIS_HOST` | Redis host | `127.0.0.1` | No |
| `REDIS_PORT` | Redis port | `6379` | No |

### Google Cloud Configuration

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `GOOGLE_CLOUD_PROJECT_ID` | Google Cloud project ID | `your-project-id` | Yes |
| `GOOGLE_CLOUD_BUCKET_NAME` | Google Cloud Storage bucket | `your-bucket-name` | Yes |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to credentials file | `path/to/key.json` | Yes |

### Application Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AVATAR_GENERATION_ENABLED` | Enable avatar generation | `True` | No |
| `AVATAR_CACHE_TIMEOUT` | Avatar cache timeout (seconds) | `3600` | No |
| `CORS_ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000` | No |
| `JWT_ACCESS_TOKEN_LIFETIME` | JWT access token lifetime (minutes) | `60` | No |
| `JWT_REFRESH_TOKEN_LIFETIME` | JWT refresh token lifetime (minutes) | `1440` | No |
| `TIME_ZONE` | Application timezone | `Asia/Almaty` | No |
| `STATIC_URL` | Static files URL | `/static/` | No |
| `STATIC_ROOT` | Static files directory | `staticfiles/` | No |
| `MEDIA_URL` | Media files URL | `/media/` | No |
| `MEDIA_ROOT` | Media files directory | `media/` | No |

## Setup Instructions

### 1. Copy Environment File
```bash
cp env.example .env
```

### 2. Configure Environment Variables
Edit the `.env` file with your specific values:

```bash
# Django Settings
SECRET_KEY=your-actual-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*

# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/dbname
# OR use individual settings:
# DB_NAME=your_db_name
# DB_USER=your_db_user
# DB_PASSWORD=your_db_password
# DB_HOST=your_db_host
# DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=127.0.0.1
REDIS_PORT=6379

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT_ID=your-project-id
GOOGLE_CLOUD_BUCKET_NAME=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/key.json
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Test Configuration
```bash
python manage.py check
```

## Docker Setup

### Development
```bash
# Copy environment file
cp env.example .env

# Edit .env with your values
nano .env

# Start services
docker-compose up --build
```

### Production
```bash
# Copy environment file
cp env.example .env

# Edit .env with production values
nano .env

# Start production services
docker-compose -f docker-compose.prod.yml up --build
```

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong, unique values** for `SECRET_KEY`
3. **Set `DEBUG=False`** in production
4. **Use environment-specific values** for different deployments
5. **Rotate credentials regularly**
6. **Use secrets management** in production environments

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'dotenv'**
   ```bash
   pip install python-dotenv==1.0.0
   ```

2. **Environment variables not loading**
   - Check if `.env` file exists in project root
   - Verify file permissions
   - Check for syntax errors in `.env` file

3. **Database connection issues**
   - Verify database credentials in `.env`
   - Check if database server is running
   - Test connection manually

4. **Redis connection issues**
   - Verify Redis is running
   - Check Redis host and port in `.env`
   - Test Redis connection manually

### Testing Environment Variables

```bash
# Test Django settings
python manage.py check

# Test environment variable loading
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('SECRET_KEY:', os.getenv('SECRET_KEY', 'Not set'))"

# Test Django configuration
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); import django; django.setup(); from django.conf import settings; print('DEBUG:', settings.DEBUG)"
```

## Migration from Hardcoded Values

The project has been successfully migrated from hardcoded configuration values to environment variables. All existing functionality remains the same, but now the configuration is more flexible and secure.

### What Changed
- All sensitive configuration moved to environment variables
- Added fallback default values for backward compatibility
- Updated Docker configuration to use environment variables
- Added comprehensive documentation and examples

### Benefits
- **Security**: Sensitive data not in code
- **Flexibility**: Easy configuration for different environments
- **Maintainability**: Centralized configuration management
- **Deployment**: Easy deployment to different environments
- **Compliance**: Better security practices

## Next Steps

1. **Set up production environment** with proper `.env` file
2. **Configure CI/CD** to use environment variables
3. **Set up monitoring** for configuration issues
4. **Document deployment procedures** for different environments
5. **Set up secrets management** for production deployments 