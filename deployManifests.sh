#!/bin/bash

# Script to apply all Kubernetes manifests

echo "Applying all manifests from KubernetesConfigs/ ..."
echo ""

# Apply manifests in order (they are numbered for proper sequencing)
kubectl apply -f KubernetesConfigs/

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ All manifests applied successfully!"
    echo ""
    echo "Waiting for pods to be ready..."
    sleep 5
    echo ""
    echo "Current resources in default namespace:"
    kubectl get all -n default -o wide
    echo ""
    echo "Persistent Volumes and Claims:"
    kubectl get pv,pvc -n default
else
    echo "❌ Failed to apply manifests"
    exit 1
fi

