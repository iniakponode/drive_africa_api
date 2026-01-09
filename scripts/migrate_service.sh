#!/bin/bash
# Script to migrate from 'fastapi' service to 'safedriveapi-prod'
# Usage: sudo ./scripts/migrate_service.sh

set -e

OLD_SERVICE="fastapi"
NEW_SERVICE="safedriveapi-prod"
APP_DIR="/var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root or with sudo"
    exit 1
fi

echo "🔄 Migrating service from $OLD_SERVICE to $NEW_SERVICE..."

# Check if old service exists
if ! systemctl list-unit-files | grep -q "$OLD_SERVICE.service"; then
    echo "❌ Old service $OLD_SERVICE not found"
    exit 1
fi

# Create new service file
cat > /etc/systemd/system/$NEW_SERVICE.service << 'EOF'
[Unit]
Description=Safe Drive Africa API
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com
Environment="ENVIRONMENT=production"
Environment="DATABASE_URL=mysql+pymysql://dev2:ProgressIniks2018@localhost:3306/drive_safe_db"

ExecStart=/var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com/venv/bin/gunicorn \
          -w 4 \
          -k uvicorn.workers.UvicornWorker \
          --log-level=info \
          --access-logfile=- \
          --error-logfile=- \
          --capture-output \
          -b 0.0.0.0:8000 \
          --timeout 120 \
          --keep-alive 5 \
          --forwarded-allow-ips="*" \
          main:app

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Created new service file: /etc/systemd/system/$NEW_SERVICE.service"

# Reload systemd
systemctl daemon-reload
echo "✅ Reloaded systemd"

# Enable new service
systemctl enable $NEW_SERVICE
echo "✅ Enabled new service"

# Perform quick switch
echo "🔄 Switching services (3-5 seconds downtime)..."
systemctl stop $OLD_SERVICE
systemctl start $NEW_SERVICE

# Check status
echo "✅ Checking new service status..."
sleep 2
systemctl status $NEW_SERVICE --no-pager

# Test health endpoint
echo "🏥 Testing health endpoint..."
sleep 3
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "⚠️  Health check failed - rolling back..."
    systemctl stop $NEW_SERVICE
    systemctl start $OLD_SERVICE
    echo "❌ Rolled back to old service"
    exit 1
fi

echo ""
echo "🎉 Migration successful!"
echo ""
echo "Old service ($OLD_SERVICE) is stopped but not removed."
echo "Monitor the new service for 24-48 hours, then run:"
echo "  sudo systemctl disable $OLD_SERVICE"
echo "  sudo rm /etc/systemd/system/$OLD_SERVICE.service"
echo "  sudo systemctl daemon-reload"
echo ""
echo "New service commands:"
echo "  sudo systemctl status $NEW_SERVICE"
echo "  sudo systemctl restart $NEW_SERVICE"
echo "  sudo journalctl -u $NEW_SERVICE -f"
