# 🚨 URGENT: Mobile App Authentication Fix

## The Problem

Your mobile app is getting this error:
```
Error 422: {"detail":[{"type":"missing","loc":["header","X-API-Key"],"msg":"Field required"}]}
```

## The Solution

**ALL data upload endpoints now require JWT authentication instead of API keys.**

---

## What You Need to Do

### 1. Add Login Screen (if not already done)

```kotlin
// Login API call
data class LoginRequest(val email: String, val password: String)
data class TokenResponse(
    val access_token: String,
    val token_type: String,
    val driver_profile_id: String,
    val email: String
)

interface ApiService {
    @POST("api/auth/driver/login")
    suspend fun login(@Body request: LoginRequest): TokenResponse
}
```

### 2. Store the JWT Token Securely

```kotlin
// After successful login
val response = apiService.login(LoginRequest(email, password))
secureStorage.saveToken(response.access_token)
```

### 3. Add Token to ALL Requests

**CRITICAL: Use an OkHttp Interceptor**

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

// Configure Retrofit
val okHttpClient = OkHttpClient.Builder()
    .addInterceptor(AuthInterceptor(secureStorage))
    .build()

val retrofit = Retrofit.Builder()
    .baseUrl("https://api.safedriveafrica.com/")
    .client(okHttpClient)
    .addConverterFactory(GsonConverterFactory.create())
    .build()
```

---

## Affected Endpoints (REQUIRES JWT)

All of these now require `Authorization: Bearer <token>` header:

- ✅ POST `/api/trips/` - Trip upload
- ✅ POST `/api/raw_sensor_data/` - Sensor data
- ✅ POST `/api/unsafe_behaviours/` - Unsafe behaviors
- ✅ POST `/api/driving_tips/` - Driving tips  
- ✅ POST `/api/nlg_reports/` - NLG reports
- ✅ POST `/api/report_statistics/` - Report statistics
- ✅ POST `/api/questionnaire/` - Alcohol questionnaire
- ✅ All `/batch_create` endpoints

## Driver Registration (No Auth Required)

Registration is still public - no token needed:

```kotlin
data class RegisterRequest(
    val driverProfileId: String,
    val email: String,
    val password: String,
    val sync: Boolean = true
)

@POST("api/auth/driver/register")
suspend fun register(@Body request: RegisterRequest): TokenResponse
```

After registration, you get a token immediately - store it and use it for all future requests.

---

## Testing Your Fix

### 1. Test Login
```bash
curl -X POST https://api.safedriveafrica.com/api/auth/driver/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### 2. Test Upload with Token
```bash
# Replace YOUR_TOKEN with actual JWT
curl -X POST https://api.safedriveafrica.com/api/trips/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"driverProfileId":"...","start_time":"2026-01-10T10:00:00"}'
```

---

## Secure Token Storage

**Android (EncryptedSharedPreferences)**

```kotlin
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

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

---

## Token Expiry Handling

Tokens expire after **30 days**. Handle 401 errors:

```kotlin
class TokenExpiredInterceptor(
    private val secureStorage: SecureStorage
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val response = chain.proceed(chain.request())
        
        if (response.code == 401) {
            // Token expired - clear and redirect to login
            secureStorage.clearToken()
            // Show login screen
        }
        
        return response
    }
}

// Add AFTER AuthInterceptor
val okHttpClient = OkHttpClient.Builder()
    .addInterceptor(AuthInterceptor(secureStorage))
    .addInterceptor(TokenExpiredInterceptor(secureStorage))
    .build()
```

---

## Migration for Existing Users

For drivers already in your app without passwords:

### Option 1: Force Password Setup
```kotlin
if (!hasPassword()) {
    showPasswordSetupScreen()
}

// Then register with existing driver ID
val request = RegisterRequest(
    driverProfileId = existingDriverId,
    email = userEmail,
    password = newPassword,
    sync = true
)
apiService.register(request)
```

### Option 2: Force Re-registration
```kotlin
fun migrateToNewAuth() {
    localDb.clearAllData()
    showRegistrationScreen()
}
```

---

## Complete Example

```kotlin
// 1. Setup
class SafeDriveApp : Application() {
    lateinit var secureStorage: SecureStorage
    lateinit var apiService: ApiService
    
    override fun onCreate() {
        super.onCreate()
        
        secureStorage = SecureStorage(this)
        
        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(secureStorage))
            .addInterceptor(TokenExpiredInterceptor(secureStorage))
            .build()
        
        apiService = Retrofit.Builder()
            .baseUrl("https://api.safedriveafrica.com/")
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }
}

// 2. Login
suspend fun login(email: String, password: String) {
    try {
        val response = apiService.login(LoginRequest(email, password))
        secureStorage.saveToken(response.access_token)
        // Navigate to main screen
    } catch (e: HttpException) {
        if (e.code() == 401) {
            showError("Invalid email or password")
        }
    }
}

// 3. Upload Trip (token automatically added)
suspend fun uploadTrip(trip: Trip) {
    try {
        apiService.createTrip(trip)
        // Success
    } catch (e: HttpException) {
        if (e.code() == 401) {
            // Token expired, re-login required
            navigateToLogin()
        }
    }
}
```

---

## API Endpoints Reference

| Endpoint | Auth | Purpose |
|----------|------|---------|
| POST `/api/auth/driver/register` | ❌ None | Register new driver |
| POST `/api/auth/driver/login` | ❌ None | Login existing driver |
| GET `/api/auth/driver/me` | ✅ JWT | Get current driver |
| POST `/api/trips/` | ✅ JWT | Upload trip |
| POST `/api/raw_sensor_data/` | ✅ JWT | Upload sensor data |
| All other driver endpoints | ✅ JWT | Requires authentication |

---

## Need Help?

- **API Base URL**: https://api.safedriveafrica.com
- **API Docs**: https://api.safedriveafrica.com/docs
- **Token Lifetime**: 30 days
- **Password Min Length**: 6 characters

---

## Summary

1. ✅ Add login screen
2. ✅ Store JWT token securely  
3. ✅ Add `Authorization: Bearer <token>` to ALL requests using OkHttp interceptor
4. ✅ Handle 401 errors (token expired)
5. ✅ Migrate existing users

**That's it! The 422 error will be gone.**
