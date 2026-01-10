# DataHub Frontend Integration Guide

## Overview

This document outlines the backend API changes and authentication requirements for the Safe Drive Africa DataHub web application.

## What Changed

### Analytics Endpoints - Simplified Access

The following analytics endpoints no longer require `fleetId` or `insurancePartnerId` parameters for admin/researcher roles:

- `GET /api/analytics/driver-kpis`
- `GET /api/analytics/leaderboard`
- `GET /api/analytics/bad-days`

These endpoints will now return data for **all drivers** in the system when no scope is provided.

### Dual Authentication System

The DataHub now supports **two authentication methods**:

1. **API Key Authentication** - For admin, researcher, fleet_manager, insurance_partner
2. **JWT Authentication** - For drivers accessing their dashboard/leaderboard

## Authentication

### For Admin/Researcher/Fleet/Insurance Users

**No changes required.** Continue using your existing admin API key in the `X-API-Key` header.

```http
GET /api/analytics/driver-kpis?period=week
Host: api.safedriveafrica.com
X-API-Key: your-admin-api-key-here
```

### For Driver Users (NEW)

Drivers now log in with **email/password** and receive a JWT token.

```http
GET /api/analytics/driver-kpis?period=week
Host: api.safedriveafrica.com
X-API-Key: your-admin-api-key-here
```

#### Driver Login Flow (NEW)

1. **Login Screen** - Driver enters email/password
2. **API Call** - POST to `/api/auth/driver/login`
3. **Receive Token** - Store JWT token in localStorage/sessionStorage
4. **Use Token** - Include in `Authorization: Bearer <token>` header

**Login Request:**
```javascript
const loginDriver = async (email, password) => {
  const response = await fetch('https://api.safedriveafrica.com/api/auth/driver/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email, password })
  });
  
  if (response.ok) {
    const data = await response.json();
    // Store token
    localStorage.setItem('jwt_token', data.access_token);
    localStorage.setItem('user_type', 'driver');
    localStorage.setItem('driver_id', data.driver_profile_id);
    return data;
  } else if (response.status === 401) {
    throw new Error('Invalid email or password');
  }
  throw new Error('Login failed');
};Implementation Steps

### 1. Add Login Page for Drivers

Create a driver login form:

```jsx
// DriverLogin.jsx
import { useState } from 'react';

function DriverLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await fetch('https://api.safedriveafrica.com/api/auth/driver/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('jwt_token', data.access_token);
        localStorage.setItem('user_type', 'driver');
        localStorage.setItem('driver_id', data.driver_profile_id);
        // Redirect to driver dashboard
        window.location.href = '/driver/dashboard';
      } else if (response.status === 401) {
        setError('Invalid email or password');
      }
    } catch (err) {
      setError('Login failed. Please try again.');
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      {error && <div className="error">{error}</div>}
      <button type="submit">Login</button>
    </form>
  );
}
```

### 2. Create Authentication Utility

```javascript
// auth.js
export const getAuthHeaders = () => {
  const userType = localStorage.getItem('user_type');
  
  if (userType === 'driver') {
    const token = localStorage.getItem('jwt_token');
    return { 'Authorization': `Bearer ${token}` };
  } else {
    const apiKey = localStorage.getItem('api_key');
    return { 'X-API-Key': apiKey };
  }
};

export const isAuthenticated = () => {
  const userType = localStorage.getItem('user_type');
  
  if (userType === 'driver') {
    return !!localStorage.getItem('jwt_token');
  }
  return !!localStorage.getItem('api_key');
};

export const logout = () => {
  localStorage.removeItem('jwt_token');
  locmmary: Two Login Pages

Your DataHub needs **two separate login pages**:

### 1. Admin/Staff Login Page (`/admin-login`)
- Users: admin, researcher, fleet_manager, insurance_partner
- Input: API Key (paste into field)
- Store: `localStorage.setItem('api_key', key)` and `localStorage.setItem('user_type', 'admin')`
- Usage: All requests include `X-API-Key` header

### 2. Driver Login Page (`/login`)
- Users: drivers
- Input: Email + Password
- API: POST `/api/auth/driver/login`
- Store: JWT token + `localStorage.setItem('user_type', 'driver')`
- Usage: All requests include `Authorization: Bearer <token>` header

## Key Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/auth/driver/login` | POST | None | Driver login (returns JWT) |
| `/api/auth/driver/me` | GET | JWT | Get current driver profile |
| `/api/auth/me` | GET | API Key | Get current admin/staff profile |
| `/api/analytics/driver-kpis` | GET | JWT or API Key | Get driver KPIs |
| `/api/analytics/leaderboard` | GET | JWT or API Key | Get leaderboard |
| `/api/analytics/bad-days` | GET | JWT or API Key | Get bad driving days |

## SualStorage.removeItem('api_key');
  localStorage.removeItem('user_type');
  localStorage.removeItem('driver_id');
  window.location.href = '/login';
};

export const getUserType = () => {
  return localStorage.getItem('user_type'); // 'driver' or 'admin'/'researcher'/etc
};
```

### 3. Update API Client

```javascript
// api.js
import { getAuthHeaders } from './auth';

export const fetchAPI = async (endpoint, options = {}) => {
  const headers = {
    'Content-Type': 'application/json',
    ...getAuthHeaders(),
    ...options.headers
  };

  const response = await fetch(`https://api.safedriveafrica.com${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401) {
    // Token expired or invalid
    logout();
    throw new Error('Authentication failed');
  }

  return response;
};

// Usage
export const getDriverKPIs = async (period = 'week') => {
  const response = await fetchAPI(`/api/analytics/driver-kpis?period=${period}`);
  return await response.json();
};

export const getLeaderboard = async (period = 'week') => {
  const response = await fetchAPI(`/api/analytics/leaderboard?period=${period}`);
  return await response.json();
};
```

### 4. Update Routes

```jsx
// App.jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { isAuthenticated, getUserType } from './auth';

function PrivateRoute({ children, allowedTypes }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" />;
  }
  
  const userType = getUserType();
  if (allowedTypes && !allowedTypes.includes(userType)) {
    return <Navigate to="/unauthorized" />;
  }
  
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<DriverLogin />} />
        <Route path="/admin-login" element={<AdminLogin />} />
        
        {/* Driver routes */}
        <Route
          path="/driver/dashboard"
          element={
            <PrivateRoute allowedTypes={['driver']}>
              <DriverDashboard />
            </PrivateRoute>
          }
        />
        <Route
          path="/driver/leaderboard"
          element={
            <PrivateRoute allowedTypes={['driver']}>
              <Leaderboard />
            </PrivateRoute>
          }
        />
        
        {/* Admin routes */}
        <Route
          path="/admin/dashboard"
          element={
            <PrivateRoute allowedTypes={['admin', 'researcher']}>
              <AdminDashboard />
            </PrivateRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
```

### 5. Driver Dashboard Example

```jsx
// DriverDashboard.jsx
import { useEffect, useState } from 'react';
import { getDriverKPIs, getLeaderboard } from './api';

function DriverDashboard() {
  const [kpis, setKpis] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [kpiData, leaderboardData] = await Promise.all([
          getDriverKPIs('week'),
          getLeaderboard('week')
        ]);
        setKpis(kpiData);
        setLeaderboard(leaderboardData);
      } catch (error) {
        console.error('Failed to load data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Driver Dashboard</h1>
      
      <section>
        <h2>Your Stats</h2>
        <div>UBPK Score: {kpis?.ubpk_score}</div>
        <div>Total Trips: {kpis?.total_trips}</div>
        <div>Safe Days: {kpis?.safe_days}</div>
      </section>

      <section>
        <h2>Leaderboard</h2>
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Driver</th>
              <th>UBPK Score</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.map((driver, index) => (
              <tr key={driver.driver_id}>
                <td>{index + 1}</td>
                <td>{driver.driver_name}</td>
                <td>{driver.ubpk_score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
```

## Testing

### Test Admin Authentication (Existing)
```bash
curl -H "X-API-Key: YOUR_ADMIN_KEY" \
  https://api.safedriveafrica.com/api/analytics/driver-kpis?period=week
```

### Test Driver Authentication (NEW)

**1. Login:**
```bash
curl -X POST https://api.safedriveafrica.com/api/auth/driver/login \
  -H "Content-Type: application/json" \
  -d '{"email": "driver@example.com", "password": "password123"}'
```

**2. Use Token:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://api.safedriveafrica.com/api/analytics/driver-kpis?period=week
```

**3. Get Driver Profile:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://api.safedriveafrica.com/api/auth/driver/me
```

## Error Handling

### API Key Users (Admin/Researcher/etc.)
- `401 Unauthorized` - Invalid API key
- `403 Forbidden` - Insufficient permissions
- `400 Bad Request` - Invalid parameters

### JWT Users (Drivers)
- `401 Unauthorized` - Token expired or invalid (redirect to login)
- `422 Validation Error` - Invalid login credential
### Before
```javascript
// Required fleetId or insurancePartnerId
const response = await fetch(
  'https://api.safedriveafrica.com/api/analytics/driver-kpis?period=week&fleetId=xxx',
  {
    headers: {
      'X-API-Key': adminApiKey
    }
  }
);
```

### After
```javascript
// No fleetId/insurancePartnerId needed for admin/researcher
const response = await fetch(
  'https://api.safedriveafrica.com/api/analytics/driver-kpis?period=week',
  {
    headers: {
      'X-API-Key': adminApiKey
    }
  }
);
// Returns data for ALL drivers
```

## Testing

Test the analytics endpoints to ensure they return data for all drivers:

```bash
# Driver KPIs
curl -H "X-API-Key: YOUR_ADMIN_KEY" \
  https://api.safedriveafrica.com/api/analytics/driver-kpis?period=week

# Leaderboard
curl -H "X-API-Key: YOUR_ADMIN_KEY" \
  https://api.safedriveafrica.com/api/analytics/leaderboard?period=week

# Bad Days
curl -H "X-API-Key: YOUR_ADMIN_KEY" \
  https://api.safedriveafrica.com/api/analytics/bad-days
```

## Error Handling

No changes to error handling. Continue handling:
- `401 Unauthorized` - Invalid API key
- `403 Forbidden` - Insufficient permissions
- `400 Bad Request` - Invalid parameters

## Optional: Scope Filtering

You can still provide `fleetId` or `insurancePartnerId` to filter results:

```javascript
// Optional: Filter by fleet
const response = await fetch(
  'https://api.safedriveafrica.com/api/analytics/driver-kpis?period=week&fleetId=xxx',
  {
    headers: {
      'X-API-Key': adminApiKey
    }
  }
);
```

## Support

For issues or questions, contact the backend team or check the API documentation at:
`https://api.safedriveafrica.com/docs`
