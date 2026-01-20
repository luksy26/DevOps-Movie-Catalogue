# Session Management Fix

## 🐛 **The Problem**

**Before the fix:**
- Users who logged out (or closed the browser) remained marked as `is_active = TRUE`
- The notification service kept sending notifications to inactive users
- When users logged back in, they would have **hundreds of accumulated notifications**
- Database and TMDB API were wasted on inactive users

## ✅ **The Solution**

Implemented **proper session lifecycle management** with three layers:

### 1. **Explicit Logout** 🚪
When users click the logout button:
```
Frontend → API → Auth → Notification Service
                           ↓
                  Sets is_active = FALSE
```

### 2. **Auto-Expire Old Sessions** ⏰
Every 20-30 seconds, the background task checks for stale sessions:
```sql
UPDATE user_sessions
SET is_active = FALSE
WHERE is_active = TRUE
AND login_time < NOW() - INTERVAL '1 hour'
```

This matches the JWT expiration time (1 hour).

### 3. **Session Reset on Re-Login** 🔄
When users log in again:
```sql
-- UPSERT clears old state
INSERT INTO user_sessions (user_id, user_email, login_time, is_active)
VALUES (..., NOW(), TRUE)
ON CONFLICT (user_id)
DO UPDATE SET
    login_time = NOW(),
    is_active = TRUE,
    last_notification_time = NULL  -- Reset notification timer
```

---

## 📝 **Changes Made**

### Frontend (`frontend/index.html`)
**Changed `logout()` to async and call API:**
```javascript
async function logout() {
    // Call logout endpoint to mark session as inactive
    if (authToken) {
        await fetch(`${API_BASE}/logout`, {
            method: 'POST',
            headers: { 'Authorization': authToken }
        });
    }
    
    // Clear local state
    authToken = null;
    clearAuthState();
    showLogin();
}
```

### API Service (`api-service/api.py`)
**Added logout endpoint:**
```python
@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Logout a user. Marks their session as inactive."""
    token = request.headers.get('Authorization')
    response = requests.post(
        f"{AUTH_SERVICE_URL}/auth/logout",
        headers={"Authorization": token}
    )
    return jsonify(response.json()), response.status_code
```

### Auth Service (`auth-service/auth.py`)
**Added logout endpoint that calls notification service:**
```python
@app.route('/auth/logout', methods=['POST'])
def logout():
    """Logout user and mark session as inactive"""
    decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    user_id = decoded_token.get('user_id')
    
    # Mark session as inactive in notification service
    requests.delete(
        f"{NOTIFICATION_SERVICE_URL}/notifications/session/{user_id}"
    )
    
    return jsonify({"message": "Logged out successfully"}), 200
```

### Notification Service (`notification-service/notification.py`)
**Added auto-expire logic in background task:**
```python
# Auto-expire old sessions (inactive for 1+ hours)
cur.execute("""
    UPDATE user_sessions
    SET is_active = FALSE
    WHERE is_active = TRUE
    AND login_time < NOW() - INTERVAL '1 hour'
""")
expired_count = cur.rowcount
if expired_count > 0:
    logging.info(f"⏰ Auto-expired {expired_count} old session(s)")
```

**Existing DELETE endpoint** (already works):
```python
@app.route('/notifications/session/<int:user_id>', methods=['DELETE'])
def end_session(user_id):
    """Mark user session as inactive"""
    cur.execute("""
        UPDATE user_sessions
        SET is_active = FALSE
        WHERE user_id = %s
    """, (user_id,))
```

---

## 🔄 **Session Lifecycle (Fixed)**

```
┌─────────────┐
│ User Logs In│
└──────┬──────┘
       │
       ↓
   is_active = TRUE
   login_time = NOW()
       │
       ↓
┌──────────────────────────────┐
│ Background Task Loop         │
│ (every 20-30 seconds)        │
│                              │
│ 1. Auto-expire old sessions  │
│    (login_time > 1 hour)     │
│                              │
│ 2. Send notifications to     │
│    active users only         │
└──────────────────────────────┘
       │
       ↓
   [User Actions]
       │
       ├─→ Logs Out       → is_active = FALSE ✅
       ├─→ Closes Browser → Auto-expired after 1 hour ✅
       └─→ Re-Logs In     → is_active = TRUE, timer reset ✅
```

---

## 📊 **Before vs After**

| Scenario | Before | After |
|----------|--------|-------|
| **User logs out** | ❌ Still active | ✅ Marked inactive |
| **User closes browser** | ❌ Still active forever | ✅ Auto-expired after 1 hour |
| **User returns after 2 hours** | ❌ 200+ notifications waiting | ✅ Clean slate |
| **Notifications sent to inactive users** | ❌ Yes (wasted resources) | ✅ No |

---

## 🧪 **Testing**

### Test 1: Explicit Logout
```bash
# 1. Login
curl -X POST http://localhost:30000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "password"}'

# 2. Check session (should be active)
kubectl exec -it deployment/notification-deployment -- \
  psql -U admin -d movieApp -c \
  "SELECT user_id, is_active FROM user_sessions WHERE user_id = 1;"

# 3. Logout
curl -X POST http://localhost:30000/api/logout \
  -H "Authorization: <your-token>"

# 4. Check session (should be inactive)
kubectl exec -it deployment/notification-deployment -- \
  psql -U admin -d movieApp -c \
  "SELECT user_id, is_active FROM user_sessions WHERE user_id = 1;"
```

### Test 2: Auto-Expire
```bash
# 1. Manually set old login_time
kubectl exec -it deployment/notification-deployment -- \
  psql -U admin -d movieApp -c \
  "UPDATE user_sessions SET login_time = NOW() - INTERVAL '2 hours' WHERE user_id = 1;"

# 2. Wait 20-30 seconds for background task to run

# 3. Check logs
kubectl logs -l app=notification --tail=20

# Should see: "⏰ Auto-expired 1 old session(s)"

# 4. Check session (should be inactive)
kubectl exec -it deployment/notification-deployment -- \
  psql -U admin -d movieApp -c \
  "SELECT user_id, is_active, login_time FROM user_sessions WHERE user_id = 1;"
```

### Test 3: No Accumulated Notifications
```bash
# 1. Login and immediately logout
curl -X POST http://localhost:30000/api/login ...
curl -X POST http://localhost:30000/api/logout ...

# 2. Wait 5 minutes

# 3. Login again
curl -X POST http://localhost:30000/api/login ...

# 4. Check notification count (should be 0 or very few)
curl http://localhost:30000/api/notifications \
  -H "Authorization: <token>"
```

---

## 🎯 **Benefits**

1. ✅ **No notification spam** - Users don't accumulate hundreds of notifications
2. ✅ **Resource efficiency** - Don't waste DB/API calls on inactive users
3. ✅ **Better UX** - Clean slate when returning to the app
4. ✅ **Automatic cleanup** - Handles users who close browser without logging out
5. ✅ **Matches JWT lifetime** - Sessions expire when tokens do (1 hour)

---

## 🔍 **Monitoring Queries**

```sql
-- View all sessions
SELECT 
    user_id,
    user_email,
    is_active,
    login_time,
    EXTRACT(EPOCH FROM (NOW() - login_time))/60 as minutes_since_login,
    last_notification_time
FROM user_sessions
ORDER BY login_time DESC;

-- Count active vs inactive
SELECT 
    is_active,
    COUNT(*) as session_count
FROM user_sessions
GROUP BY is_active;

-- Find sessions that should be expired
SELECT 
    user_id,
    is_active,
    login_time,
    EXTRACT(EPOCH FROM (NOW() - login_time))/3600 as hours_since_login
FROM user_sessions
WHERE is_active = TRUE
AND login_time < NOW() - INTERVAL '1 hour';
```

---

## ⚙️ **Configuration**

### Session Timeout Duration
Edit `notification-service/notification.py`:
```python
# Line ~248
AND login_time < NOW() - INTERVAL '1 hour'  # Change this
```

Match it with JWT expiration in `auth-service/auth.py`:
```python
# Line ~198
"exp": datetime.now() + timedelta(hours=1)  # Keep these in sync
```

---

## 📅 **Date**
January 20, 2026

---

## 🎉 **Result**

Users can now:
- ✅ Logout properly (sessions marked inactive immediately)
- ✅ Close the browser (sessions auto-expire after 1 hour)
- ✅ Return to a clean slate (no notification backlog)
- ✅ Have a much better user experience!
