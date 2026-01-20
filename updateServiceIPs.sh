#!/bin/bash
set -euo pipefail

echo "========================================="
echo "  🔄 Updating Service IPs in Deployments"
echo "========================================="
echo ""

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Get current ClusterIPs
POSTGRES_IP=$(kubectl get svc postgres -o jsonpath='{.spec.clusterIP}')
AUTH_IP=$(kubectl get svc auth -o jsonpath='{.spec.clusterIP}')
CATALOGUE_IP=$(kubectl get svc catalogue -o jsonpath='{.spec.clusterIP}')

# Verify core services exist
if [ -z "$POSTGRES_IP" ] || [ -z "$AUTH_IP" ] || [ -z "$CATALOGUE_IP" ]; then
    echo "❌ Error: Core services not ready!"
    echo "   Postgres IP: $POSTGRES_IP"
    echo "   Auth IP: $AUTH_IP"
    echo "   Catalogue IP: $CATALOGUE_IP"
    exit 1
fi

echo "Current service IPs:"
echo "  Postgres:   $POSTGRES_IP"
echo "  Auth:       $AUTH_IP"
echo "  Catalogue:  $CATALOGUE_IP"
echo ""

# Update API deployment (needs Auth IP and Postgres IP)
echo "Updating api-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/06-api-deployment.yaml
sed -i '' "s|value: \"http://[0-9.]*:8090\" # AUTH_SERVICE_URL|value: \"http://$AUTH_IP:8090\" # AUTH_SERVICE_URL|" KubernetesConfigs/06-api-deployment.yaml

# Get Recommendation, Review, and Notification service IPs
RECOMMENDATION_IP=$(kubectl get service recommendation-service -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
REVIEW_IP=$(kubectl get service review-service -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
NOTIFICATION_IP=$(kubectl get service notification-service -o jsonpath='{.spec.clusterIP}' 2>/dev/null)

# Verify new services exist
if [ -z "$RECOMMENDATION_IP" ] || [ -z "$REVIEW_IP" ] || [ -z "$NOTIFICATION_IP" ]; then
    echo "⚠️  Warning: New services not found!"
    echo "   Recommendation IP: ${RECOMMENDATION_IP:-NOT FOUND}"
    echo "   Review IP: ${REVIEW_IP:-NOT FOUND}"
    echo "   Notification IP: ${NOTIFICATION_IP:-NOT FOUND}"
    echo "   Skipping new service URL updates in auth-deployment"
    echo ""
    SKIP_NEW_SERVICES=true
else
    echo "  Recommendation: $RECOMMENDATION_IP"
    echo "  Review:         $REVIEW_IP"
    echo "  Notification:   $NOTIFICATION_IP"
    echo ""
    SKIP_NEW_SERVICES=false
fi

# Update Auth deployment (needs Catalogue, Recommendation, Review IPs and Postgres IP)
echo "Updating auth-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/08-auth-deployment.yaml
sed -i '' "s|value: \"http://[0-9.]*:8091\" # CATALOGUE_SERVICE_URL|value: \"http://$CATALOGUE_IP:8091\" # CATALOGUE_SERVICE_URL|" KubernetesConfigs/08-auth-deployment.yaml

if [ "$SKIP_NEW_SERVICES" = false ]; then
    sed -i '' "s|value: \"http://[0-9.]*:8092\" # RECOMMENDATION_SERVICE_URL|value: \"http://$RECOMMENDATION_IP:8092\" # RECOMMENDATION_SERVICE_URL|" KubernetesConfigs/08-auth-deployment.yaml
    sed -i '' "s|value: \"http://[0-9.]*:8093\" # REVIEW_SERVICE_URL|value: \"http://$REVIEW_IP:8093\" # REVIEW_SERVICE_URL|" KubernetesConfigs/08-auth-deployment.yaml
    sed -i '' "s|value: \"http://[0-9.]*:8094\" # NOTIFICATION_SERVICE_URL|value: \"http://$NOTIFICATION_IP:8094\" # NOTIFICATION_SERVICE_URL|" KubernetesConfigs/08-auth-deployment.yaml
fi

# Update Catalogue deployment (needs Postgres IP)
echo "Updating catalogue-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/10-catalogue-deployment.yaml

# Update Recommendation deployment (needs Postgres IP)
echo "Updating recommendation-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/16-recommendation-deployment.yaml

# Update Review deployment (needs Postgres IP)
echo "Updating review-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/18-review-deployment.yaml

# Update Notification deployment (needs Postgres IP)
echo "Updating notification-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/20-notification-deployment.yaml

echo ""
echo "✅ Service IPs updated in deployment files!"
echo ""
echo "Applying updated deployments..."
kubectl apply -f KubernetesConfigs/06-api-deployment.yaml
kubectl apply -f KubernetesConfigs/08-auth-deployment.yaml
kubectl apply -f KubernetesConfigs/10-catalogue-deployment.yaml

if [ "$SKIP_NEW_SERVICES" = false ]; then
    kubectl apply -f KubernetesConfigs/16-recommendation-deployment.yaml
    kubectl apply -f KubernetesConfigs/18-review-deployment.yaml
    kubectl apply -f KubernetesConfigs/20-notification-deployment.yaml
fi

echo ""
echo "Restarting deployments to pick up new IPs..."
if [ "$SKIP_NEW_SERVICES" = false ]; then
    kubectl rollout restart deployment api-deployment auth-deployment catalogue-deployment recommendation-deployment review-deployment notification-deployment
else
    kubectl rollout restart deployment api-deployment auth-deployment catalogue-deployment
fi

echo ""
echo "Waiting for rollouts to complete (timeout: 2 minutes)..."
kubectl rollout status deployment api-deployment --timeout=120s || echo "⚠️  API deployment taking longer than expected"
kubectl rollout status deployment auth-deployment --timeout=120s || echo "⚠️  Auth deployment taking longer than expected"
kubectl rollout status deployment catalogue-deployment --timeout=120s || echo "⚠️  Catalogue deployment taking longer than expected"

if [ "$SKIP_NEW_SERVICES" = false ]; then
    kubectl rollout status deployment recommendation-deployment --timeout=120s || echo "⚠️  Recommendation deployment taking longer than expected"
    kubectl rollout status deployment review-deployment --timeout=120s || echo "⚠️  Review deployment taking longer than expected"
    kubectl rollout status deployment notification-deployment --timeout=120s || echo "⚠️  Notification deployment taking longer than expected"
    echo ""
    echo "✅ All 6 services updated with current IPs!"
else
    echo ""
    echo "✅ Core 3 services updated with current IPs!"
fi

