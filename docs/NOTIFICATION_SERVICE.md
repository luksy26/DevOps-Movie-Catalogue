# Notification Service Implementation

## Overview
The notification service sends random upcoming movie recommendations to logged-in users at intervals between 20-30 seconds (with random jitter).

## Architecture

### New Microservice: `notification-service`
- **Port**: 8094
- **Language**: Python/Flask
- **Database**: PostgreSQL (shares `movieApp` database)
- **External API**: TMDB (The Movie Database)

## Features

### 1. Automatic Movie Recommendations
- Fetches upcoming movies from TMDB API
- Randomly selects movies from different pages (1-5)
- Sends recommendations to active users every 20-30 seconds (randomized)
- Background thread continuously monitors for active sessions

### 2. User Session Tracking
- Registers user sessions on login
- Tracks last notification time per user
- Marks sessions as inactive on logout

### 3. Notification Storage
- Stores notifications in database with:
  - Movie ID, title, overview
  - Poster path, release date, rating
  - Read/unread status
  - Timestamp

### 4. Frontend Integration
- **Notification Bell** (🔔) in top-right corner
- **Badge** showing unread count
- **Dropdown** displaying notification list
- **Auto-refresh** every 10 seconds
- **Mark as read** on click
- **Responsive design** with animations

## Database Tables

### `user_sessions`
```sql
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_notification_time TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
)
```

### `notifications`
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    movie_title VARCHAR(255) NOT NULL,
    movie_overview TEXT,
    movie_poster_path VARCHAR(255),
    movie_release_date VARCHAR(20),
    movie_rating FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE
)
```

## API Endpoints

### Notification Service (Port 8094)
```
GET  /notifications/test-db                  - Test database connection
POST /notifications/session                  - Register user session
DELETE /notifications/session/<user_id>      - End user session
GET  /notifications/<user_id>                - Get user notifications
GET  /notifications/<user_id>/unread-count   - Get unread count
PUT  /notifications/<notification_id>/read   - Mark as read
```

### Auth Service (Forwards to Notification Service)
```
GET  /auth/notifications                     - Get user notifications
GET  /auth/notifications/unread-count        - Get unread count
PUT  /auth/notifications/<id>/read           - Mark as read
```

### API Service (Frontend-facing)
```
GET  /api/notifications                      - Get user notifications
GET  /api/notifications/unread-count         - Get unread count
PUT  /api/notifications/<id>/read            - Mark as read
```

## Files Created/Modified

### New Files
```
notification-service/
├── notification.py          - Main Flask application
├── requirements.txt         - Python dependencies
├── Dockerfile              - Container definition
└── rebuildImage.sh         - Image build script

KubernetesConfigs/
├── 20-notification-deployment.yaml    - Deployment manifest
└── 21-notification-ClusterIP.yaml     - Service manifest
```

### Modified Files
```
auth-service/auth.py                    - Added notification endpoints + session registration
api-service/api.py                      - Added notification endpoints
frontend/index.html                     - Added notification UI + JavaScript
KubernetesConfigs/08-auth-deployment.yaml  - Added NOTIFICATION_SERVICE_URL
updateServiceIPs.sh                     - Added notification service IP updates
rebuildAllImages.sh                     - Added notification service build (6 services now)
restartDeployments.sh                   - Added notification deployment restart
```

## How It Works

### 1. User Logs In
```
Frontend → API → Auth → Login Success
                 ↓
          Notification Service (POST /notifications/session)
                 ↓
          Session registered, is_active=TRUE
```

### 2. Background Task (Runs Every 20-30 Seconds)
```
Notification Service Background Thread:
1. Sleep random(20, 30) seconds
2. Query active users eligible for notifications
3. Fetch random upcoming movie from TMDB
4. Insert notification into database
5. Update last_notification_time for user
6. Repeat
```

### 3. Frontend Polling (Every 10 Seconds)
```
Frontend (Auto-refresh):
1. Call GET /api/notifications/unread-count
2. Update badge number
3. Repeat every 10 seconds
```

### 4. User Opens Notifications
```
User clicks bell → GET /api/notifications
                   ↓
          Display list in dropdown
                   ↓
          User clicks notification
                   ↓
          PUT /api/notifications/<id>/read
                   ↓
          Notification marked as read
                   ↓
          Badge count updated
```

## Configuration

### Environment Variables (Notification Service)
```yaml
PGUSER: admin
PGPASSWORD: admin
PGDATABASE: movieApp
PGHOST: postgres
PGHOSTADDR: <postgres-cluster-ip>
PGPORT: 5432
TMDB_API_TOKEN: <from-configmap>
```

### TMDB API Configuration
- Uses existing `TMDB_API_TOKEN` from ConfigMap
- Endpoint: `https://api.themoviedb.org/3/movie/upcoming`
- Fetches from random pages (1-5) for variety

## Deployment

### Quick Start
```bash
# Full setup (includes notification service)
./fullSetup.sh

# Or manual deployment
kubectl apply -f KubernetesConfigs/20-notification-deployment.yaml
kubectl apply -f KubernetesConfigs/21-notification-ClusterIP.yaml
./updateServiceIPs.sh
```

### Build & Deploy
```bash
# Rebuild all images (including notification service)
./rebuildAllImages.sh

# Restart all deployments
./restartDeployments.sh
```

### Verify Deployment
```bash
# Check pods
kubectl get pods -l app=notification

# Check logs
kubectl logs -l app=notification --tail=50

# Should see:
# ✅ Notification tables initialized successfully
# 🔔 Notification background task started
# 💤 Sleeping for X seconds before next notification check...
```

## Testing

### 1. Login to Frontend
```
http://localhost:30000
```

### 2. Watch for Notifications
- Wait 20-30 seconds after login
- Notification bell badge should appear with count
- Click bell to see notification dropdown

### 3. Check Logs
```bash
# See notification background task
kubectl logs -l app=notification --tail=50 -f

# Should see:
# 📢 Found X users eligible for notifications
# ✅ Sent notification to user X: <Movie Title>
```

### 4. Verify Database
```bash
# Connect to postgres
kubectl port-forward svc/postgres-exposed 30001:5432

# Query notifications
psql -h localhost -p 30001 -U admin -d movieApp
SELECT * FROM notifications ORDER BY created_at DESC LIMIT 10;
SELECT * FROM user_sessions WHERE is_active = TRUE;
```

## Customization

### Change Notification Frequency
Edit `notification-service/notification.py`:
```python
# Line ~142
sleep_time = random.randint(20, 30)  # Change these values
```

### Change Eligible Wait Time
Edit `notification-service/notification.py`:
```python
# Line ~168
OR last_notification_time < NOW() - INTERVAL '20 seconds'  # Change interval
```

### Change Frontend Poll Frequency
Edit `frontend/index.html`:
```javascript
// Line ~992
notificationCheckInterval = setInterval(() => {
    checkUnreadCount();
}, 10000);  // Change from 10000ms (10 seconds)
```

## Troubleshooting

### No Notifications Appearing
1. Check notification service logs:
   ```bash
   kubectl logs -l app=notification --tail=50
   ```
2. Verify TMDB API token is configured
3. Check user session is registered:
   ```sql
   SELECT * FROM user_sessions WHERE user_id = X;
   ```

### Notification Service Not Starting
1. Check database connection:
   ```bash
   kubectl logs -l app=notification
   ```
2. Verify PGHOSTADDR is correct in deployment
3. Run `./updateServiceIPs.sh`

### Badge Not Updating
1. Check browser console for errors
2. Verify auth token is valid
3. Check API service can reach auth service

## Architecture Diagram

```
┌─────────────┐
│   Frontend  │ (Notification Bell + Dropdown)
└──────┬──────┘
       │ HTTP (every 10s)
       ↓
┌─────────────┐
│ API Service │ (Port 30000)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│Auth Service │ (Port 8090)
└──────┬──────┘
       │
       ↓
┌───────────────────┐
│Notification Service│ (Port 8094)
│                   │
│  ┌─────────────┐  │
│  │Background   │  │ Runs every 20-30s
│  │Task Thread  │  │
│  └──────┬──────┘  │
└─────────┼─────────┘
          │
          ↓
    ┌──────────┐      ┌────────┐
    │PostgreSQL│◄────►│ TMDB   │
    └──────────┘      │  API   │
                      └────────┘
```

## Success Metrics
- ✅ 6 microservices running (was 5)
- ✅ Background task sends notifications every 20-30 seconds
- ✅ Frontend polls for updates every 10 seconds
- ✅ Notifications stored in database
- ✅ Real-time badge count updates
- ✅ Mark as read functionality
- ✅ Session tracking on login/logout

## Date
January 20, 2026
