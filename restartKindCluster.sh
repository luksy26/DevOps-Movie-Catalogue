#!/bin/bash

# Script to restart the kind cluster (delete and recreate)

echo "Deleting existing kind cluster..."
kind delete cluster

echo ""
echo "Creating new kind cluster..."
kind create cluster --config 00-cluster-config.yaml

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Kind cluster restarted successfully!"
    echo ""
    echo "Cluster info:"
    kubectl cluster-info --context kind-kind
    echo ""
    echo "Nodes:"
    kubectl get nodes
else
    echo "❌ Failed to create kind cluster"
    exit 1
fi

