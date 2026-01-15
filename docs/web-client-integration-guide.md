# Web Client Integration Guide
## API Updates for Bad Days Analytics Endpoint

**Target Audience:** Frontend Developers, Web Client Maintainers, AI Agents  
**Date:** January 15, 2026  
**API Version:** v1  
**Difficulty Level:** Intermediate

---

## Table of Contents

1. [Overview](#overview)
2. [What Changed in the API](#what-changed-in-the-api)
3. [API Endpoint Reference](#api-endpoint-reference)
4. [Authentication Setup](#authentication-setup)
5. [CORS Configuration](#cors-configuration)
6. [Response Format](#response-format)
7. [Error Handling](#error-handling)
8. [Performance Considerations](#performance-considerations)
9. [Code Examples](#code-examples)
10. [Testing Guide](#testing-guide)
11. [Migration Checklist](#migration-checklist)
12. [Troubleshooting](#troubleshooting)

---

## Overview

### What This Guide Covers

This guide helps you integrate the newly optimized `/api/analytics/bad-days` endpoint into your web client. The API has been significantly improved:

- **Performance:** 2,088x faster (165s → 79ms cached)
- **Reliability:** No more 504 timeouts
- **Caching:** Responses cached for 5 minutes
- **Pagination:** Default page size reduced to 25 drivers

### Breaking Changes

⚠️ **IMPORTANT:** Review these changes carefully:

1. **Default Page Size Changed:** 50 → 25 drivers per page
2. **Response Time Improved:** First request ~10s, cached <100ms
3. **CORS Origins Updated:** Must use approved origins
4. **API Key Required:** No anonymous access

### Non-Breaking Changes

✅ These work the same way:
- Response structure (no schema changes)
- Authentication methods (API Key or JWT)
- Query parameters (all optional)
- Error response format

---

## What Changed in the API

### Backend Improvements

| Aspect | Before | After | Impact on Frontend |
|--------|--------|-------|-------------------|
| **Response Time** | 60-165 seconds | 10s (uncached)<br>0.079s (cached) | ✅ Faster loading, better UX |
| **Timeout Errors** | Frequent 504s | None | ✅ More reliable |
| **Default Page Size** | 50 drivers | 25 drivers | ⚠️ Check pagination logic |
| **Cache Duration** | None | 5 minutes | ℹ️ Data may be up to 5min old |
| **CORS Origins** | Unrestricted | Whitelist only | ⚠️ Verify your domain is allowed |

### Database Optimizations

These are transparent to the frontend but good to understand:

1. **Indexes Added:** Speeds up queries on `trip.start_time`, `raw_sensor_data.trip_id`, etc.
2. **Query Restructuring:** Pre-aggregates 8.5M sensor records before joining
3. **Redis Caching:** Stores computed results for 5 minutes
4. **UUID Serialization:** Proper JSON conversion for all UUIDs

---

## API Endpoint Reference

### Base URL

```
Production:  https://api.safedriveafrica.com
Development: http://localhost:8000
```

### Endpoint

```http
GET /api/analytics/bad-days
```

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `fleetId` | UUID | No | `null` | Filter by specific fleet (fleet managers auto-filtered) |
| `insurancePartnerId` | UUID | No | `null` | Filter by insurance partner (partners auto-filtered) |
| `page` | Integer | No | `1` | Page number (1-indexed) |
| `pageSize` | Integer | No | `25` | Drivers per page (min: 10, max: 100) |

### Headers

| Header | Required | Format | Example |
|--------|----------|--------|---------|
| `X-API-Key` | Yes* | String | `02QDlql_JlwQXjdcj-Awsw8gBPs06-6JEP-aasDKf38` |
| `Authorization` | Yes* | Bearer token | `Bearer eyJhbGciOiJIUzI1NiIs...` |

*One of `X-API-Key` or `Authorization` is required

### Full Request Example

```http
GET /api/analytics/bad-days?page=1&pageSize=25&fleetId=5564e348-99dc-4921-858e-d06887d33077 HTTP/1.1
Host: api.safedriveafrica.com
X-API-Key: 02QDlql_JlwQXjdcj-Awsw8gBPs06-6JEP-aasDKf38
Origin: https://datahub.safedriveafrica.com
```

---

## Authentication Setup

### Option 1: API Key Authentication (Recommended for Admin Dashboard)

**When to use:** Server-side rendering, admin dashboards, internal tools

**How to obtain API Key:**
1. Contact backend team or check `ADMIN_KEYS.txt` on server
2. Keys are role-specific (admin, researcher, fleet_manager, etc.)
3. Store securely (environment variables, secrets manager)

**Implementation:**

```javascript
// Store API key securely
const API_KEY = process.env.NEXT_PUBLIC_API_KEY; // Next.js
// OR
const API_KEY = import.meta.env.VITE_API_KEY; // Vite
// OR
const API_KEY = process.env.REACT_APP_API_KEY; // Create React App

// Make request
const response = await fetch('https://api.safedriveafrica.com/api/analytics/bad-days', {
  headers: {
    'X-API-Key': API_KEY,
  },
});
```

**Security Notes:**
- ⚠️ Never expose API keys in client-side code (publicly visible)
- ✅ Use environment variables that stay server-side
- ✅ For purely client-side apps, use JWT (Option 2)

### Option 2: JWT Token Authentication (Recommended for Client-Side Apps)

**When to use:** Client-side React/Vue/Angular apps, mobile web views

**How to obtain JWT:**
```javascript
// 1. User logs in
const loginResponse = await fetch('https://api.safedriveafrica.com/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'secure_password',
  }),
});

const { access_token } = await loginResponse.json();

// 2. Store token securely
localStorage.setItem('access_token', access_token); // Simple (less secure)
// OR use secure cookie with httpOnly flag (more secure)

// 3. Use token in requests
const response = await fetch('https://api.safedriveafrica.com/api/analytics/bad-days', {
  headers: {
    'Authorization': `Bearer ${access_token}`,
  },
});
```

**Token Management:**
```javascript
// Check if token is expired
function isTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000 < Date.now();
  } catch {
    return true;
  }
}

// Refresh token if needed
async function getValidToken() {
  const token = localStorage.getItem('access_token');
  
  if (!token || isTokenExpired(token)) {
    // Redirect to login or refresh token
    window.location.href = '/login';
    return null;
  }
  
  return token;
}
```

---

## CORS Configuration

### Allowed Origins

The API accepts requests from these origins only:

```javascript
const ALLOWED_ORIGINS = [
  'https://datahub.safedriveafrica.com',  // Production dashboard
  'https://api.safedriveafrica.com',      // API docs/testing
  'https://www.safedriveafrica.com',      // Main website
  'http://localhost:3000',                 // Local development
];
```

### Common CORS Issues

**Problem 1: Origin Not Allowed**
```
Access to fetch at 'https://api.safedriveafrica.com/api/analytics/bad-days' 
from origin 'https://my-dashboard.com' has been blocked by CORS policy
```

**Solution:**
Contact backend team to add your domain to allowed origins.

**Problem 2: Credentials Not Included**
```
Access to fetch blocked: The value of the 'Access-Control-Allow-Credentials' header 
in the response is '' which must be 'true' when the request's credentials mode is 'include'.
```

**Solution:**
```javascript
// Add credentials: 'include' to fetch
fetch(url, {
  credentials: 'include',
  headers: { 'X-API-Key': API_KEY },
});
```

### Testing CORS Locally

```javascript
// Development: Use proxy to avoid CORS
// next.config.js (Next.js)
module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://api.safedriveafrica.com/api/:path*',
      },
    ];
  },
};

// vite.config.js (Vite)
export default {
  server: {
    proxy: {
      '/api': {
        target: 'https://api.safedriveafrica.com',
        changeOrigin: true,
      },
    },
  },
};
```

---

## Response Format

### Success Response (HTTP 200)

```json
{
  "thresholds": {
    "day": 0.0,
    "week": 0.0,
    "month": 0.0
  },
  "drivers": [
    {
      "driverProfileId": "2d2aad8c-7c1f-4bc9-ae87-ab14854bf503",
      "bad_days": 1,
      "bad_weeks": 0,
      "bad_months": 0,
      "last_day_delta": -0.016673431294923637,
      "last_week_delta": null,
      "last_month_delta": null
    },
    {
      "driverProfileId": "7445b63c-8e2c-4a17-9cf6-1a3f8e9d4c5b",
      "bad_days": 0,
      "bad_weeks": 1,
      "bad_months": 2,
      "last_day_delta": 0.024531,
      "last_week_delta": -0.012345,
      "last_month_delta": 0.008765
    }
  ]
}
```

### Response Schema

#### Root Object
| Field | Type | Description |
|-------|------|-------------|
| `thresholds` | Object | Global thresholds (75th percentile of deltas) |
| `drivers` | Array | List of driver bad-day statistics |

#### Thresholds Object
| Field | Type | Description |
|-------|------|-------------|
| `day` | Float | 75th percentile of daily UBPK increases |
| `week` | Float | 75th percentile of weekly UBPK increases |
| `month` | Float | 75th percentile of monthly UBPK increases |

#### Driver Object
| Field | Type | Description | Can Be Null? |
|-------|------|-------------|--------------|
| `driverProfileId` | String (UUID) | Unique driver identifier | No |
| `bad_days` | Integer | Count of days with UBPK spike | No |
| `bad_weeks` | Integer | Count of weeks with UBPK spike | No |
| `bad_months` | Integer | Count of months with UBPK spike | No |
| `last_day_delta` | Float | Most recent daily UBPK change | Yes (if no data) |
| `last_week_delta` | Float | Most recent weekly UBPK change | Yes (if no data) |
| `last_month_delta` | Float | Most recent monthly UBPK change | Yes (if no data) |

### Pagination

The response is **already paginated**. To get more pages:

```javascript
// Get page 1 (drivers 1-25)
const page1 = await fetch('/api/analytics/bad-days?page=1&pageSize=25');

// Get page 2 (drivers 26-50)
const page2 = await fetch('/api/analytics/bad-days?page=2&pageSize=25');

// Get page 3 (drivers 51-75)
const page3 = await fetch('/api/analytics/bad-days?page=3&pageSize=25');
```

**Note:** The API does **not** return total count or total pages. Keep requesting until you get an empty `drivers` array.

### Understanding the Data

**What is a "Bad Day"?**
A day where the driver's UBPK (Unsafe Behavior Per Kilometer) increased significantly compared to their historical average. The threshold is dynamically calculated as the 75th percentile across all drivers.

**Example Interpretation:**
```json
{
  "driverProfileId": "abc-123",
  "bad_days": 3,
  "last_day_delta": -0.016673
}
```
Means:
- This driver had 3 days where UBPK spiked
- Most recent day: UBPK *improved* by 0.0167 (negative = better)
- This day is NOT counted as a bad day

**Null Values:**
- `null` means no data available for that period
- Could be new driver, no trips, or data collection issue
- Handle gracefully in UI (show "N/A" or hide metric)

---

## Error Handling

### Common Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Authentication required. Provide either X-API-Key or Authorization: Bearer token."
}
```

**Causes:**
- Missing `X-API-Key` or `Authorization` header
- Invalid/expired API key
- Invalid/expired JWT token

**Fix:**
```javascript
// Check if auth headers are present
const headers = new Headers();
if (apiKey) {
  headers.append('X-API-Key', apiKey);
} else if (token) {
  headers.append('Authorization', `Bearer ${token}`);
} else {
  // Redirect to login
  window.location.href = '/login';
  return;
}
```

#### 403 Forbidden
```json
{
  "detail": "You do not have access to this resource."
}
```

**Causes:**
- Role doesn't have permission (e.g., driver trying to access admin analytics)
- Fleet manager trying to access different fleet's data

**Fix:**
Show appropriate error message and redirect to authorized page.

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["query", "page"],
      "msg": "ensure this value is greater than or equal to 1",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

**Causes:**
- Invalid query parameters (e.g., `page=0`, `pageSize=200`)

**Fix:**
```javascript
// Validate parameters before sending
function validateParams(page, pageSize) {
  const errors = [];
  
  if (page < 1) {
    errors.push('Page must be >= 1');
  }
  
  if (pageSize < 10 || pageSize > 100) {
    errors.push('Page size must be between 10 and 100');
  }
  
  return errors;
}
```

#### 504 Gateway Timeout (Should be rare now)
```html
<html>
<head><title>504 Gateway Time-out</title></head>
<body>
<h1>504 Gateway Time-out</h1>
</body>
</html>
```

**Causes:**
- Server overload (very rare after optimization)
- Network issues

**Fix:**
```javascript
// Implement retry logic
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok) return response;
      
      if (response.status === 504 && i < maxRetries - 1) {
        // Wait 2 seconds before retry
        await new Promise(resolve => setTimeout(resolve, 2000));
        continue;
      }
      
      return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
}
```

### Generic Error Handler

```javascript
async function fetchBadDays(page = 1, pageSize = 25) {
  try {
    const response = await fetch(
      `https://api.safedriveafrica.com/api/analytics/bad-days?page=${page}&pageSize=${pageSize}`,
      {
        headers: {
          'X-API-Key': process.env.NEXT_PUBLIC_API_KEY,
        },
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      switch (response.status) {
        case 401:
          throw new Error('Authentication failed. Please log in again.');
        case 403:
          throw new Error('Access denied. You do not have permission.');
        case 422:
          throw new Error('Invalid parameters. Check your input.');
        case 504:
          throw new Error('Request timeout. Please try again.');
        default:
          throw new Error(errorData.detail || 'An error occurred');
      }
    }
    
    return await response.json();
  } catch (error) {
    if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
      throw new Error('Network error. Check your internet connection.');
    }
    throw error;
  }
}
```

---

## Performance Considerations

### Caching Strategy

The API caches responses for **5 minutes**. This means:

**✅ Benefits:**
- Lightning-fast response (~79ms)
- Reduced server load
- Better user experience

**⚠️ Considerations:**
- Data may be up to 5 minutes stale
- Multiple users see same cached data
- Changes take up to 5 minutes to appear

### Client-Side Caching

**Don't cache on client side** (or use very short TTL):

```javascript
// ❌ BAD: Cache for 1 hour client-side + 5 min server-side = 65 min stale data
const cachedData = localStorage.getItem('bad_days');
if (cachedData && Date.now() - cachedData.timestamp < 3600000) {
  return JSON.parse(cachedData.data);
}

// ✅ GOOD: Let server handle caching
const response = await fetch('/api/analytics/bad-days');
return await response.json();
```

**Exception:** You can cache for the **duration of a user session**:
```javascript
// Cache in memory (cleared on page refresh)
const sessionCache = new Map();

function getCachedOrFetch(url) {
  if (sessionCache.has(url)) {
    return Promise.resolve(sessionCache.get(url));
  }
  
  return fetch(url)
    .then(r => r.json())
    .then(data => {
      sessionCache.set(url, data);
      return data;
    });
}
```

### Loading States

**First Request (Cache Miss):**
- Show loading spinner for up to 10-12 seconds
- Display "Computing analytics..." message
- Don't timeout too early

**Subsequent Requests (Cache Hit):**
- Data loads almost instantly (<100ms)
- Minimal loading state needed

**Implementation:**
```javascript
function BadDaysComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      const start = Date.now();
      
      try {
        const result = await fetchBadDays(1, 25);
        setData(result);
        
        const elapsed = Date.now() - start;
        if (elapsed > 1000) {
          // Slow response = cache miss
          setIsFirstLoad(false); // Subsequent loads will be fast
        }
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }
    
    loadData();
  }, []);
  
  if (loading) {
    return (
      <div>
        <Spinner />
        <p>
          {isFirstLoad 
            ? "Computing analytics (this may take 10-15 seconds)..." 
            : "Loading cached data..."}
        </p>
      </div>
    );
  }
  
  return <BadDaysTable data={data} />;
}
```

### Optimistic Updates

When user actions might affect bad-days data:

```javascript
// User updates trip data
async function updateTrip(tripId, updates) {
  // 1. Optimistic update (instant feedback)
  setBadDaysData(optimisticallyUpdatedData);
  
  // 2. Send update to server
  await fetch(`/api/trips/${tripId}`, {
    method: 'PATCH',
    body: JSON.stringify(updates),
  });
  
  // 3. Invalidate cache (tell server to recompute)
  // Note: API doesn't have invalidation endpoint yet
  // Workaround: Just wait 5 minutes or refresh manually
  
  // 4. Show message to user
  showToast('Changes saved. Analytics will update in a few minutes.');
}
```

### Pagination Performance

```javascript
// ✅ GOOD: Load pages on demand
function BadDaysList() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState([]);
  
  const loadMore = async () => {
    const newPage = await fetchBadDays(page + 1, 25);
    setData([...data, ...newPage.drivers]);
    setPage(page + 1);
  };
  
  return (
    <>
      <Table data={data} />
      <button onClick={loadMore}>Load More</button>
    </>
  );
}

// ❌ BAD: Load all pages upfront
async function loadAllDrivers() {
  const allDrivers = [];
  let page = 1;
  
  while (true) {
    const response = await fetchBadDays(page, 25);
    if (response.drivers.length === 0) break;
    allDrivers.push(...response.drivers);
    page++;
  }
  
  return allDrivers; // Could be thousands of drivers!
}
```

---

## Code Examples

### React Example (Functional Component)

```jsx
import React, { useState, useEffect } from 'react';

const API_BASE = 'https://api.safedriveafrica.com';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

function BadDaysAnalytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  useEffect(() => {
    fetchData();
  }, [page, pageSize]);

  async function fetchData() {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/analytics/bad-days?page=${page}&pageSize=${pageSize}`,
        {
          headers: {
            'X-API-Key': API_KEY,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
      console.error('Failed to fetch bad days:', err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>Loading analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error">
        <p>Error: {error}</p>
        <button onClick={fetchData}>Retry</button>
      </div>
    );
  }

  if (!data) {
    return <div>No data available</div>;
  }

  return (
    <div className="bad-days-analytics">
      <h2>Bad Days Analytics</h2>
      
      <div className="thresholds">
        <h3>Thresholds (75th Percentile)</h3>
        <ul>
          <li>Day: {data.thresholds.day.toFixed(4)}</li>
          <li>Week: {data.thresholds.week.toFixed(4)}</li>
          <li>Month: {data.thresholds.month.toFixed(4)}</li>
        </ul>
      </div>

      <table className="drivers-table">
        <thead>
          <tr>
            <th>Driver ID</th>
            <th>Bad Days</th>
            <th>Bad Weeks</th>
            <th>Bad Months</th>
            <th>Last Day Δ</th>
          </tr>
        </thead>
        <tbody>
          {data.drivers.map((driver) => (
            <tr key={driver.driverProfileId}>
              <td>{driver.driverProfileId.substring(0, 8)}...</td>
              <td>{driver.bad_days}</td>
              <td>{driver.bad_weeks}</td>
              <td>{driver.bad_months}</td>
              <td>
                {driver.last_day_delta !== null
                  ? driver.last_day_delta.toFixed(4)
                  : 'N/A'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button 
          onClick={() => setPage(p => Math.max(1, p - 1))}
          disabled={page === 1}
        >
          Previous
        </button>
        <span>Page {page}</span>
        <button 
          onClick={() => setPage(p => p + 1)}
          disabled={data.drivers.length < pageSize}
        >
          Next
        </button>
      </div>
    </div>
  );
}

export default BadDaysAnalytics;
```

### Vue 3 Example (Composition API)

```vue
<template>
  <div class="bad-days-analytics">
    <h2>Bad Days Analytics</h2>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading analytics...</p>
    </div>

    <div v-else-if="error" class="error">
      <p>Error: {{ error }}</p>
      <button @click="fetchData">Retry</button>
    </div>

    <div v-else-if="data">
      <div class="thresholds">
        <h3>Thresholds (75th Percentile)</h3>
        <ul>
          <li>Day: {{ data.thresholds.day.toFixed(4) }}</li>
          <li>Week: {{ data.thresholds.week.toFixed(4) }}</li>
          <li>Month: {{ data.thresholds.month.toFixed(4) }}</li>
        </ul>
      </div>

      <table class="drivers-table">
        <thead>
          <tr>
            <th>Driver ID</th>
            <th>Bad Days</th>
            <th>Bad Weeks</th>
            <th>Bad Months</th>
            <th>Last Day Δ</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="driver in data.drivers" :key="driver.driverProfileId">
            <td>{{ driver.driverProfileId.substring(0, 8) }}...</td>
            <td>{{ driver.bad_days }}</td>
            <td>{{ driver.bad_weeks }}</td>
            <td>{{ driver.bad_months }}</td>
            <td>
              {{ driver.last_day_delta !== null 
                ? driver.last_day_delta.toFixed(4) 
                : 'N/A' 
              }}
            </td>
          </tr>
        </tbody>
      </table>

      <div class="pagination">
        <button @click="prevPage" :disabled="page === 1">
          Previous
        </button>
        <span>Page {{ page }}</span>
        <button @click="nextPage" :disabled="data.drivers.length < pageSize">
          Next
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';

const API_BASE = 'https://api.safedriveafrica.com';
const API_KEY = import.meta.env.VITE_API_KEY;

const data = ref(null);
const loading = ref(false);
const error = ref(null);
const page = ref(1);
const pageSize = ref(25);

async function fetchData() {
  loading.value = true;
  error.value = null;

  try {
    const response = await fetch(
      `${API_BASE}/api/analytics/bad-days?page=${page.value}&pageSize=${pageSize.value}`,
      {
        headers: {
          'X-API-Key': API_KEY,
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }

    data.value = await response.json();
  } catch (err) {
    error.value = err.message;
    console.error('Failed to fetch bad days:', err);
  } finally {
    loading.value = false;
  }
}

function prevPage() {
  if (page.value > 1) {
    page.value--;
  }
}

function nextPage() {
  page.value++;
}

onMounted(() => {
  fetchData();
});

watch([page, pageSize], () => {
  fetchData();
});
</script>
```

### TypeScript Type Definitions

```typescript
// types/analytics.ts

export interface BadDaysResponse {
  thresholds: BadDaysThresholds;
  drivers: DriverBadDays[];
}

export interface BadDaysThresholds {
  day: number;
  week: number;
  month: number;
}

export interface DriverBadDays {
  driverProfileId: string; // UUID
  bad_days: number;
  bad_weeks: number;
  bad_months: number;
  last_day_delta: number | null;
  last_week_delta: number | null;
  last_month_delta: number | null;
}

export interface ApiError {
  detail: string | ValidationError[];
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}
```

```typescript
// services/analyticsApi.ts

import type { BadDaysResponse } from '../types/analytics';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api.safedriveafrica.com';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

export class AnalyticsApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'AnalyticsApiError';
  }
}

export async function fetchBadDays(
  page: number = 1,
  pageSize: number = 25,
  fleetId?: string,
  insurancePartnerId?: string
): Promise<BadDaysResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    pageSize: pageSize.toString(),
  });

  if (fleetId) params.append('fleetId', fleetId);
  if (insurancePartnerId) params.append('insurancePartnerId', insurancePartnerId);

  const url = `${API_BASE}/api/analytics/bad-days?${params}`;

  const response = await fetch(url, {
    headers: {
      'X-API-Key': API_KEY || '',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new AnalyticsApiError(
      errorData.detail || 'Failed to fetch bad days analytics',
      response.status,
      errorData
    );
  }

  return response.json();
}
```

### Vanilla JavaScript Example

```html
<!DOCTYPE html>
<html>
<head>
  <title>Bad Days Analytics</title>
  <style>
    .loading { text-align: center; padding: 20px; }
    .error { color: red; padding: 20px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
  </style>
</head>
<body>
  <div id="app">
    <h2>Bad Days Analytics</h2>
    <div id="content"></div>
    <div id="pagination"></div>
  </div>

  <script>
    const API_BASE = 'https://api.safedriveafrica.com';
    const API_KEY = 'YOUR_API_KEY_HERE';
    
    let currentPage = 1;
    const pageSize = 25;

    async function fetchBadDays(page) {
      const contentDiv = document.getElementById('content');
      contentDiv.innerHTML = '<div class="loading">Loading...</div>';

      try {
        const response = await fetch(
          `${API_BASE}/api/analytics/bad-days?page=${page}&pageSize=${pageSize}`,
          {
            headers: {
              'X-API-Key': API_KEY,
            },
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        renderData(data);
        renderPagination(data);
      } catch (error) {
        contentDiv.innerHTML = `
          <div class="error">
            <p>Error: ${error.message}</p>
            <button onclick="fetchBadDays(${page})">Retry</button>
          </div>
        `;
      }
    }

    function renderData(data) {
      const html = `
        <div class="thresholds">
          <h3>Thresholds</h3>
          <p>Day: ${data.thresholds.day.toFixed(4)}</p>
          <p>Week: ${data.thresholds.week.toFixed(4)}</p>
          <p>Month: ${data.thresholds.month.toFixed(4)}</p>
        </div>

        <table>
          <thead>
            <tr>
              <th>Driver ID</th>
              <th>Bad Days</th>
              <th>Bad Weeks</th>
              <th>Bad Months</th>
              <th>Last Day Δ</th>
            </tr>
          </thead>
          <tbody>
            ${data.drivers.map(driver => `
              <tr>
                <td>${driver.driverProfileId.substring(0, 8)}...</td>
                <td>${driver.bad_days}</td>
                <td>${driver.bad_weeks}</td>
                <td>${driver.bad_months}</td>
                <td>${driver.last_day_delta !== null ? driver.last_day_delta.toFixed(4) : 'N/A'}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
      
      document.getElementById('content').innerHTML = html;
    }

    function renderPagination(data) {
      const hasMore = data.drivers.length === pageSize;
      const html = `
        <button onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
          Previous
        </button>
        <span>Page ${currentPage}</span>
        <button onclick="goToPage(${currentPage + 1})" ${!hasMore ? 'disabled' : ''}>
          Next
        </button>
      `;
      
      document.getElementById('pagination').innerHTML = html;
    }

    function goToPage(page) {
      if (page < 1) return;
      currentPage = page;
      fetchBadDays(page);
    }

    // Load initial data
    fetchBadDays(1);
  </script>
</body>
</html>
```

---

## Testing Guide

### Manual Testing Checklist

- [ ] **Authentication works**
  - [ ] API Key in header
  - [ ] JWT token in header
  - [ ] Error message when missing auth
  
- [ ] **Pagination works**
  - [ ] Page 1 loads
  - [ ] Page 2 loads
  - [ ] Empty page returns empty drivers array
  - [ ] Invalid page number (0, -1) shows error
  
- [ ] **Filtering works** (if using)
  - [ ] Fleet ID filter
  - [ ] Insurance Partner ID filter
  - [ ] Both filters together
  
- [ ] **Error handling**
  - [ ] 401 error handled gracefully
  - [ ] 403 error handled gracefully
  - [ ] Network error handled
  - [ ] Timeout handled (rare)
  
- [ ] **Loading states**
  - [ ] Spinner shows during load
  - [ ] Slow first request (~10s)
  - [ ] Fast cached request (<1s)
  
- [ ] **Data display**
  - [ ] All columns show correct data
  - [ ] Null values show as "N/A"
  - [ ] UUIDs render correctly
  - [ ] Numbers formatted properly

### Automated Testing

```javascript
// tests/analytics.test.js

import { describe, it, expect, vi } from 'vitest';
import { fetchBadDays } from '../services/analyticsApi';

describe('Bad Days Analytics', () => {
  it('fetches data successfully', async () => {
    const mockData = {
      thresholds: { day: 0.0, week: 0.0, month: 0.0 },
      drivers: [
        {
          driverProfileId: 'abc-123',
          bad_days: 1,
          bad_weeks: 0,
          bad_months: 0,
          last_day_delta: -0.016,
          last_week_delta: null,
          last_month_delta: null,
        },
      ],
    };

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockData),
      })
    );

    const result = await fetchBadDays(1, 25);
    
    expect(result).toEqual(mockData);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/analytics/bad-days?page=1&pageSize=25'),
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-API-Key': expect.any(String),
        }),
      })
    );
  });

  it('handles 401 error', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ detail: 'Authentication required' }),
      })
    );

    await expect(fetchBadDays(1, 25)).rejects.toThrow('Authentication required');
  });

  it('handles network error', async () => {
    global.fetch = vi.fn(() => Promise.reject(new Error('Network error')));

    await expect(fetchBadDays(1, 25)).rejects.toThrow('Network error');
  });
});
```

### Performance Testing

```javascript
// Test cache performance
async function testCachePerformance() {
  console.log('Testing cache performance...');
  
  // First request (cache miss)
  const start1 = performance.now();
  await fetchBadDays(1, 25);
  const time1 = performance.now() - start1;
  console.log(`First request: ${time1.toFixed(0)}ms`);
  
  // Second request (cache hit)
  const start2 = performance.now();
  await fetchBadDays(1, 25);
  const time2 = performance.now() - start2;
  console.log(`Second request: ${time2.toFixed(0)}ms`);
  
  // Verify cache is working
  if (time2 < time1 * 0.1) {
    console.log('✅ Cache is working! 10x+ faster');
  } else {
    console.log('⚠️ Cache might not be working');
  }
}
```

---

## Migration Checklist

### Pre-Migration

- [ ] Review this entire document
- [ ] Verify your domain is in allowed CORS origins
- [ ] Obtain valid API key or set up JWT authentication
- [ ] Test API endpoint with curl/Postman
- [ ] Set up environment variables for API key

### Code Changes

- [ ] Update API endpoint URL if changed
- [ ] Add/update authentication headers
- [ ] Update default page size from 50 to 25 (if hardcoded)
- [ ] Handle new cache timing (10s first, <100ms cached)
- [ ] Add error handling for new error types
- [ ] Update loading messages for longer initial load

### Testing

- [ ] Test authentication (API key and/or JWT)
- [ ] Test pagination (pages 1, 2, 3, etc.)
- [ ] Test CORS (from production domain)
- [ ] Test error handling (remove auth, invalid params)
- [ ] Test loading states (spinner shows correctly)
- [ ] Test data display (all fields render)
- [ ] Performance test (cache hit rate)

### Deployment

- [ ] Set production API key in environment
- [ ] Configure production CORS origins
- [ ] Deploy to staging first
- [ ] Verify on staging environment
- [ ] Deploy to production
- [ ] Monitor for errors in first 24 hours

### Post-Deployment

- [ ] Verify analytics page loads correctly
- [ ] Check browser console for errors
- [ ] Monitor API response times
- [ ] Collect user feedback
- [ ] Document any issues found

---

## Troubleshooting

### Issue: "Failed to fetch" in browser console

**Diagnosis:**
Open browser DevTools → Network tab → Look for the request

**Possible Causes:**

1. **CORS error:**
   ```
   Access to fetch at 'https://api.safedriveafrica.com/api/analytics/bad-days' 
   from origin 'https://your-site.com' has been blocked by CORS policy
   ```
   
   **Fix:** Contact backend team to add your domain to allowed origins.

2. **Wrong URL:**
   ```
   GET https://api.safedriveafrica.com/api/analytics/bad-days 404 Not Found
   ```
   
   **Fix:** Check API base URL and endpoint path.

3. **Network error:**
   ```
   TypeError: Failed to fetch
   ```
   
   **Fix:** Check internet connection, DNS, firewall.

### Issue: 401 Authentication Error

**Diagnosis:**
Check request headers in Network tab

**Possible Causes:**

1. **Missing header:**
   ```javascript
   // ❌ Wrong - no auth header
   fetch('/api/analytics/bad-days');
   
   // ✅ Correct
   fetch('/api/analytics/bad-days', {
     headers: { 'X-API-Key': API_KEY },
   });
   ```

2. **Wrong header name:**
   ```javascript
   // ❌ Wrong
   headers: { 'API-Key': API_KEY }
   
   // ✅ Correct
   headers: { 'X-API-Key': API_KEY }
   ```

3. **Invalid API key:**
   - Check environment variable is set
   - Verify key matches server-side keys
   - Check for extra spaces or newlines

### Issue: Data is stale/outdated

**Diagnosis:**
Data doesn't reflect recent changes

**Cause:**
API caches responses for 5 minutes

**Solutions:**

1. **Wait 5 minutes** for cache to expire
2. **Force refresh:** Add cache-busting parameter
   ```javascript
   fetch(`/api/analytics/bad-days?page=1&_t=${Date.now()}`);
   // Note: This creates new cache entries, use sparingly
   ```
3. **Accept eventual consistency:** Show message like "Data updates every 5 minutes"

### Issue: Pagination not working

**Diagnosis:**
Next page doesn't load or shows same data

**Possible Causes:**

1. **Cache key collision:**
   ```javascript
   // ❌ Wrong - page not included in URL
   fetch('/api/analytics/bad-days?pageSize=25');
   
   // ✅ Correct
   fetch(`/api/analytics/bad-days?page=${page}&pageSize=25`);
   ```

2. **No more data:**
   ```javascript
   // Check if response has fewer drivers than page size
   if (response.drivers.length < pageSize) {
     // This is the last page
     disableNextButton();
   }
   ```

### Issue: Slow initial load

**Diagnosis:**
First request takes 10-15 seconds

**Explanation:**
This is **expected behavior**:
- First request computes analytics (cache miss)
- Database aggregates 8.5M sensor records
- Result is cached for 5 minutes
- Subsequent requests are instant (<100ms)

**Solutions:**

1. **Show appropriate loading message:**
   ```javascript
   "Computing analytics for all drivers... This may take 10-15 seconds."
   ```

2. **Implement progress indication:**
   ```javascript
   const [progress, setProgress] = useState(0);
   
   // Fake progress bar (aesthetic only)
   const interval = setInterval(() => {
     setProgress(p => Math.min(p + 1, 95));
   }, 150); // 10s total
   
   // Clear when done
   clearInterval(interval);
   setProgress(100);
   ```

3. **Pre-warm cache (advanced):**
   ```javascript
   // In background job or cron
   fetch('/api/analytics/bad-days?page=1&pageSize=25');
   // Cache is now warm for next user
   ```

### Issue: TypeScript type errors

**Diagnosis:**
TS complaining about null values

**Cause:**
Delta fields can be `null`

**Fix:**
```typescript
// ❌ Wrong - assumes always number
const delta: number = driver.last_day_delta;
delta.toFixed(4); // Error if null

// ✅ Correct - handle null
const delta: number | null = driver.last_day_delta;
const formatted = delta !== null ? delta.toFixed(4) : 'N/A';
```

---

## Additional Resources

### API Documentation
- Full API docs: `https://api.safedriveafrica.com/docs`
- OpenAPI spec: `https://api.safedriveafrica.com/openapi.json`

### Backend Documentation
- Performance optimization guide: `docs/database-performance-optimization-guide.md`
- Frontend integration: `docs/frontend-integration-guide.md`
- Mobile integration: `docs/mobile-integration-guide.md`

### Support Contacts
- Backend Team: [backend-team@safedriveafrica.com]
- API Issues: [Create GitHub issue]
- Urgent Issues: [Slack #api-support]

### Related Endpoints

Other analytics endpoints you might need:

- `GET /api/analytics/leaderboard` - Driver rankings by UBPK
- `GET /api/analytics/driver-ubpk` - Time-series UBPK for one driver
- `GET /api/analytics/driver-kpis` - Overall KPIs for one driver

---

## Changelog

### Version 1.0 (January 15, 2026)
- Initial documentation
- API endpoint: `/api/analytics/bad-days`
- Performance: 2,088x improvement with caching
- Default page size: 25 (changed from 50)
- Cache duration: 5 minutes

---

**Document Version:** 1.0  
**Last Updated:** January 15, 2026  
**Next Review:** February 15, 2026  
**Maintainer:** Safe Drive Africa Development Team

---

*For updates or corrections to this document, please submit a pull request or contact the backend team.*
