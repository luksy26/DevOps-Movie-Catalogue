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
echo "Restarting Recommendation deployment..."
kubectl rollout restart deployment recommendation-deployment
if [ $? -ne 0 ]; then
    echo "❌ Failed to restart Recommendation deployment"
    exit 1
fi

echo ""
echo "Restarting Review deployment..."
kubectl rollout restart deployment review-deployment
if [ $? -ne 0 ]; then
    echo "❌ Failed to restart Review deployment"
    exit 1
fi

echo ""
echo "Waiting for deployments to be ready (timeout: 2 minutes)..."
kubectl rollout status deployment api-deployment --timeout=120s || echo "⚠️  API deployment taking longer than expected"
kubectl rollout status deployment auth-deployment --timeout=120s || echo "⚠️  Auth deployment taking longer than expected"
kubectl rollout status deployment catalogue-deployment --timeout=120s || echo "⚠️  Catalogue deployment taking longer than expected"
kubectl rollout status deployment recommendation-deployment --timeout=120s || echo "⚠️  Recommendation deployment taking longer than expected"
kubectl rollout status deployment review-deployment --timeout=120s || echo "⚠️  Review deployment taking longer than expected"

echo ""
echo "========================================="
echo "  ✅ All Deployments Restarted!"
echo "========================================="
echo ""
