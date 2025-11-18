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
    echo "Deploying Portainer Agent..."
    echo ""
    
    # Deploy Portainer Agent
    curl -L https://downloads.portainer.io/ce2-21/portainer-agent-k8s-nodeport.yaml -o /tmp/portainer-agent.yaml && kubectl apply -f /tmp/portainer-agent.yaml
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Portainer Agent deployed!"
        echo ""
        echo "Waiting for pods to be ready..."
        sleep 10
        echo ""
        echo "Current resources in default namespace:"
        kubectl get all -n default -o wide
        echo ""
        echo "Persistent Volumes and Claims:"
        kubectl get pv,pvc -n default
        echo ""
        echo "========================================="
        echo "  🎯 Portainer Agent Connection Info"
        echo "========================================="
        echo ""
        echo "Use this address in Portainer UI:"
        echo ""
        AGENT_ADDRESS=$(kubectl get service portainer-agent -n portainer -o jsonpath='{.spec.clusterIP}:{.spec.ports[0].port}' 2>/dev/null)
        if [ -n "$AGENT_ADDRESS" ]; then
            echo "  $AGENT_ADDRESS"
        else
            echo "  (Waiting for service to be ready...)"
            sleep 3
            AGENT_ADDRESS=$(kubectl get service portainer-agent -n portainer -o jsonpath='{.spec.clusterIP}:{.spec.ports[0].port}')
            echo "  $AGENT_ADDRESS"
        fi
        echo ""
        echo "========================================="
    else
        echo "⚠️  Failed to deploy Portainer Agent, but main manifests are deployed"
    fi
else
    echo "❌ Failed to apply manifests"
    exit 1
fi

