#!/bin/bash

# Complete setup script: Restart cluster and deploy everything

echo "========================================="
echo "  Movie Catalogue - Full Setup"
echo "========================================="
echo ""

# Step 1: Restart kind cluster
echo "Step 1: Restarting kind cluster..."
./restartKindCluster.sh

if [ $? -ne 0 ]; then
    echo "❌ Failed to restart cluster"
    exit 1
fi

echo ""
echo "========================================="
echo ""

# Step 2: Rebuild Docker images
echo "Step 2: Rebuilding Docker images..."
echo ""

echo "Building API service..."
cd api-service
./rebuildImage.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to rebuild API service image"
    cd ..
    exit 1
fi
cd ..

echo ""
echo "Building Auth service..."
cd auth-service
./rebuildImage.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to rebuild Auth service image"
    cd ..
    exit 1
fi
cd ..

echo ""
echo "Building Catalogue service..."
cd catalogue-service
./rebuildImage.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to rebuild Catalogue service image"
    cd ..
    exit 1
fi
cd ..

echo ""
echo "Building Recommendation service..."
cd recommendation-service
./rebuildImage.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to rebuild Recommendation service image"
    cd ..
    exit 1
fi
cd ..

echo ""
echo "Building Review service..."
cd review-service
./rebuildImage.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to rebuild Review service image"
    cd ..
    exit 1
fi
cd ..

echo ""
echo "Building Notification service..."
cd notification-service
./rebuildImage.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to rebuild Notification service image"
    cd ..
    exit 1
fi
cd ..

echo ""
echo "✅ All Docker images rebuilt successfully"

echo ""
echo "========================================="
echo ""

# Step 3: Deploy all manifests
echo "Step 3: Deploying Kubernetes manifests..."
./deployManifests.sh

if [ $? -ne 0 ]; then
    echo "❌ Failed to deploy manifests"
    exit 1
fi

echo ""
echo "========================================="
echo ""

# Step 4: Update service IPs
echo "Step 4: Updating service IPs in deployments..."
./updateServiceIPs.sh

if [ $? -ne 0 ]; then
    echo "❌ Failed to update service IPs"
    exit 1
fi

echo ""
echo "========================================="
echo "  ✅ Setup Complete!"
echo "========================================="
echo ""
echo "Your services are available at:"
echo "  - API Service:    http://localhost:30000"
echo "  - Portainer UI:   http://localhost:30002"
echo "  - PostgreSQL:     localhost:30001"
echo "  - Frontend:       http://localhost:8000 (run: cd frontend && ./serve.sh)"
echo ""
echo "Portainer Agent Address (for Kubernetes environment setup):"
AGENT_ADDRESS=$(kubectl get service portainer-agent -n portainer -o jsonpath='{.spec.clusterIP}:{.spec.ports[0].port}' 2>/dev/null)
if [ -n "$AGENT_ADDRESS" ]; then
    echo "  $AGENT_ADDRESS"
else
    echo "  (Agent service not ready yet, run: kubectl get svc portainer-agent -n portainer)"
fi
echo ""
echo "To view all resources: kubectl get all -n default -o wide"
echo ""

