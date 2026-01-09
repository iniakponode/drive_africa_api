#!/bin/bash
# Safe Drive Africa API Server Setup Script
# This script sets up the production environment on IONOS VPS

set -e

APP_DIR="/var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com"
SERVICE_NAME="safedriveapi-prod"
VENV_DIR="$APP_DIR/venv"
USER="www-data"
GROUP="www-data"
PYTHON_VERSION="3.11"

echo "🚀 Setting up Safe Drive Africa API..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root or with sudo"
    exit 1
fi

# Create application directory if it doesn't exist
if [ ! -d "$APP_DIR" ]; then
    mkdir -p $APP_DIR
    chown -R $USER:$GROUP $APP_DIR
    echo "✅ Created application directory: $APP_DIR"
fi

cd $APP_DIR

# Clone repository (if not exists)
if [ ! -d ".git" ]; then
    echo "📥 Please clone the repository manually:"
    echo "   cd $APP_DIR"
    echo "   git clone https://github.com/yourusername/drive_africa_api.git ."
    exit 1
fi

# Set up Python virtual environment
if [ ! -d "$VENV_DIR" ]; then
    python$PYTHON_VERSION -m venv $VENV_DIR
    echo "✅ Created virtual environment"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Installed dependencies"

# Create logs directory
mkdir -p $APP_DIR/logs
chown -R $USER:$GROUP $APP_DIR/logs
echo "✅ Created logs directory"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please create it manually or copy from .env.example"
    echo "   Required variables: DATABASE_URL, SECRET_KEY, ENVIRONMENT"
fi

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head
echo "✅ Applied database migrations"

# Create systemd service file
cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Safe Drive Africa API
After=network.target mysql.service

[Service]
User=$USER
Group=$GROUP
WorkingDirectory=$APP_DIR
Environment="ENVIRONMENT=production"
Environment="DATABASE_URL=mysql+pymysql://dev2:ProgressIniks2018@localhost:3306/drive_safe_db"

ExecStart=$VENV_DIR/bin/gunicorn \\
          -w 4 \\
          -k uvicorn.workers.UvicornWorker \\
          --log-level=info \\
          --access-logfile=- \\
          --error-logfile=- \\
          --capture-output \\
          -b 0.0.0.0:8000 \\
          --timeout 120 \\
          --keep-alive 5 \\
          --forwarded-allow-ips="*" \\
          main:app

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Created systemd service: $SERVICE_NAME"

# Reload systemd and start service
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME
echo "✅ Service started: $SERVICE_NAME"

# Set up log rotation
cat > /etc/logrotate.d/safedriveapi << EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $USER $GROUP
    sharedscripts
    postrotate
        systemctl reload $SERVICE_NAME > /dev/null 2>&1 || true
    endscript
}
EOF

echo "✅ Configured log rotation"

# Set correct permissions
chown -R $USER:$GROUP $APP_DIR
echo "✅ Set correct permissions"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Service status:"
systemctl status $SERVICE_NAME --no-pager
echo ""
echo "Next steps:"
echo "1. Update .env file with production credentials"
echo "2. Configure Nginx reverse proxy"
echo "3. Set up SSL certificate"
echo "4. Test API: curl http://localhost:8000/health"
