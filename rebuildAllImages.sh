#!/bin/bash

# Rebuild all Docker images for the microservices

echo "========================================="
echo "  Rebuilding All Docker Images"
echo "========================================="
echo ""

# API Service
echo "Step 1/3: Building API service..."
cd api-service
./rebuildImage.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to rebuild API service image"
    cd ..
    exit 1
fi
cd ..

echo ""

# Auth Service
echo "Step 2/3: Building Auth service..."
cd auth-service
./rebuildImage.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to rebuild Auth service image"
    cd ..
    exit 1
fi
cd ..

echo ""

# Catalogue Service
echo "Step 3/3: Building Catalogue service..."
cd catalogue-service
./rebuildImage.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to rebuild Catalogue service image"
    cd ..
    exit 1
fi
cd ..

echo ""
echo "========================================="
echo "  ✅ All Images Rebuilt Successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Restart the deployments to pull the new images:"
echo "     kubectl rollout restart deployment api-deployment"
echo "     kubectl rollout restart deployment auth-deployment"
echo "     kubectl rollout restart deployment catalogue-deployment"
echo ""
echo "  2. Or run: ./restartDeployments.sh"
echo ""
