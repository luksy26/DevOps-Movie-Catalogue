#!/bin/bash

# Restart all service deployments to pull latest images

echo "========================================="
echo "  Restarting Service Deployments"
echo "========================================="
echo ""

echo "Restarting API deployment..."
kubectl rollout restart deployment api-deployment
if [ $? -ne 0 ]; then
    echo "❌ Failed to restart API deployment"
    exit 1
fi

echo ""
echo "Restarting Auth deployment..."
kubectl rollout restart deployment auth-deployment
if [ $? -ne 0 ]; then
    echo "❌ Failed to restart Auth deployment"
    exit 1
fi

echo ""
echo "Restarting Catalogue deployment..."
kubectl rollout restart deployment catalogue-deployment
if [ $? -ne 0 ]; then
    echo "❌ Failed to restart Catalogue deployment"
    exit 1
fi

echo ""
echo "Waiting for deployments to be ready..."
kubectl rollout status deployment api-deployment
kubectl rollout status deployment auth-deployment
kubectl rollout status deployment catalogue-deployment

echo ""
echo "========================================="
echo "  ✅ All Deployments Restarted!"
echo "========================================="
echo ""
