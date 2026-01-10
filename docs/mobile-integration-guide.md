# Mobile App Integration Guide - JWT Authentication

## Overview

The Safe Drive Africa API now implements JWT (JSON Web Token) authentication for mobile app drivers. This replaces the previous system where API keys were required.

## ⚡ BREAKING CHANGE - Immediate Action Required

**All mobile app data upload endpoints now accept JWT tokens!**

### What Changed

| Old Behavior | New Behavior |
|--------------|--------------|
| ❌ Required `X-API-Key` header (422 error) | ✅ Accepts `Authorization: Bearer <JWT_TOKEN>` |
| ❌ No driver authentication | ✅ Email + password login |
| ❌ Individual API keys per driver | ✅ Single token valid for 30 days |

### Affected Endpoints (ALL DATA UPLOADS)
- ✅ `/api/trips/` - Trip creation
- ✅ `/api/raw_sensor_data/` - Sensor data upload
- ✅ `/api/unsafe_behaviours/` - Unsafe behavior reporting
- ✅ `/api/driving_tips/` - Driving tips
- ✅ `/api/nlg_reports/` - NLG reports
- ✅ `/api/report_statistics/` - Report statistics
- ✅ `/api/questionnaire/` - Alcohol questionnaire
- ✅ All batch upload endpoints

---

## Quick Start - Fix the 422 Error

The error you're seeing:
```
{"detail":[{"type":"missing","loc":["header","X-API-Key"],"msg":"Field required","input":null}]}
```

**Solution:** Add JWT token to ALL requests

### Step 1: Implement Login

### Endpoint
```
POST https://api.safedriveafrica.com/api/auth/driver/register
```

### Request Body
```json
{
  "driverProfileId": "c1042a63-8363-4b96-a492-1f5c53e5975e",
  "email": "driver@example.com",
  "password": "securePassword123",
  "sync": true
}
```

### Response (201 Created)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "driver_profile_id": "c1042a63-8363-4b96-a492-1f5c53e5975e",
  "email": "driver@example.com"
}
```

### Android/Kotlin Implementation
```kotlin
data class RegisterRequest(
    val driverProfileId: String,
    val email: String,
    val password: String,
    val sync: Boolean = true
)

data class TokenResponse(
    val access_token: String,
    val token_type: String,
    val driver_profile_id: String,
    val email: String
)

// Retrofit Interface
interface ApiService {
    @POST("api/auth/driver/register")
    suspend fun register(@Body request: RegisterRequest): TokenResponse
}

// Usage
suspend fun registerDriver(email: String, password: String): TokenResponse {
    val request = RegisterRequest(
        driverProfileId = UUID.randomUUID().toString(),
        email = email,
        password = password,
        sync = true
    )
    
    val response = apiService.register(request)
    
    // Save token securely
    secureStorage.saveToken(response.access_token)
    secureStorage.saveDriverId(response.driver_profile_id)
    
    return response
}
```

### Error Handling
- **400 Bad Request**: Email already registered (show login screen instead)
- **422 Validation Error**: Password too short (minimum 6 characters) or invalid email

---

## 2. Driver Login

### Endpoint
```
POST https://api.safedriveafrica.com/api/auth/driver/login
```

### Request Body
```json
{
  "email": "driver@example.com",
  "password": "securePassword123"
}
```

### Response (200 OK)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "driver_profile_id": "c1042a63-8363-4b96-a492-1f5c53e5975e",
  "email": "driver@example.com"
}
```

### Android/Kotlin Implementation
```kotlin
data class LoginRequest(
    val email: String,
    val password: String
)

// Retrofit Interface
interface ApiService {
    @POST("api/auth/driver/login")
    suspend fun login(@Body request: LoginRequest): TokenResponse
}

// Usage
suspend fun loginDriver(email: String, password: String): TokenResponse {
    val request = LoginRequest(email, password)
    val response = apiService.login(request)
    
    // Save token securely
    secureStorage.saveToken(response.access_token)
    
    return response
}
```

### Error Handling
- **401 Unauthorized**: Invalid email or password

---

## 3. Using JWT Token in API Requests

All subsequent API calls must include the JWT token in the `Authorization` header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### OkHttp Interceptor (Recommended)
```kotlin
class AuthInterceptor(private val secureStorage: SecureStorage) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = secureStorage.getToken()
        
        val request = if (token != null) {
            chain.request().newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
        } else {
            chain.request()
        }
        
        return chain.proceed(request)
    }
}

// Add to OkHttpClient
val client = OkHttpClient.Builder()
    .addInterceptor(AuthInterceptor(secureStorage))
    .build()

val retrofit = Retrofit.Builder()
    .baseUrl("https://api.safedriveafrica.com/")
    .client(client)
    .addConverterFactory(GsonConverterFactory.create())
    .build()
```

### Example API Call with Token
```kotlin
// Retrofit Interface
interface ApiService {
    @POST("api/trips/")
    suspend fun createTrip(
        @Body trip: TripCreate
    ): TripResponse
    // Token automatically added by interceptor
}

// Usage
val trip = TripCreate(
    driverProfileId = driverId,
    start_date = Date(),
    // ... other fields
)

val response = apiService.createTrip(trip)
```

---

## 4. Get Current Driver Profile

### Endpoint
```
GET https://api.safedriveafrica.com/api/auth/driver/me
```

### Headers
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Response (200 OK)
```json
{
  "driverProfileId": "c1042a63-8363-4b96-a492-1f5c53e5975e",
  "email": "driver@example.com",
  "sync": true
}
```

### Android/Kotlin Implementation
```kotlin
// Retrofit Interface
interface ApiService {
    @GET("api/auth/driver/me")
    suspend fun getCurrentDriver(): DriverProfileResponse
}

// Usage
suspend fun loadDriverProfile(): DriverProfileResponse {
    return apiService.getCurrentDriver()
}
```

---

## 5. Token Management

### Token Lifetime
- **Duration**: 30 days
- **Auto-renewal**: Not implemented (user must re-login after expiration)

### Secure Storage

**Android - EncryptedSharedPreferences:**
```kotlin
class SecureStorage(context: Context) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()
    
    private val sharedPreferences = EncryptedSharedPreferences.create(
        context,
        "secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    
    fun saveToken(token: String) {
        sharedPreferences.edit().putString("jwt_token", token).apply()
    }
    
    fun getToken(): String? {
        return sharedPreferences.getString("jwt_token", null)
    }
    
    fun clearToken() {
        sharedPreferences.edit().remove("jwt_token").apply()
    }
}
```

### Logout
```kotlin
fun logout() {
    secureStorage.clearToken()
    // Navigate to login screen
}
```

---

## 6. Migration Guide for Existing Users

For drivers already registered in the system (without passwords):

### Option 1: Require Password Setup
```kotlin
// On first launch after update
if (!hasPassword()) {
    showPasswordSetupScreen()
}

suspend fun setupPassword(email: String, password: String) {
    // Use existing driverProfileId from local storage
    val driverId = localDb.getDriverId()
    
    // Register with existing ID (will update password)
    val request = RegisterRequest(
        driverProfileId = driverId,
        email = email,
        password = password
    )
    
    val response = apiService.register(request)
    secureStorage.saveToken(response.access_token)
}
```

### Option 2: Force Re-registration
```kotlin
// Clear existing data and show registration screen
fun migrateToNewAuth() {
    localDb.clearDriverData()
    showRegistrationScreen()
}
```

---

## 7. Error Handling Best Practices

### 401 Unauthorized (Token Expired/Invalid)
```kotlin
class TokenExpiredInterceptor(
    private val secureStorage: SecureStorage
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val response = chain.proceed(chain.request())
        
        if (response.code == 401) {
            // Token expired or invalid
            secureStorage.clearToken()
            // Trigger navigation to login screen
            eventBus.post(TokenExpiredEvent())
        }
        
        return response
    }
}
```

### Validation Errors (422)
```kotlin
fun handleValidationError(error: ValidationError) {
    when {
        error.message.contains("password") -> 
            showError("Password must be at least 6 characters")
        error.message.contains("email") -> 
            showError("Invalid email format")
        else -> 
            showError("Please check your input")
    }
}
```

---

## 8. Testing

### Test Registration
```bash
curl -X POST https://api.safedriveafrica.com/api/auth/driver/register \
  -H "Content-Type: application/json" \
  -d '{
    "driverProfileId": "550e8400-e29b-41d4-a716-446655440000",
    "email": "test@example.com",
    "password": "test123",
    "sync": true
  }'
```

### Test Login
```bash
curl -X POST https://api.safedriveafrica.com/api/auth/driver/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }'
```

### Test Authenticated Request
```bash
curl https://api.safedriveafrica.com/api/auth/driver/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## 9. Complete Example Flow

```kotlin
class AuthRepository(
    private val apiService: ApiService,
    private val secureStorage: SecureStorage
) {
    
    suspend fun register(email: String, password: String): Result<TokenResponse> {
        return try {
            val request = RegisterRequest(
                driverProfileId = UUID.randomUUID().toString(),
                email = email,
                password = password
            )
            val response = apiService.register(request)
            secureStorage.saveToken(response.access_token)
            Result.success(response)
        } catch (e: HttpException) {
            when (e.code()) {
                400 -> Result.failure(Exception("Email already registered"))
                422 -> Result.failure(Exception("Invalid input"))
                else -> Result.failure(e)
            }
        }
    }
    
    suspend fun login(email: String, password: String): Result<TokenResponse> {
        return try {
            val request = LoginRequest(email, password)
            val response = apiService.login(request)
            secureStorage.saveToken(response.access_token)
            Result.success(response)
        } catch (e: HttpException) {
            when (e.code()) {
                401 -> Result.failure(Exception("Invalid email or password"))
                else -> Result.failure(e)
            }
        }
    }
    
    fun logout() {
        secureStorage.clearToken()
    }
    
    fun isLoggedIn(): Boolean {
        return secureStorage.getToken() != null
    }
}
```

---

## 10. API Endpoints Summary

| Endpoint | Method | Auth Required | Purpose |
|----------|--------|---------------|---------|
| `/api/auth/driver/register` | POST | No | Register new driver |
| `/api/auth/driver/login` | POST | No | Login existing driver |
| `/api/auth/driver/me` | GET | Yes (JWT) | Get current driver profile |
| `/api/trips/` | POST | Yes (JWT) | Create trip (example) |
| All other driver endpoints | * | Yes (JWT) | Require JWT token |

---

## Support

- **API Documentation**: https://api.safedriveafrica.com/docs
- **Base URL**: https://api.safedriveafrica.com
- **Token Lifetime**: 30 days
- **Password Requirements**: Minimum 6 characters

For questions or issues, contact the backend development team.
