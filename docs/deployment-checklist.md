# Deployment Checklist

Use this checklist for every production deployment.

## Pre-Deployment

- [ ] All tests passing locally: `pytest tests/`
- [ ] Code reviewed and approved
- [ ] Database migrations tested on staging
- [ ] Environment variables verified in production `.env`
- [ ] CHANGELOG.md updated with new version
- [ ] Backup of production database created
- [ ] Team notified of deployment window

## Deployment Steps

### Automatic Deployment (via GitHub Actions)
1. [ ] Merge PR to `main` branch
2. [ ] Monitor GitHub Actions workflow
3. [ ] Wait for deployment to complete
4. [ ] Skip to Post-Deployment section

### Manual Deployment (via SSH)
1. [ ] SSH into production server: `ssh user@api.safedriveafrica.com`
2. [ ] Navigate to app directory: `cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com`
3. [ ] Pull latest code: `git pull origin main`
4. [ ] Activate virtual environment: `source venv/bin/activate`
5. [ ] Install dependencies: `pip install -r requirements.txt`
6. [ ] Run migrations: `alembic upgrade head`
7. [ ] Restart service: `sudo systemctl restart safedriveapi-prod`
8. [ ] Check logs: `sudo journalctl -u safedriveapi-prod -f`

**Or use deployment script:**
```bash
cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com
./scripts/deploy.sh
```

## Post-Deployment Verification

### Immediate Checks (0-5 minutes)
- [ ] Service is running: `sudo systemctl status safedriveapi-prod`
- [ ] Health check passes: `curl https://api.safedriveafrica.com/health`
- [ ] No errors in logs: `sudo journalctl -u safedriveapi-prod -n 100`

### Critical Endpoints (5-10 minutes)
Test these endpoints manually or with automated tests:
- [ ] Authentication: `POST /api/auth/login` or `/api/auth/me`
- [ ] Trips: `GET /api/trips/`
- [ ] Analytics: `GET /api/analytics/drivers/kpi`
- [ ] UBPK Metrics: `GET /api/ubpk/overview`

### Frontend Integration (10-15 minutes)
- [ ] React frontend connects successfully
- [ ] Login flow works
- [ ] Dashboard loads data
- [ ] No CORS errors in browser console

### Database Verification
- [ ] Migrations applied successfully
- [ ] No locked tables: `SHOW OPEN TABLES WHERE In_use > 0;`
- [ ] Recent data accessible
- [ ] No duplicate records created

### Performance Monitoring (15-30 minutes)
- [ ] Response times normal (< 500ms for most endpoints)
- [ ] No memory leaks (check `htop` or similar)
- [ ] Database connections stable
- [ ] No 5xx errors

## Rollback Procedure

If critical issues occur:

### Quick Rollback (Git)
```bash
cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com
git reset --hard HEAD~1
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart safedriveapi-prod
```

### Database Rollback
```bash
# Restore from backup
cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com/backups
gunzip -c db_backup_YYYYMMDD_HHMMSS.sql.gz | mysql -u dev2 -p drive_safe_db
```

### Full Rollback Steps
1. [ ] Stop service: `sudo systemctl stop safedriveapi-prod`
2. [ ] Revert code: `git reset --hard <previous-commit-hash>`
3. [ ] Restore database from backup (if migrations were applied)
4. [ ] Rollback Alembic: `alembic downgrade -1`
5. [ ] Reinstall dependencies: `pip install -r requirements.txt`
6. [ ] Start service: `sudo systemctl start safedriveapi-prod`
7. [ ] Verify health check
8. [ ] Notify team of rollback

## Communication

### Before Deployment
- [ ] Notify team in Slack/Discord/Email
- [ ] Post status: "Deployment starting at HH:MM"

### After Deployment
- [ ] Update status: "Deployment complete - monitoring"
- [ ] After 30 minutes: "Deployment stable ✅"

### If Issues Occur
- [ ] Immediately notify team
- [ ] Document issue and impact
- [ ] Execute rollback if critical
- [ ] Create incident report

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Service won't start | Check logs: `journalctl -u safedriveapi-prod -n 100` |
| Database connection error | Verify DATABASE_URL in .env |
| Migration fails | Rollback: `alembic downgrade -1` |
| 502 Bad Gateway | Check if Gunicorn is running on port 8000 |
| Permission denied | Fix ownership: `chown -R www-data:www-data /var/www/...` |

## Useful Commands

```bash
# Service management
sudo systemctl status safedriveapi-prod
sudo systemctl restart safedriveapi-prod
sudo systemctl stop safedriveapi-prod
sudo systemctl start safedriveapi-prod

# Logs
sudo journalctl -u safedriveapi-prod -f         # Follow logs
sudo journalctl -u safedriveapi-prod -n 100     # Last 100 lines
sudo journalctl -u safedriveapi-prod --since "1 hour ago"

# Database
mysql -u dev2 -p drive_safe_db
alembic current                                  # Current migration
alembic history                                  # Migration history

# Process monitoring
ps aux | grep gunicorn
netstat -tulpn | grep 8000
htop
```

## Sign-off

- **Deployed by:** ________________
- **Date/Time:** ________________
- **Version/Commit:** ________________
- **Verified by:** ________________
