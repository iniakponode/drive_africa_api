# Web Client JWT Authentication Fix

## Problem

The web client at `datahub.safedriveafrica.com` shows "Access denied - Your API key does not have access to this view" when drivers try to log in. This is because the web client is still configured to use API keys, but drivers now authenticate with JWT tokens.

## Solution Overview

Update the web client to support **both** authentication methods:
- **JWT tokens** for drivers (mobile users logging into web)
- **API keys** for admin/researcher/fleet manager users

---

## Required Changes

### 1. Update API Client Configuration

**File:** `src/services/api.js` (or similar)

**Find the axios/fetch configuration:**
```javascript
// OLD CODE - Remove this
const apiClient = axios.create({
  baseURL: 'https://api.safedriveafrica.com',
  headers: {
    'X-API-Key': localStorage.getItem('api_key'),
  }
});
```

**Replace with:**
```javascript
// NEW CODE - Support both auth methods
const apiClient = axios.create({
  baseURL: 'https://api.safedriveafrica.com',
});

// Add request interceptor to include auth headers
apiClient.interceptors.request.use((config) => {
  const jwtToken = localStorage.getItem('jwt_token');
  const apiKey = localStorage.getItem('api_key');
  
  // Prefer JWT token if available (for drivers)
  if (jwtToken) {
    config.headers['Authorization'] = `Bearer ${jwtToken}`;
  } 
  // Fall back to API key (for admin/researchers)
  else if (apiKey) {
    config.headers['X-API-Key'] = apiKey;
  }
  
  return config;
}, (error) => {
  return Promise.reject(error);
});
```

---

### 2. Update Driver Login Handler

**File:** `src/pages/DriverLogin.jsx` (or wherever driver login is handled)

**After successful driver login API call:**

```javascript
// When calling POST /api/auth/driver/login
const handleDriverLogin = async (email, password) => {
  try {
    const response = await axios.post(
      'https://api.safedriveafrica.com/api/auth/driver/login',
      { email, password }
    );
    
    // Store JWT token and driver info
    localStorage.setItem('jwt_token', response.data.access_token);
    localStorage.setItem('driver_id', response.data.driver_profile_id);
    localStorage.setItem('user_role', 'driver');
    localStorage.setItem('user_email', response.data.email);
    
    // Remove any old API key (drivers don't use API keys)
    localStorage.removeItem('api_key');
    
    // Redirect to dashboard
    navigate('/dashboard');
  } catch (error) {
    console.error('Login failed:', error);
    setError('Invalid email or password');
  }
};
```

---

### 3. Update Admin/Researcher Login Handler

**File:** `src/pages/AdminLogin.jsx` (or similar)

**Keep existing API key login for non-drivers:**

```javascript
const handleAdminLogin = async (apiKey) => {
  try {
    // Verify API key works
    const response = await axios.get(
      'https://api.safedriveafrica.com/api/auth/me',
      {
        headers: { 'X-API-Key': apiKey }
      }
    );
    
    // Store API key and user info
    localStorage.setItem('api_key', apiKey);
    localStorage.setItem('user_role', response.data.role);
    localStorage.setItem('user_email', response.data.name);
    
    // Remove any old JWT token
    localStorage.removeItem('jwt_token');
    
    navigate('/dashboard');
  } catch (error) {
    setError('Invalid API key');
  }
};
```

---

### 4. Update Authentication Check

**File:** `src/utils/auth.js` or `src/contexts/AuthContext.jsx`

**Replace:**
```javascript
// OLD
export const isAuthenticated = () => {
  return !!localStorage.getItem('api_key');
};
```

**With:**
```javascript
// NEW - Check for either auth method
export const isAuthenticated = () => {
  const jwtToken = localStorage.getItem('jwt_token');
  const apiKey = localStorage.getItem('api_key');
  return !!(jwtToken || apiKey);
};

export const getUserRole = () => {
  return localStorage.getItem('user_role');
};

export const isDriver = () => {
  return getUserRole() === 'driver';
};

export const logout = () => {
  localStorage.removeItem('jwt_token');
  localStorage.removeItem('api_key');
  localStorage.removeItem('user_role');
  localStorage.removeItem('user_email');
  localStorage.removeItem('driver_id');
};
```

---

### 5. Update Protected Routes

**File:** `src/components/ProtectedRoute.jsx` or routing config

```javascript
import { Navigate } from 'react-router-dom';
import { isAuthenticated, getUserRole } from '../utils/auth';

const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  
  const userRole = getUserRole();
  
  // Check if user's role is allowed to access this route
  if (allowedRoles.length > 0 && !allowedRoles.includes(userRole)) {
    return <Navigate to="/unauthorized" replace />;
  }
  
  return children;
};

// Usage example
<Route 
  path="/analytics" 
  element={
    <ProtectedRoute allowedRoles={['admin', 'researcher', 'driver']}>
      <AnalyticsPage />
    </ProtectedRoute>
  } 
/>
```

---

### 6. Handle JWT Token Expiration

**Add response interceptor to handle 401 errors:**

```javascript
// In your API client file
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // JWT token expired or invalid
      localStorage.removeItem('jwt_token');
      localStorage.removeItem('api_key');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

---

## Login Flow Examples

### Driver Login Flow
```
1. Driver visits datahub.safedriveafrica.com/driver-login
2. Enters email + password
3. Frontend calls: POST /api/auth/driver/login
4. Backend returns: { access_token, driver_profile_id, email }
5. Frontend stores JWT token in localStorage
6. All subsequent API calls include: Authorization: Bearer <token>
7. Driver sees their data (trips, analytics, etc.)
```

### Admin/Researcher Login Flow
```
1. Admin visits datahub.safedriveafrica.com/admin-login
2. Enters API key
3. Frontend calls: GET /api/auth/me with X-API-Key header
4. Backend returns: { role, name, ... }
5. Frontend stores API key in localStorage
6. All subsequent API calls include: X-API-Key: <key>
7. Admin sees all data based on their role
```

---

## Testing Checklist

After implementing changes:

- [ ] Driver can log in with email/password
- [ ] Driver can view their dashboard
- [ ] Driver can access analytics endpoints
- [ ] Driver sees "unauthorized" on admin-only pages
- [ ] Admin can still log in with API key
- [ ] Admin/researcher can access all allowed endpoints
- [ ] Logout works for both auth methods
- [ ] Page refresh doesn't log users out
- [ ] 401 errors redirect to login page

---

## API Endpoints Reference

### Driver Authentication
- **POST** `/api/auth/driver/register` - Register new driver
- **POST** `/api/auth/driver/login` - Login (returns JWT)
- **GET** `/api/auth/me` - Get current user info (works with JWT or API key)

### API Key Authentication
- **GET** `/api/auth/me` - Get current user info (with X-API-Key header)

### Protected Endpoints (Accept JWT or API Key)
- **GET** `/api/analytics/leaderboard`
- **GET** `/api/analytics/driver-ubpk`
- **GET** `/api/analytics/bad-days`
- **GET** `/api/analytics/driver-kpis`
- **GET** `/api/trips/`
- **POST** `/api/trips/`
- And all other driver-accessible endpoints

---

## Common Issues & Solutions

### Issue: "Access denied - Your API key does not have access"
**Cause:** Web client is sending X-API-Key header but driver has JWT token  
**Fix:** Update API client to send Authorization header with JWT

### Issue: 401 Unauthorized after login
**Cause:** JWT token not being included in requests  
**Fix:** Check axios/fetch interceptor is configured correctly

### Issue: Driver can't see any data
**Cause:** Missing role-based access control in frontend  
**Fix:** Implement role checks in protected routes

---

## Additional Notes

- JWT tokens expire after 30 days (configured in backend)
- API keys don't expire unless manually revoked
- Both auth methods work on the same endpoints
- The backend was updated to support both methods simultaneously
- No breaking changes for existing admin/researcher users

---

## Support

If you encounter issues:
1. Check browser console for error messages
2. Check network tab to see what headers are being sent
3. Verify localStorage contains either `jwt_token` or `api_key`
4. Check backend logs: `journalctl -u safedriveapi-prod -f`

---

## Backend API Documentation

Full API documentation available at:
- Swagger UI: https://api.safedriveafrica.com/docs
- ReDoc: https://api.safedriveafrica.com/redoc
