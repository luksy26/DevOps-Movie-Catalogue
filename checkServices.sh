#!/bin/bash

echo "========================================="
echo "  Service Status Check"
echo "========================================="
echo ""

echo "📊 Checking all pods..."
kubectl get pods -o wide

echo ""
echo "========================================="
echo ""

echo "🔍 Checking services..."
kubectl get services

echo ""
echo "========================================="
echo ""

echo "📝 Checking deployments..."
kubectl get deployments

echo ""
echo "========================================="
echo ""

echo "🔎 Checking if recommendation-service exists..."
kubectl get service recommendation-service 2>/dev/null && echo "✅ Recommendation service exists" || echo "❌ Recommendation service NOT FOUND"

echo ""
echo "🔎 Checking if review-service exists..."
kubectl get service review-service 2>/dev/null && echo "✅ Review service exists" || echo "❌ Review service NOT FOUND"

echo ""
echo "========================================="
echo ""

echo "📋 Recent events:"
kubectl get events --sort-by='.lastTimestamp' | tail -15

echo ""
echo "========================================="
echo ""

# Check if recommendation deployment exists
RECOMMENDATION_POD=$(kubectl get pods -l app=recommendation -o name 2>/dev/null | head -1)
if [ -n "$RECOMMENDATION_POD" ]; then
    echo "✅ Recommendation pod found: $RECOMMENDATION_POD"
    echo "Logs:"
    kubectl logs $RECOMMENDATION_POD --tail=20
else
    echo "❌ No recommendation pod found"
    echo "To create it, the deployment manifest needs to be applied."
fi

echo ""
echo "========================================="
echo ""

# Check if review deployment exists
REVIEW_POD=$(kubectl get pods -l app=review -o name 2>/dev/null | head -1)
if [ -n "$REVIEW_POD" ]; then
    echo "✅ Review pod found: $REVIEW_POD"
    echo "Logs:"
    kubectl logs $REVIEW_POD --tail=20
else
    echo "❌ No review pod found"
    echo "To create it, the deployment manifest needs to be applied."
fi

echo ""
echo "========================================="
echo ""

echo "💡 Quick fixes:"
echo ""
echo "If services are missing, apply the manifests:"
echo "  kubectl apply -f KubernetesConfigs/16-recommendation-deployment.yaml"
echo "  kubectl apply -f KubernetesConfigs/17-recommendation-ClusterIP.yaml"
echo "  kubectl apply -f KubernetesConfigs/18-review-deployment.yaml"
echo "  kubectl apply -f KubernetesConfigs/19-review-ClusterIP.yaml"
echo ""
echo "Or use terraform:"
echo "  cd terraform-infra && terraform apply"
echo ""
