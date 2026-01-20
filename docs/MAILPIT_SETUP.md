# Mailpit Email Notification Setup

## Overview
Mailpit is now integrated with your notification service to send beautiful HTML email notifications to users when they receive movie recommendations.

## What Was Set Up

### 1. **Mailpit Service** 📬
- **Web UI Port**: 30025 (`http://localhost:30025`)
- **SMTP Port**: 1025
- Modern email testing tool with a beautiful UI
- Stores up to 500 messages
- REST API available

### 2. **Database Updates** 💾
- Added `email` column to `users` table (auth service)
- Added `user_email` column to `user_sessions` table (notification service)
- Email is optional but recommended for notifications

### 3. **Notification Service Updates** 📧
- Sends HTML emails with movie posters, ratings, and descriptions
- Beautiful responsive email templates
- Automatic email sending every 20-30 seconds (same as app notifications)
- Email can be disabled via environment variable

### 4. **Auth Service Updates** 🔐
- Registration now accepts optional email field
- Login passes user email to notification service
- Email stored securely in database

---

## Architecture

```
User Login → Auth Service → Notification Service
                                    ↓
                          Registers session with email
                                    ↓
                          Background Task (20-30s)
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
            Create DB Notification          Send Email via SMTP
                    ↓                               ↓
            Frontend Bell 🔔                   Mailpit 📬
```

---

## Deployment Instructions

### Step 1: Start Your Kubernetes Cluster
```bash
cd /Users/llazaroiu/DevOps-Movie-Catalogue
kind create cluster --config kind-config.yaml
# Or if already created: kubectl cluster-info
```

### Step 2: Deploy Mailpit
```bash
kubectl apply -f KubernetesConfigs/22-mailpit-deployment.yaml
kubectl apply -f KubernetesConfigs/23-mailpit-service.yaml

# Wait for Mailpit to be ready
kubectl wait --for=condition=ready pod -l app=mailpit --timeout=60s
```

### Step 3: Rebuild Services with Email Support
```bash
# Rebuild notification and auth services
cd notification-service && ./rebuildImage.sh && cd ..
cd auth-service && ./rebuildImage.sh && cd ..
```

### Step 4: Deploy Everything
```bash
# Run full setup (recommended)
./fullSetup.sh

# Or update just the services
kubectl apply -f KubernetesConfigs/08-auth-deployment.yaml
kubectl apply -f KubernetesConfigs/20-notification-deployment.yaml
kubectl rollout restart deployment auth-deployment notification-deployment
```

### Step 5: Verify Deployment
```bash
# Check all pods are running
kubectl get pods

# Should see:
# mailpit-deployment-xxx          (Running)
# notification-deployment-xxx     (Running)
# auth-deployment-xxx             (Running)
```

---

## Access Mailpit UI

Once deployed, open your browser to:
```
http://localhost:30025
```

You'll see a beautiful interface showing all emails sent by the system!

---

## Testing Email Notifications

### Option 1: Register with Email (New User)
```bash
# Via frontend (http://localhost:30000)
1. Click "Register"
2. Username: testuser
3. Password: password123
4. Email: testuser@example.com  ← NEW FIELD
5. Click Register
```

### Option 2: API Test
```bash
# Register user with email
curl -X POST http://localhost:30000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "email": "testuser@example.com"
  }'

# Login (automatically registers session with email)
curl -X POST http://localhost:30000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### Option 3: Direct Database Update (Existing Users)
```bash
# Connect to postgres
kubectl port-forward svc/postgres-exposed 30001:5432

# Update existing user with email
psql -h localhost -p 30001 -U admin -d movieApp
UPDATE users SET email = 'user@example.com' WHERE username = 'youruser';
```

### Watch for Emails
1. Open Mailpit: `http://localhost:30025`
2. Wait 20-30 seconds after login
3. You should see an email appear!
4. Click to view the beautiful HTML email

---

## Email Template Preview

The emails include:
- 🎬 Movie title with gradient header
- ⭐ Rating and release date
- 🖼️ Movie poster image
- 📝 Full movie overview
- 🎨 Responsive, mobile-friendly design

---

## Configuration Options

### Environment Variables (Notification Service)

```yaml
# SMTP Configuration
SMTP_HOST: "mailpit"           # Mailpit service name
SMTP_PORT: "1025"              # SMTP port
SMTP_FROM: "notifications@movieapp.local"  # From address
EMAIL_ENABLED: "true"          # Enable/disable emails

# To disable emails temporarily
EMAIL_ENABLED: "false"
```

### Customization

#### Change Email Frequency
Edit `notification-service/notification.py`:
```python
# Line ~226
sleep_time = random.randint(20, 30)  # Seconds between checks
```

#### Change Email Template
Edit `notification-service/notification.py`, function `send_email_notification()`:
```python
# Lines ~130-180 contain the HTML template
```

#### Change "From" Address
Edit `KubernetesConfigs/20-notification-deployment.yaml`:
```yaml
- name: SMTP_FROM
  value: "your-custom@address.com"
```

---

## Troubleshooting

### No Emails Arriving

**Check 1: Is Mailpit running?**
```bash
kubectl get pods -l app=mailpit
# Should show: Running
```

**Check 2: Check notification service logs**
```bash
kubectl logs -l app=notification --tail=50

# Look for:
# 📧 Email sent to user@example.com: Movie Title
```

**Check 3: Is EMAIL_ENABLED set?**
```bash
kubectl get deployment notification-deployment -o yaml | grep EMAIL_ENABLED
# Should show: value: "true"
```

**Check 4: Does user have email?**
```bash
# Connect to database
kubectl port-forward svc/postgres-exposed 30001:5432
psql -h localhost -p 30001 -U admin -d movieApp

# Check user email
SELECT id, username, email FROM users WHERE username = 'youruser';

# Check session email
SELECT user_id, user_email, is_active FROM user_sessions WHERE user_id = X;
```

### Emails in Spam/Not Displaying

- Mailpit shows ALL emails, they can't go to spam
- If not seeing in Mailpit UI, check the notification service logs
- Mailpit UI refresh: F5 or click the refresh button

### Mailpit UI Not Accessible

```bash
# Check service
kubectl get service mailpit

# Should show NodePort 30025

# Check port forwarding
kubectl port-forward svc/mailpit 30025:8025

# Then access: http://localhost:30025
```

---

## Mailpit Features

### Web UI (`http://localhost:30025`)
- **Inbox View**: See all emails
- **Search**: Search by recipient, subject, content
- **Preview**: View HTML/text versions
- **Headers**: Inspect email headers
- **Raw**: View raw email source
- **Auto-refresh**: New emails appear automatically

### REST API (`http://localhost:30025/api/v1/`)
- Get messages: `GET /api/v1/messages`
- Get message: `GET /api/v1/message/{id}`
- Delete message: `DELETE /api/v1/message/{id}`
- Search: `GET /api/v1/search?query=test`

### Storage
- In-memory (data lost on restart)
- Max 500 messages (configurable)
- Oldest messages auto-deleted when limit reached

---

## Production Considerations

### For Production Deployment

**Don't use Mailpit in production!** It's for development/testing only.

For production, use a real email service:

1. **SendGrid** (recommended)
   ```python
   SMTP_HOST: "smtp.sendgrid.net"
   SMTP_PORT: "587"
   SMTP_USER: "apikey"
   SMTP_PASSWORD: "<your-api-key>"
   ```

2. **AWS SES**
   ```python
   SMTP_HOST: "email-smtp.us-east-1.amazonaws.com"
   SMTP_PORT: "587"
   ```

3. **Mailgun**
   ```python
   SMTP_HOST: "smtp.mailgun.org"
   SMTP_PORT: "587"
   ```

### Update notification-service/notification.py for Production

```python
# Add authentication support
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

def send_email_notification(...):
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        if SMTP_USER and SMTP_PASSWORD:
            server.starttls()  # Enable TLS
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
```

---

## Files Created/Modified

### New Files
```
KubernetesConfigs/
├── 22-mailpit-deployment.yaml    - Mailpit pod deployment
└── 23-mailpit-service.yaml       - Mailpit service (ports 8025, 1025)
```

### Modified Files
```
notification-service/notification.py  - Added email sending functionality
auth-service/auth.py                  - Added email field to users table
KubernetesConfigs/20-notification-deployment.yaml  - Added SMTP env vars
```

### Database Changes
```sql
-- users table (auth service)
ALTER TABLE users ADD COLUMN email VARCHAR(255);

-- user_sessions table (notification service)
ALTER TABLE user_sessions ADD COLUMN user_email VARCHAR(255);
```

---

## Quick Commands Reference

```bash
# Deploy Mailpit
kubectl apply -f KubernetesConfigs/22-mailpit-deployment.yaml
kubectl apply -f KubernetesConfigs/23-mailpit-service.yaml

# Access Mailpit UI
open http://localhost:30025

# Check Mailpit logs
kubectl logs -l app=mailpit --tail=50

# Check notification service logs
kubectl logs -l app=notification --tail=50 -f

# Restart notification service
kubectl rollout restart deployment notification-deployment

# Test email sending
# (Register new user with email, then wait 20-30 seconds)
```

---

## Success Checklist

- ✅ Mailpit pod running
- ✅ Mailpit UI accessible at `http://localhost:30025`
- ✅ Notification service has SMTP environment variables
- ✅ Auth service updated to handle email field
- ✅ Users can register with email
- ✅ Emails arrive in Mailpit inbox within 20-30 seconds of login

---

## Date
January 20, 2026
