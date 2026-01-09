# API Key Seeding Guide

## Quick Start

### Step 1: SSH into Production Server

```bash
ssh your-user@api.safedriveafrica.com
cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com
source venv/bin/activate
```

### Step 2: Run Seeding Script

**Option A: Basic Seeding (Admin & Researcher)**
```bash
python scripts/seed_api_keys.py
```

**Option B: Advanced Seeding (Uses Existing Data)**
This creates API clients for existing fleets, drivers, and insurance partners:
```bash
python scripts/seed_with_existing_data.py
```

### Step 3: Save the Generated Keys

The script will output API keys like this:

```
🔑 API KEYS - SAVE THESE SECURELY!
====================================================================

📋 Admin
   Role: admin
   ID: bb33af69-a843-487c-bc53-5fd3dd22febb
   🔑 API Key: FeZGph0Os2oPHofcpgp0NlYODfdzwDSIErBC_105uVs

📋 Researcher
   Role: researcher
   ID: 9c7323df-0dfd-4929-b769-1da0e8788550
   🔑 API Key: xY9ZpQwErTyUiOpLkJhGfDsAqWeRtYuIoP1234567890
```

**⚠️ IMPORTANT:** Copy these keys immediately! They are hashed in the database and cannot be retrieved later.

### Step 4: Test the Admin Key

```bash
# Test locally on server
curl -H "X-API-Key: YOUR_ADMIN_KEY_HERE" \
     http://localhost:8000/api/auth/me

# Test from outside
curl -H "X-API-Key: YOUR_ADMIN_KEY_HERE" \
     https://api.safedriveafrica.com/api/auth/me
```

Expected response:
```json
{
  "id": "bb33af69-a843-487c-bc53-5fd3dd22febb",
  "name": "Admin",
  "role": "admin",
  "driverProfileId": null,
  "fleet_id": null,
  "insurance_partner_id": null
}
```

---

## Using the Admin Key

Once you have the admin key, you can:

### 1. Create Additional API Clients

```bash
curl -X POST https://api.safedriveafrica.com/api/admin/api-clients/ \
  -H "X-API-Key: YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fleet Manager - Abuja",
    "role": "fleet_manager",
    "active": true,
    "fleet_id": "af1fbd02-6ffd-4917-ae98-58ea1b661efc"
  }'
```

### 2. List All API Clients

```bash
curl -H "X-API-Key: YOUR_ADMIN_KEY" \
     https://api.safedriveafrica.com/api/admin/api-clients/
```

### 3. Create Fleet Assignments

```bash
curl -X POST https://api.safedriveafrica.com/api/fleet/assignments/ \
  -H "X-API-Key: YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "fleet_id": "af1fbd02-6ffd-4917-ae98-58ea1b661efc",
    "driverProfileId": "e1c3446f-ffbc-4b90-b5be-2d8d25869d31",
    "vehicle_group_id": "8bfd2ab4-45ee-4936-aa8d-f6cbca8204e1",
    "active": true
  }'
```

### 4. Create Insurance Partner

```bash
curl -X POST https://api.safedriveafrica.com/api/admin/insurance-partners/ \
  -H "X-API-Key: YOUR_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Insurance Co",
    "label": "new_insurance",
    "active": true
  }'
```

---

## Role-Based Access

| Role | Access Level | Scope |
|------|--------------|-------|
| **admin** | Full access to all endpoints | System-wide |
| **researcher** | Read-only access to research datasets | All drivers |
| **fleet_manager** | Manage fleet, view driver data | Assigned fleet only |
| **driver** | View own trips and reports | Own profile only |
| **insurance_partner** | View insured drivers' data | Assigned drivers only |

---

## Security Best Practices

1. **Store Keys Securely**
   - Use environment variables or secrets management
   - Never commit keys to git
   - Rotate keys periodically

2. **Principle of Least Privilege**
   - Create specific keys for each service/user
   - Use appropriate roles (don't use admin for everything)

3. **Monitor API Usage**
   - Check logs regularly: `sudo journalctl -u safedriveapi-prod -f`
   - Disable inactive clients

4. **Key Rotation**
   - Generate new keys for compromised accounts
   - Disable old keys via admin API

---

## Troubleshooting

### Error: "Invalid or inactive API key"
- Check if key is copied correctly (no extra spaces)
- Verify client is active: `SELECT * FROM api_client WHERE name='Admin';`

### Error: "Unsupported role for this API key"
- Role must be one of: admin, driver, researcher, fleet_manager, insurance_partner
- Check role in database

### Can't run seeding script
```bash
# Make sure you're in the app directory
cd /var/www/vhosts/safedriveafrica.com/api.safedriveafrica.com

# Activate virtual environment
source venv/bin/activate

# Check DATABASE_URL is set
echo $DATABASE_URL

# If not set, load from .env
export $(grep -v '^#' .env | xargs)
```

### Keys not saved to file
The script saves keys to `api_keys_GENERATED.txt` in the current directory. If you don't see it:
```bash
ls -la api_keys_GENERATED.txt
cat api_keys_GENERATED.txt
```

---

## Web Client Integration

For the React frontend, store the API key after login:

```typescript
// Login component
const login = async (apiKey: string) => {
  try {
    const response = await fetch('https://api.safedriveafrica.com/api/auth/me', {
      headers: {
        'X-API-Key': apiKey
      }
    });
    
    if (response.ok) {
      const user = await response.json();
      // Store key and user info
      localStorage.setItem('apiKey', apiKey);
      localStorage.setItem('user', JSON.stringify(user));
      // Redirect based on role
      redirectByRole(user.role);
    }
  } catch (error) {
    console.error('Login failed:', error);
  }
};

// API client
const apiClient = axios.create({
  baseURL: 'https://api.safedriveafrica.com',
  headers: {
    'X-API-Key': localStorage.getItem('apiKey')
  }
});
```

---

## Next Steps

1. Run seeding script to get admin key
2. Test admin key with `/api/auth/me`
3. Use admin key to:
   - Create fleet manager keys for existing fleets
   - Create driver keys for testing
   - Set up insurance partner keys
4. Integrate keys into web client
5. Document key distribution process for your team

---

## Support

For issues:
1. Check logs: `sudo journalctl -u safedriveapi-prod -f`
2. Verify database: `mysql -u dev2 -p drive_safe_db`
3. Re-run seeding if needed (it's idempotent)
4. Check [CICD.md](CICD.md) for deployment issues
