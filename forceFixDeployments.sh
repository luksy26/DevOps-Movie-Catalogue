#!/bin/bash

# Force fix for stuck deployments

echo "========================================="
echo "  Force Fix Stuck Deployments"
echo "========================================="
echo ""

read -p "This will force delete all stuck pods. Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

echo ""
echo "Step 1: Force deleting any terminating pods..."
TERMINATING_PODS=$(kubectl get pods --field-selector=status.phase=Terminating -o name 2>/dev/null)
if [ -n "$TERMINATING_PODS" ]; then
    echo "$TERMINATING_PODS" | xargs -I {} kubectl delete {} --grace-period=0 --force
    echo "✅ Terminating pods deleted"
else
    echo "No terminating pods found"
fi

echo ""
echo "Step 2: Force deleting failed/errored pods..."
FAILED_PODS=$(kubectl get pods --field-selector=status.phase=Failed -o name 2>/dev/null)
if [ -n "$FAILED_PODS" ]; then
    echo "$FAILED_PODS" | xargs -I {} kubectl delete {}
    echo "✅ Failed pods deleted"
else
    echo "No failed pods found"
fi

echo ""
echo "Step 3: Scaling down deployments..."
kubectl scale deployment api-deployment --replicas=0
kubectl scale deployment auth-deployment --replicas=0
kubectl scale deployment catalogue-deployment --replicas=0

echo "Waiting for pods to terminate..."
sleep 5

echo ""
echo "Step 4: Scaling up deployments..."
kubectl scale deployment api-deployment --replicas=1
kubectl scale deployment auth-deployment --replicas=1
kubectl scale deployment catalogue-deployment --replicas=1

echo ""
echo "Step 5: Waiting for new pods to start..."
sleep 10

echo ""
echo "Current pod status:"
kubectl get pods

echo ""
echo "========================================="
echo "  ✅ Force fix complete!"
echo "========================================="
echo ""
echo "Check pod status with: kubectl get pods"
echo "If issues persist, run: ./troubleshootDeployments.sh"
echo ""
