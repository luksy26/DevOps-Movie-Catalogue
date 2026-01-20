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
echo "Step 3/5: Building Catalogue service..."
cd catalogue-service
./rebuildImage.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to rebuild Catalogue service image"
    cd ..
    exit 1
fi
cd ..

echo ""

# Recommendation Service
echo "Step 4/5: Building Recommendation service..."
cd recommendation-service
./rebuildImage.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to rebuild Recommendation service image"
    cd ..
    exit 1
fi
cd ..

echo ""

# Review Service
echo "Step 5/5: Building Review service..."
cd review-service
./rebuildImage.sh
if [ $? -ne 0 ]; then
    echo "❌ Failed to rebuild Review service image"
    cd ..
    exit 1
fi
cd ..

echo ""
echo "========================================="
echo "  ✅ All 5 Images Rebuilt Successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Restart the deployments to pull the new images:"
echo "     kubectl rollout restart deployment api-deployment"
echo "     kubectl rollout restart deployment auth-deployment"
echo "     kubectl rollout restart deployment catalogue-deployment"
echo "     kubectl rollout restart deployment recommendation-deployment"
echo "     kubectl rollout restart deployment review-deployment"
echo ""
echo "  2. Or run: ./restartDeployments.sh"
echo ""
