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

# Update Auth deployment (needs Catalogue IP and Postgres IP)
echo "Updating auth-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/08-auth-deployment.yaml
sed -i '' "s|value: \"http://[0-9.]*:8091\" # CATALOGUE_SERVICE_URL|value: \"http://$CATALOGUE_IP:8091\" # CATALOGUE_SERVICE_URL|" KubernetesConfigs/08-auth-deployment.yaml

# Update Catalogue deployment (needs Postgres IP)
echo "Updating catalogue-deployment.yaml..."
sed -i '' "s/value: \"[0-9.]*\" # PGHOSTADDR/value: \"$POSTGRES_IP\" # PGHOSTADDR/" KubernetesConfigs/10-catalogue-deployment.yaml

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
echo "Waiting for rollouts to complete..."
kubectl rollout status deployment api-deployment
kubectl rollout status deployment auth-deployment
kubectl rollout status deployment catalogue-deployment

echo ""
echo "✅ All services updated with current IPs!"

