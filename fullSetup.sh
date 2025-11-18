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

# Step 2: Deploy all manifests
echo "Step 2: Deploying Kubernetes manifests..."
./deployManifests.sh

if [ $? -ne 0 ]; then
    echo "❌ Failed to deploy manifests"
    exit 1
fi

echo ""
echo "========================================="
echo "  ✅ Setup Complete!"
echo "========================================="
echo ""
echo "Your services are available at:"
echo "  - API Service:    http://localhost:30000"
echo "  - Portainer:      http://localhost:30002"
echo "  - PostgreSQL:     localhost:30001"
echo ""
echo "To view all resources: kubectl get all -n default -o wide"
echo ""

