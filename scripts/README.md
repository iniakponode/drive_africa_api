# Scripts Directory

This directory contains utility scripts for deployment, database management, and seeding.

## Deployment Scripts

### `server_setup.sh`
Initial server setup for production environment.

```bash
sudo ./scripts/server_setup.sh
```

### `deploy.sh`
Manual deployment script.

```bash
./scripts/deploy.sh
```

### `migrate_db.sh`
Run database migrations with automatic backup.

```bash
./scripts/migrate_db.sh
```

### `migrate_service.sh`
Migrate from old `fastapi` service to `safedriveapi-prod`.

```bash
sudo ./scripts/migrate_service.sh
```

## Seeding Scripts

### `seed_api_keys.py`
Create basic API clients (Admin & Researcher).

```bash
python scripts/seed_api_keys.py
```

### `seed_with_existing_data.py`
Create API clients for existing fleets, drivers, and insurance partners.

```bash
python scripts/seed_with_existing_data.py
```

**⚠️ Important:** Both seeding scripts output API keys that cannot be retrieved later. Save them immediately!

## Usage

1. Make scripts executable:
```bash
chmod +x scripts/*.sh
```

2. Run from project root:
```bash
cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com
./scripts/deploy.sh
```

## Documentation

- [CI/CD Guide](../docs/CICD.md)
- [API Key Seeding Guide](../docs/api-key-seeding.md)
- [Deployment Checklist](../docs/deployment-checklist.md)
