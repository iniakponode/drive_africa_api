#!/bin/bash
# Database migration script with backup
# Usage: ./scripts/migrate_db.sh

set -e

APP_DIR="/var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com"
BACKUP_DIR="$APP_DIR/backups"
DB_USER="dev2"
DB_PASSWORD="ProgressIniks2018"
DB_NAME="drive_safe_db"

# Load environment variables
if [ -f "$APP_DIR/.env" ]; then
    source "$APP_DIR/.env"
fi

cd $APP_DIR
source venv/bin/activate

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database before migration
echo "📦 Creating database backup..."
BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > $BACKUP_FILE
gzip $BACKUP_FILE
echo "✅ Backup created: ${BACKUP_FILE}.gz"

# Keep only last 10 backups
cd $BACKUP_DIR
ls -t db_backup_*.sql.gz | tail -n +11 | xargs -r rm
echo "✅ Cleaned old backups (keeping last 10)"

cd $APP_DIR

# Check current migration status
echo ""
echo "📊 Current migration status:"
alembic current

# Show pending migrations
echo ""
echo "📋 Pending migrations:"
alembic history --verbose | head -n 20

# Confirm before proceeding
echo ""
read -p "Apply migrations? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration cancelled"
    exit 0
fi

# Apply migrations
echo "🔄 Applying migrations..."
alembic upgrade head

echo "✅ Migrations complete!"

# Restart service
echo "🔄 Restarting service..."
sudo systemctl restart safedriveapi-prod
echo "✅ Service restarted"

# Check service status
sleep 3
sudo systemctl status safedriveapi-prod --no-pager

echo ""
echo "🎉 Database migration complete!"
echo "📦 Backup location: ${BACKUP_FILE}.gz"
