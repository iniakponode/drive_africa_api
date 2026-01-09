# CI/CD Documentation

This directory contains all the CI/CD and deployment automation files for Safe Drive Africa API.

## Files Overview

### GitHub Actions
- **`.github/workflows/deploy.yml`** - Automated CI/CD pipeline for testing and deployment

### Deployment Scripts
- **`scripts/server_setup.sh`** - Initial server setup script
- **`scripts/deploy.sh`** - Manual deployment script
- **`scripts/migrate_db.sh`** - Database migration with backup
- **`scripts/migrate_service.sh`** - Service name migration script

### Configuration
- **`.env.example`** - Example environment variables
- **`gunicorn.conf.py`** - Production-ready Gunicorn configuration
- **`docs/deployment-checklist.md`** - Comprehensive deployment checklist

## Quick Start

### 1. Configure GitHub Secrets

Add these secrets in GitHub repository settings:

```
SSH_PRIVATE_KEY        # Your SSH private key
SSH_USERNAME           # SSH username (e.g., root or your user)
SSH_PORT              # SSH port (default: 22)
PROD_HOST             # Production server hostname/IP
STAGING_HOST          # Staging server hostname/IP (optional)
```

### 2. Make Scripts Executable

```bash
chmod +x scripts/*.sh
```

### 3. Initial Server Setup

On your production server:

```bash
sudo ./scripts/server_setup.sh
```

### 4. Migrate Service Name (if upgrading)

If you're upgrading from the old `fastapi` service:

```bash
sudo ./scripts/migrate_service.sh
```

## Deployment Methods

### Automatic (via GitHub Actions)

Simply push to `main` branch:

```bash
git push origin main
```

The workflow will automatically:
1. Run tests
2. Deploy to production
3. Run database migrations
4. Restart the service
5. Perform health checks

### Manual Deployment

SSH into server and run:

```bash
cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com
./scripts/deploy.sh
```

## Service Management

```bash
# Status
sudo systemctl status safedriveapi-prod

# Restart
sudo systemctl restart safedriveapi-prod

# View logs
sudo journalctl -u safedriveapi-prod -f

# Stop/Start
sudo systemctl stop safedriveapi-prod
sudo systemctl start safedriveapi-prod
```

## Database Migrations

### Automatic (part of deployment)
Migrations run automatically during deployment.

### Manual Migration with Backup

```bash
./scripts/migrate_db.sh
```

This script:
1. Creates a timestamped database backup
2. Shows pending migrations
3. Applies migrations
4. Restarts the service

## Health Checks

Test the API health endpoint:

```bash
# Local
curl http://localhost:8000/health

# Production
curl https://api.safedriveafrica.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "2.0.0"
}
```

## Rollback

If deployment fails:

```bash
cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com
git reset --hard HEAD~1
source venv/bin/activate
pip install -r requirements.txt
alembic downgrade -1  # if migrations were applied
sudo systemctl restart safedriveapi-prod
```

## Monitoring

### View Logs

```bash
# Real-time logs
sudo journalctl -u safedriveapi-prod -f

# Last 100 lines
sudo journalctl -u safedriveapi-prod -n 100

# Logs from last hour
sudo journalctl -u safedriveapi-prod --since "1 hour ago"
```

### Check Processes

```bash
# Gunicorn processes
ps aux | grep gunicorn

# Port usage
netstat -tulpn | grep 8000

# System resources
htop
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Service won't start | `sudo journalctl -u safedriveapi-prod -n 100` |
| Database error | Check DATABASE_URL in `.env` |
| 502 Bad Gateway | Verify Gunicorn is running: `ps aux \| grep gunicorn` |
| Permission denied | `sudo chown -R www-data:www-data /var/www/...` |
| Port in use | `sudo lsof -i :8000` |

## Environment Setup

1. Copy example env file:
```bash
cp .env.example .env
```

2. Update with production values:
```bash
nano .env
```

Required variables:
- `DATABASE_URL` - MySQL connection string
- `SECRET_KEY` - Generate with `openssl rand -hex 32`
- `ENVIRONMENT` - Set to `production`

## Best Practices

1. **Always test on staging first** (if available)
2. **Create database backups before migrations**
3. **Monitor logs for 15-30 minutes after deployment**
4. **Use the deployment checklist** in `docs/deployment-checklist.md`
5. **Deploy during low-traffic hours** if possible
6. **Keep deployment announcement in team chat**

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u safedriveapi-prod -f`
2. Review deployment checklist
3. Consult AGENTS.md for system overview
4. Contact DevOps team

## Next Steps

- [ ] Set up staging environment
- [ ] Configure monitoring (e.g., Sentry, New Relic)
- [ ] Set up automated backups
- [ ] Configure log aggregation
- [ ] Add performance monitoring
- [ ] Set up uptime monitoring
