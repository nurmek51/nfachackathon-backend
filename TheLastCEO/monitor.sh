#!/bin/bash

# Monitoring script for TheLastCEO
# Usage: ./monitor.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 TheLastCEO System Monitor${NC}"
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

# Check service status
echo -e "${YELLOW}📊 Service Status:${NC}"
docker-compose ps

echo ""

# Check resource usage
echo -e "${YELLOW}💾 Resource Usage:${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

echo ""

# Check disk usage
echo -e "${YELLOW}💿 Disk Usage:${NC}"
df -h | grep -E "(Filesystem|/dev/)"

echo ""

# Check memory usage
echo -e "${YELLOW}🧠 Memory Usage:${NC}"
free -h

echo ""

# Check recent logs
echo -e "${YELLOW}📝 Recent Logs (last 10 lines):${NC}"
docker-compose logs --tail=10

echo ""

# Check database connection
echo -e "${YELLOW}🗄️  Database Connection Test:${NC}"
if docker-compose exec -T web python manage.py check --database default > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Database connection OK${NC}"
else
    echo -e "${RED}❌ Database connection failed${NC}"
fi

# Check Redis connection
echo -e "${YELLOW}🔴 Redis Connection Test:${NC}"
if docker-compose exec redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis connection OK${NC}"
else
    echo -e "${RED}❌ Redis connection failed${NC}"
fi

echo ""

# Check SSL certificate (if exists)
if [ -f "certbot/conf/live/$(grep server_name nginx/conf.d/default.conf | head -1 | awk '{print $2}' | sed 's/;//')/fullchain.pem" ]; then
    echo -e "${YELLOW}🔐 SSL Certificate Status:${NC}"
    CERT_FILE="certbot/conf/live/$(grep server_name nginx/conf.d/default.conf | head -1 | awk '{print $2}' | sed 's/;//')/fullchain.pem"
    if openssl x509 -checkend 86400 -noout -in "$CERT_FILE" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ SSL certificate is valid and not expiring soon${NC}"
    else
        echo -e "${RED}❌ SSL certificate is expiring soon or invalid${NC}"
    fi
fi

echo ""
echo -e "${BLUE}📋 Quick Actions:${NC}"
echo "  View all logs: docker-compose logs -f"
echo "  Restart services: docker-compose restart"
echo "  Stop services: docker-compose down"
echo "  Update application: git pull && docker-compose build && docker-compose up -d" 