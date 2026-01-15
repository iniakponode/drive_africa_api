# Mobile App Fleet Integration Guide

**Status:** ✅ **DEPLOYED TO PRODUCTION** (January 15, 2026)

**Production API:** `https://api.safedriveafrica.com`

This document provides implementation guidance for mobile app developers to integrate the fleet joining functionality into the Drive Africa driver app.

## Overview

Drivers can join fleets in two ways:

| Flow | When It Happens | User Action Required |
|------|-----------------|---------------------|
| **Flow 1: Email Invitation** | During registration | None (automatic) |
| **Flow 2: Invite Code** | After registration | Enter code manually |

---

## Flow 1: Email-Based Invitation (Automatic)

### How It Works

1. Fleet manager invites a driver by email address (via web dashboard)
2. Driver receives an email: *"You've been invited to join ABC Transport Fleet"*
3. Driver downloads app and registers **using that exact email**
4. Backend automatically detects the pending invitation and assigns driver to fleet
5. Driver is immediately part of the fleet upon registration

### Mobile App Implementation

**No changes required to registration UI.** The magic happens on the backend.

However, the **registration response** will now include fleet information if the driver was auto-assigned:

#### Updated Registration Response

```json
// POST /api/auth/register
// Request: { "email": "john@gmail.com", "password": "..." }

// Response (driver was invited):
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "john@gmail.com",
    "role": "driver"
  },
  "driver_profile": {
    "id": "uuid",
    "email": "john@gmail.com"
  },
  "fleet_assignment": {
    "fleet_id": "uuid",
    "fleet_name": "ABC Transport",
    "vehicle_group_id": "uuid",
    "vehicle_group_name": "Downtown Team",
    "assigned_at": "2024-01-15T10:00:00Z"
  }
}

// Response (driver was NOT invited - normal registration):
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "john@gmail.com",
    "role": "driver"
  },
  "driver_profile": {
    "id": "uuid",
    "email": "john@gmail.com"
  },
  "fleet_assignment": null
}
```

### Post-Registration UI Flow

After registration, check if `fleet_assignment` is present:

```kotlin
// Android (Kotlin)
fun handleRegistrationResponse(response: RegisterResponse) {
    saveAuthToken(response.token)
    
    if (response.fleetAssignment != null) {
        // Show welcome message with fleet name
        showFleetWelcome(
            fleetName = response.fleetAssignment.fleetName,
            vehicleGroup = response.fleetAssignment.vehicleGroupName
        )
        // Navigate to main dashboard
        navigateTo(Screen.Dashboard)
    } else {
        // No fleet - show option to join one
        navigateTo(Screen.JoinFleet)
    }
}
```

```swift
// iOS (Swift)
func handleRegistrationResponse(_ response: RegisterResponse) {
    AuthManager.shared.saveToken(response.token)
    
    if let fleetAssignment = response.fleetAssignment {
        // Show welcome message with fleet name
        showFleetWelcome(
            fleetName: fleetAssignment.fleetName,
            vehicleGroup: fleetAssignment.vehicleGroupName
        )
        // Navigate to main dashboard
        navigator.push(.dashboard)
    } else {
        // No fleet - show option to join one
        navigator.push(.joinFleet)
    }
}
```

---

## Flow 2: Invite Code (Manual Entry)

### How It Works

1. Fleet manager generates an invite code (e.g., `BAYE-7EOBSF`) via web dashboard
2. Driver registers in app (normal registration, no fleet assigned)
3. Driver enters the invite code in the app (format: 4 letters-6 alphanumeric)
4. A **join request** is created with status "pending"
5. Fleet manager reviews and approves/rejects the request
6. Upon approval, driver is assigned to the fleet

### Mobile App Implementation

#### New Screen: Join Fleet

Add a screen where drivers can enter an invite code. This screen should be accessible:
- After registration (if `fleet_assignment` is null)
- From Settings/Profile menu
- From Dashboard (if not in a fleet)

**UI Mockup:**

```
┌─────────────────────────────────────┐
│         Join a Fleet                │
├─────────────────────────────────────┤
│                                     │
│  Enter the invite code provided     │
│  by your fleet manager:             │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  ABCT-X7K2M9                │    │
│  └─────────────────────────────┘    │
│                                     │
│  ┌─────────────────────────────┐    │
│  │      Submit Request         │    │
│  └─────────────────────────────┘    │
│                                     │
│  Don't have a code? Contact your    │
│  fleet manager to get one.          │
│                                     │
└─────────────────────────────────────┘
```

#### API: Submit Join Request

```
POST https://api.safedriveafrica.com/api/driver/join-fleet
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "invite_code": "BAYE-7EOBSF"
}
```

**Success Response (201):**
```json
{
  "message": "Join request submitted",
  "request_id": "uuid",
  "fleet_name": "ABC Transport",
  "status": "pending"
}
```

**Error Responses:**

| Status | Code | Message |
|--------|------|---------|
| 400 | `INVALID_CODE` | Invalid invite code |
| 400 | `EXPIRED_CODE` | This invite code has expired |
| 400 | `CODE_LIMIT_REACHED` | This invite code has reached its usage limit |
| 409 | `ALREADY_IN_FLEET` | You are already a member of a fleet |
| 409 | `PENDING_REQUEST` | You already have a pending join request |

#### Implementation Example

```kotlin
// Android (Kotlin)
class JoinFleetViewModel : ViewModel() {
    
    private val _state = MutableStateFlow(JoinFleetState())
    val state: StateFlow<JoinFleetState> = _state.asStateFlow()
    
    fun submitJoinRequest(code: String) {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, error = null) }
            
            try {
                val response = api.joinFleet(JoinFleetRequest(inviteCode = code.uppercase().trim()))
                _state.update { 
                    it.copy(
                        isLoading = false,
                        success = true,
                        fleetName = response.fleetName,
                        requestStatus = response.status
                    )
                }
            } catch (e: HttpException) {
                val error = when (e.code()) {
                    400 -> parseErrorMessage(e) // "Invalid invite code" etc.
                    409 -> parseErrorMessage(e) // "Already in a fleet" etc.
                    else -> "Something went wrong. Please try again."
                }
                _state.update { it.copy(isLoading = false, error = error) }
            }
        }
    }
}

data class JoinFleetState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val success: Boolean = false,
    val fleetName: String? = null,
    val requestStatus: String? = null
)
```

```swift
// iOS (Swift)
class JoinFleetViewModel: ObservableObject {
    @Published var isLoading = false
    @Published var error: String?
    @Published var success = false
    @Published var fleetName: String?
    @Published var requestStatus: String?
    
    func submitJoinRequest(code: String) {
        isLoading = true
        error = nil
        
        let cleanCode = code.uppercased().trimmingCharacters(in: .whitespaces)
        
        APIClient.shared.joinFleet(inviteCode: cleanCode) { [weak self] result in
            DispatchQueue.main.async {
                self?.isLoading = false
                
                switch result {
                case .success(let response):
                    self?.success = true
                    self?.fleetName = response.fleetName
                    self?.requestStatus = response.status
                    
                case .failure(let error):
                    self?.error = error.localizedDescription
                }
            }
        }
    }
}
```

---

## Fleet Status Check

### When to Check

Call this endpoint:
- On app launch (after login)
- After submitting a join request
- On pull-to-refresh in Dashboard
- When returning from background

### API: Get Fleet Status

```
GET /api/driver/fleet-status
Authorization: Bearer <jwt_token>
```

**Response - Assigned to Fleet:**
```json
{
  "status": "assigned",
  "fleet": {
    "id": "uuid",
    "name": "ABC Transport"
  },
  "vehicle_group": {
    "id": "uuid",
    "name": "Downtown Team"
  },
  "vehicle": {
    "id": "uuid",
    "license_plate": "ABC-123",
    "make": "Toyota",
    "model": "Hilux"
  },
  "pending_request": null
}
```

**Response - Pending Request:**
```json
{
  "status": "pending",
  "fleet": null,
  "vehicle_group": null,
  "vehicle": null,
  "pending_request": {
    "id": "uuid",
    "fleet_name": "ABC Transport",
    "requested_at": "2024-01-20T14:00:00Z"
  }
}
```

**Response - Not in Fleet:**
```json
{
  "status": "none",
  "fleet": null,
  "vehicle_group": null,
  "vehicle": null,
  "pending_request": null
}
```

### UI States Based on Fleet Status

```kotlin
// Android (Kotlin)
sealed class FleetStatus {
    data class Assigned(
        val fleetName: String,
        val vehicleGroup: String?,
        val vehicle: Vehicle?
    ) : FleetStatus()
    
    data class Pending(
        val fleetName: String,
        val requestedAt: Instant
    ) : FleetStatus()
    
    object None : FleetStatus()
}

@Composable
fun DashboardFleetBanner(status: FleetStatus) {
    when (status) {
        is FleetStatus.Assigned -> {
            // Show fleet name and vehicle info
            Card {
                Text("Fleet: ${status.fleetName}")
                status.vehicle?.let {
                    Text("Vehicle: ${it.licensePlate}")
                }
            }
        }
        is FleetStatus.Pending -> {
            // Show pending status with fleet name
            Card(backgroundColor = Color.Yellow.copy(alpha = 0.2f)) {
                Text("⏳ Request pending for: ${status.fleetName}")
                Text("Submitted: ${status.requestedAt.formatRelative()}")
            }
        }
        is FleetStatus.None -> {
            // Show call-to-action to join a fleet
            Card(backgroundColor = Color.Blue.copy(alpha = 0.1f)) {
                Text("You're not part of a fleet yet")
                Button(onClick = { navigateTo(Screen.JoinFleet) }) {
                    Text("Join a Fleet")
                }
            }
        }
    }
}
```

---

## Login Flow Updates

### Updated Login Response

The login response should also include fleet status:

```
POST /api/auth/login
Content-Type: application/json

{
  "email": "john@gmail.com",
  "password": "..."
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "john@gmail.com",
    "role": "driver"
  },
  "driver_profile": {
    "id": "uuid",
    "email": "john@gmail.com",
    "name": "John Doe"
  },
  "fleet_status": {
    "status": "assigned",
    "fleet": {
      "id": "uuid",
      "name": "ABC Transport"
    },
    "vehicle_group": {
      "id": "uuid",
      "name": "Downtown Team"
    },
    "vehicle": {
      "id": "uuid",
      "license_plate": "ABC-123"
    },
    "pending_request": null
  }
}
```

### Post-Login Navigation

```kotlin
// Android (Kotlin)
fun handleLoginResponse(response: LoginResponse) {
    saveAuthToken(response.token)
    saveUserProfile(response.driverProfile)
    saveFleetStatus(response.fleetStatus)
    
    // Navigate based on fleet status
    when (response.fleetStatus.status) {
        "assigned" -> navigateTo(Screen.Dashboard)
        "pending" -> {
            showToast("Your fleet request is still pending")
            navigateTo(Screen.Dashboard)
        }
        "none" -> {
            // Option 1: Go to dashboard with join fleet prompt
            navigateTo(Screen.Dashboard)
            // Option 2: Go directly to join fleet screen
            // navigateTo(Screen.JoinFleet)
        }
    }
}
```

---

## Cancel Pending Request

If a driver wants to cancel their pending join request:

```
DELETE /api/driver/join-request
Authorization: Bearer <jwt_token>
```

**Response (204):** No content - request cancelled

**Error Responses:**

| Status | Message |
|--------|---------|
| 404 | No pending join request found |

---

## Push Notifications (Recommended)

Implement push notifications for these events:

| Event | Notification |
|-------|-------------|
| Join request approved | "🎉 Welcome! You've been added to ABC Transport fleet." |
| Join request rejected | "Your request to join ABC Transport was declined." |
| Assigned to vehicle | "You've been assigned to vehicle ABC-123." |
| Removed from fleet | "You've been removed from ABC Transport fleet." |

---

## Error Handling Best Practices

### Invite Code Validation

Before submitting, validate the code format client-side:

```kotlin
fun isValidInviteCode(code: String): Boolean {
    // Format: 4 letters + hyphen + 6 alphanumeric (e.g., ABCT-X7K2M9)
    val pattern = Regex("^[A-Z]{3,4}-[A-Z0-9]{5,8}$")
    return pattern.matches(code.uppercase().trim())
}
```

### User-Friendly Error Messages

Map API errors to user-friendly messages:

```kotlin
fun mapErrorToMessage(error: ApiError): String {
    return when (error.code) {
        "INVALID_CODE" -> "This invite code doesn't exist. Please check and try again."
        "EXPIRED_CODE" -> "This invite code has expired. Ask your fleet manager for a new one."
        "CODE_LIMIT_REACHED" -> "This invite code can't be used anymore. Contact your fleet manager."
        "ALREADY_IN_FLEET" -> "You're already part of a fleet. Leave your current fleet first."
        "PENDING_REQUEST" -> "You already have a pending request. Wait for approval or cancel it."
        else -> "Something went wrong. Please try again later."
    }
}
```

---

## Complete UI Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                          APP LAUNCH                                   │
└───────────────────────────────┬──────────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Has Auth Token?     │
                    └───────────┬───────────┘
                                │
              ┌────────NO───────┴───────YES────────┐
              │                                     │
    ┌─────────▼─────────┐              ┌───────────▼───────────┐
    │   Login/Register  │              │   GET /fleet-status   │
    │      Screen       │              └───────────┬───────────┘
    └─────────┬─────────┘                          │
              │                     ┌──────────────┼──────────────┐
    ┌─────────▼─────────┐           │              │              │
    │  POST /register   │     "assigned"      "pending"       "none"
    │  POST /login      │           │              │              │
    └─────────┬─────────┘           │              │              │
              │                     │              │              │
    ┌─────────▼─────────┐    ┌──────▼──────┐ ┌─────▼─────┐ ┌──────▼──────┐
    │ Check response    │    │  DASHBOARD  │ │ DASHBOARD │ │  JOIN FLEET │
    │ fleet_assignment  │    │ (full view) │ │ (pending  │ │   PROMPT    │
    └─────────┬─────────┘    └─────────────┘ │  banner)  │ └──────┬──────┘
              │                               └───────────┘        │
      ┌───────┴───────┐                                            │
   HAS FLEET      NO FLEET                                         │
      │               │                                            │
┌─────▼─────┐  ┌──────▼──────┐                            ┌────────▼────────┐
│ DASHBOARD │  │ JOIN FLEET  │◄───────────────────────────│ Enter Code Form │
└───────────┘  │   PROMPT    │                            └────────┬────────┘
               └─────────────┘                                     │
                                                          ┌────────▼────────┐
                                                          │POST /join-fleet │
                                                          └────────┬────────┘
                                                                   │
                                                          ┌────────▼────────┐
                                                          │ Success Screen  │
                                                          │ "Request sent!" │
                                                          └─────────────────┘
```

---

## Testing Checklist

**Production Environment:** `https://api.safedriveafrica.com`

**Test Invite Code:** `BAYE-7EOBSF` (Bayelsa State Transport Company, max 10 uses)

### Flow 1 (Email Invitation) Tests
- [ ] Register with an email that has a pending invite → auto-assigned to fleet
- [ ] Register with an email that has NO pending invite → fleet_assignment is null
- [ ] Register with an expired invite → treated as no invite
- [ ] Login after being assigned via invite → fleet info in response

### Flow 2 (Invite Code) Tests
- [ ] Submit valid code → join request created, "pending" status
- [ ] Submit invalid code → appropriate error message
- [ ] Submit expired code → "expired" error
- [ ] Submit code that's maxed out → "limit reached" error
- [ ] Submit code when already in a fleet → "already in fleet" error
- [ ] Submit code when request pending → "pending request" error
- [ ] Cancel pending request → request removed
- [ ] Fleet manager approves → status changes to "assigned"
- [ ] Fleet manager rejects → status changes to "none"

### Fleet Status Tests
- [ ] Check status when assigned → correct fleet/vehicle info
- [ ] Check status when pending → pending request info
- [ ] Check status when not in fleet → status = "none"
- [ ] Refresh after approval → status updates correctly

---

## API Endpoints Summary

**Base URL:** `https://api.safedriveafrica.com`

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/register` | POST | Register (auto-checks email invites) |
| `/api/auth/login` | POST | Login (returns fleet status) |
| `/api/driver/fleet-status` | GET | Get current fleet membership status |
| `/api/driver/join-fleet` | POST | Submit join request with invite code |
| `/api/driver/join-request` | DELETE | Cancel pending join request |

---

## Questions for Backend Team

1. Should the mobile app be able to leave a fleet? (Endpoint: `DELETE /api/driver/fleet`)
2. Can a driver have pending requests to multiple fleets, or only one at a time?
3. Should we add a deep link for email invitations? (e.g., `driveafrica://join?token=ABC123`)
4. What's the retention policy for rejected join requests?
