#!/bin/bash

# Troubleshooting script for stuck deployments

echo "========================================="
echo "  Deployment Troubleshooting"
echo "========================================="
echo ""

echo "📊 Checking pod status..."
kubectl get pods -l app=api
kubectl get pods -l app=auth
kubectl get pods -l app=catalogue

echo ""
echo "========================================="
echo ""

echo "🔍 Checking for pending/failed pods..."
kubectl get pods --field-selector=status.phase!=Running,status.phase!=Succeeded

echo ""
echo "========================================="
echo ""

echo "📝 Recent pod events..."
kubectl get events --sort-by='.lastTimestamp' | tail -20

echo ""
echo "========================================="
echo ""

echo "🎯 Checking deployment status..."
kubectl get deployments

echo ""
echo "========================================="
echo ""

# Check for stuck terminating pods
TERMINATING=$(kubectl get pods --field-selector=status.phase=Terminating 2>/dev/null | tail -n +2)
if [ -n "$TERMINATING" ]; then
    echo "⚠️  Found terminating pods:"
    echo "$TERMINATING"
    echo ""
    echo "To force delete these pods, run:"
    echo "  kubectl delete pod <pod-name> --grace-period=0 --force"
    echo ""
fi

# Check for ImagePullBackOff or CrashLoopBackOff
PROBLEM_PODS=$(kubectl get pods | grep -E 'ImagePullBackOff|CrashLoopBackOff|Error' || true)
if [ -n "$PROBLEM_PODS" ]; then
    echo "❌ Found pods with issues:"
    echo "$PROBLEM_PODS"
    echo ""
    echo "To see details, run:"
    echo "  kubectl describe pod <pod-name>"
    echo "  kubectl logs <pod-name>"
    echo ""
fi

echo "========================================="
echo ""
echo "💡 Common fixes:"
echo "  1. Force delete stuck pods:"
echo "     kubectl delete pod <pod-name> --grace-period=0 --force"
echo ""
echo "  2. Restart all deployments:"
echo "     kubectl rollout restart deployment api-deployment"
echo "     kubectl rollout restart deployment auth-deployment"
echo "     kubectl rollout restart deployment catalogue-deployment"
echo ""
echo "  3. Check image availability:"
echo "     docker pull lucaslazaroiu/ccproject:api-service"
echo "     docker pull lucaslazaroiu/ccproject:auth-service"
echo "     docker pull lucaslazaroiu/ccproject:catalogue-service"
echo ""
echo "  4. Delete and recreate deployments:"
echo "     cd terraform-infra"
echo "     terraform destroy -target=kubernetes_manifest.all_manifests"
echo "     terraform apply"
echo ""
