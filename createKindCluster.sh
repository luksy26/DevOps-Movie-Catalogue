#!/bin/bash

# Script to create a new kind cluster with configuration

echo "Creating kind cluster..."
kind create cluster --config 00-cluster-config.yaml

if [ $? -eq 0 ]; then
    echo "✅ Kind cluster created successfully!"
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

