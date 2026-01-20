# Bug Fix: Service IP Update Script

## Problem
When running `fullSetup.sh`, the review and recommendation services couldn't connect to the database because the `updateServiceIPs.sh` script had multiple issues:

### Issues Found:
1. **Missing Apply/Restart**: Script updated deployment files for recommendation and review services but never applied them or restarted the pods
2. **Short Wait Time**: Only waited 5 seconds for services to be ready (not enough for ClusterIPs to be assigned)
3. **No Error Handling**: Didn't verify that services actually existed before trying to use their IPs

## Solution

### Changes Made to `updateServiceIPs.sh`:

#### 1. Increased Wait Time
```bash
# Before: sleep 5
# After:  sleep 10
```

#### 2. Added Core Service Validation
```bash
if [ -z "$POSTGRES_IP" ] || [ -z "$AUTH_IP" ] || [ -z "$CATALOGUE_IP" ]; then
    echo "❌ Error: Core services not ready!"
    exit 1
fi
```

#### 3. Added New Service Detection
```bash
if [ -z "$RECOMMENDATION_IP" ] || [ -z "$REVIEW_IP" ]; then
    echo "⚠️  Warning: New services not found!"
    SKIP_NEW_SERVICES=true
else
    SKIP_NEW_SERVICES=false
fi
```

#### 4. Apply Recommendation & Review Deployments
```bash
# Now applies ALL 5 deployment files:
kubectl apply -f KubernetesConfigs/06-api-deployment.yaml
kubectl apply -f KubernetesConfigs/08-auth-deployment.yaml
kubectl apply -f KubernetesConfigs/10-catalogue-deployment.yaml
kubectl apply -f KubernetesConfigs/16-recommendation-deployment.yaml  # ✅ NEW
kubectl apply -f KubernetesConfigs/18-review-deployment.yaml          # ✅ NEW
```

#### 5. Restart All Services
```bash
# Now restarts ALL 5 deployments:
kubectl rollout restart deployment \
    api-deployment \
    auth-deployment \
    catalogue-deployment \
    recommendation-deployment \   # ✅ NEW
    review-deployment             # ✅ NEW
```

## Testing
After the fix, when you run `fullSetup.sh`:
1. Cluster restarts (new ClusterIPs assigned)
2. Images rebuilt
3. Manifests deployed
4. **Script now waits 10 seconds for services to stabilize**
5. **Script validates all services exist**
6. **Script updates ALL deployment files with correct IPs**
7. **Script applies and restarts ALL 5 services**
8. Review service connects to database successfully ✅

## Verification
To verify the fix works:
```bash
# Run full setup
./fullSetup.sh

# Check review service logs (should see successful DB connection)
kubectl logs -l app=review --tail=20

# Should see:
# INFO:root:✅ Reviews table initialized successfully
# INFO:root:✅ Reviews table created in database.
```

## Files Modified
- `updateServiceIPs.sh` - Fixed to handle all 5 services properly
- `review-service/review.py` - Added retry logic with delay (previous fix)

## Date
January 20, 2026
