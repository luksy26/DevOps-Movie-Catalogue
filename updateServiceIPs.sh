#!/bin/bash
set -euo pipefail

echo "========================================="
echo "  🔄 Updating Service IPs in Deployments"
echo "========================================="
echo ""

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Get current ClusterIPs
POSTGRES_IP=$(kubectl get svc postgres -o jsonpath='{.spec.clusterIP}')
AUTH_IP=$(kubectl get svc auth -o jsonpath='{.spec.clusterIP}')
CATALOGUE_IP=$(kubectl get svc catalogue -o jsonpath='{.spec.clusterIP}')

echo "Current service IPs:"
echo "  Postgres:   $POSTGRES_IP"
echo "  Auth:       $AUTH_IP"
echo "  Catalogue:  $CATALOGUE_IP"
echo ""

# Update API deployment (needs Auth IP and Postgres IP)
echo "Updating api-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/06-api-deployment.yaml
sed -i '' "s|value: \"http://[0-9.]*:8090\" # AUTH_SERVICE_URL|value: \"http://$AUTH_IP:8090\" # AUTH_SERVICE_URL|" KubernetesConfigs/06-api-deployment.yaml

# Get Recommendation and Review service IPs
RECOMMENDATION_IP=$(kubectl get service recommendation-service -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "10.96.0.1")
REVIEW_IP=$(kubectl get service review-service -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "10.96.0.1")
echo "  Recommendation: $RECOMMENDATION_IP"
echo "  Review:         $REVIEW_IP"
echo ""

# Update Auth deployment (needs Catalogue, Recommendation, Review IPs and Postgres IP)
echo "Updating auth-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/08-auth-deployment.yaml
sed -i '' "s|value: \"http://[0-9.]*:8091\" # CATALOGUE_SERVICE_URL|value: \"http://$CATALOGUE_IP:8091\" # CATALOGUE_SERVICE_URL|" KubernetesConfigs/08-auth-deployment.yaml
sed -i '' "s|value: \"http://[0-9.]*:8092\" # RECOMMENDATION_SERVICE_URL|value: \"http://$RECOMMENDATION_IP:8092\" # RECOMMENDATION_SERVICE_URL|" KubernetesConfigs/08-auth-deployment.yaml
sed -i '' "s|value: \"http://[0-9.]*:8093\" # REVIEW_SERVICE_URL|value: \"http://$REVIEW_IP:8093\" # REVIEW_SERVICE_URL|" KubernetesConfigs/08-auth-deployment.yaml

# Update Catalogue deployment (needs Postgres IP)
echo "Updating catalogue-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/10-catalogue-deployment.yaml

# Update Recommendation deployment (needs Postgres IP)
echo "Updating recommendation-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/16-recommendation-deployment.yaml

# Update Review deployment (needs Postgres IP)
echo "Updating review-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/18-review-deployment.yaml

echo ""
echo "✅ Service IPs updated in deployment files!"
echo ""
echo "Applying updated deployments..."
kubectl apply -f KubernetesConfigs/06-api-deployment.yaml
kubectl apply -f KubernetesConfigs/08-auth-deployment.yaml
kubectl apply -f KubernetesConfigs/10-catalogue-deployment.yaml

echo ""
echo "Restarting deployments to pick up new IPs..."
kubectl rollout restart deployment api-deployment auth-deployment catalogue-deployment

echo ""
echo "Waiting for rollouts to complete (timeout: 2 minutes)..."
kubectl rollout status deployment api-deployment --timeout=120s || echo "⚠️  API deployment taking longer than expected"
kubectl rollout status deployment auth-deployment --timeout=120s || echo "⚠️  Auth deployment taking longer than expected"
kubectl rollout status deployment catalogue-deployment --timeout=120s || echo "⚠️  Catalogue deployment taking longer than expected"

echo ""
echo "✅ All services updated with current IPs!"

