#!/bin/bash

# Backup script for TheLastCEO
# Usage: ./backup.sh [backup_name]

BACKUP_NAME=${1:-$(date +%Y%m%d_%H%M%S)}
BACKUP_DIR="./backups"
DATE=$(date +%Y-%m-%d_%H-%M-%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}💾 Starting backup: $BACKUP_NAME${NC}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
echo -e "${YELLOW}🗄️  Creating database backup...${NC}"
if docker-compose exec -T db pg_dump -U postgres thelastceo > "$BACKUP_DIR/db_backup_$BACKUP_NAME.sql"; then
    echo -e "${GREEN}✅ Database backup created: db_backup_$BACKUP_NAME.sql${NC}"
else
    echo -e "${RED}❌ Database backup failed${NC}"
    exit 1
fi

# Media files backup
echo -e "${YELLOW}📁 Creating media files backup...${NC}"
if tar -czf "$BACKUP_DIR/media_backup_$BACKUP_NAME.tar.gz" media/ 2>/dev/null; then
    echo -e "${GREEN}✅ Media backup created: media_backup_$BACKUP_NAME.tar.gz${NC}"
else
    echo -e "${YELLOW}⚠️  Media backup skipped (no media files or directory)${NC}"
fi

# Static files backup
echo -e "${YELLOW}📦 Creating static files backup...${NC}"
if tar -czf "$BACKUP_DIR/static_backup_$BACKUP_NAME.tar.gz" staticfiles/ 2>/dev/null; then
    echo -e "${GREEN}✅ Static files backup created: static_backup_$BACKUP_NAME.tar.gz${NC}"
else
    echo -e "${YELLOW}⚠️  Static files backup skipped (no staticfiles directory)${NC}"
fi

# Create backup info file
echo -e "${YELLOW}📝 Creating backup info...${NC}"
cat > "$BACKUP_DIR/backup_info_$BACKUP_NAME.txt" << EOF
Backup Information
==================
Backup Name: $BACKUP_NAME
Date: $DATE
Services: $(docker-compose ps --format "table {{.Name}}\t{{.Status}}")

Database Size: $(du -h "$BACKUP_DIR/db_backup_$BACKUP_NAME.sql" | cut -f1)
Media Size: $(du -h "$BACKUP_DIR/media_backup_$BACKUP_NAME.tar.gz" 2>/dev/null | cut -f1 || echo "N/A")
Static Size: $(du -h "$BACKUP_DIR/static_backup_$BACKUP_NAME.tar.gz" 2>/dev/null | cut -f1 || echo "N/A")

Restore Commands:
================
Database: docker-compose exec -T db psql -U postgres thelastceo < $BACKUP_DIR/db_backup_$BACKUP_NAME.sql
Media: tar -xzf $BACKUP_DIR/media_backup_$BACKUP_NAME.tar.gz
Static: tar -xzf $BACKUP_DIR/static_backup_$BACKUP_NAME.tar.gz
EOF

echo -e "${GREEN}✅ Backup info created: backup_info_$BACKUP_NAME.txt${NC}"

# Show backup summary
echo ""
echo -e "${GREEN}🎉 Backup completed successfully!${NC}"
echo -e "${YELLOW}📊 Backup Summary:${NC}"
ls -lh "$BACKUP_DIR"/*"$BACKUP_NAME"*

# Clean old backups (keep last 7 days)
echo -e "${YELLOW}🧹 Cleaning old backups (older than 7 days)...${NC}"
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.txt" -mtime +7 -delete

echo -e "${GREEN}✅ Backup process completed!${NC}" 