#!/bin/bash
# Manual deployment script for Safe Drive Africa API
# Usage: ./scripts/deploy.sh

set -e

APP_DIR="/var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com"
SERVICE_NAME="safedriveapi-prod"

echo "🚀 Deploying Safe Drive Africa API..."

cd $APP_DIR

# Pull latest code
echo "📥 Pulling latest code from git..."
git fetch origin
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"
git pull origin $CURRENT_BRANCH

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database migrations
echo "🔄 Running database migrations..."
./scripts/migrate_db.sh

# Restart service
echo "🔄 Restarting service..."
sudo systemctl restart $SERVICE_NAME

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 5

# Check service status
echo "✅ Checking service status..."
sudo systemctl status $SERVICE_NAME --no-pager

# Health check
echo "🏥 Running health check..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    echo "Check logs: sudo journalctl -u $SERVICE_NAME -n 50"
    exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "View logs: sudo journalctl -u $SERVICE_NAME -f"
