#!/bin/bash

# Script to deploy Portainer Agent and show connection info

echo "========================================="
echo "  Deploying Portainer Agent"
echo "========================================="
echo ""

# Download and apply Portainer Agent manifest
curl -L https://downloads.portainer.io/ce2-21/portainer-agent-k8s-nodeport.yaml -o /tmp/portainer-agent.yaml

if [ $? -eq 0 ]; then
    echo ""
    echo "Applying Portainer Agent manifest..."
    kubectl apply -f /tmp/portainer-agent.yaml
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Portainer Agent deployed successfully!"
        echo ""
        echo "Waiting for agent to be ready..."
        sleep 5
        echo ""
        
        # Show agent pod status
        echo "Agent Pod Status:"
        kubectl get pods -n portainer -l app=portainer-agent
        echo ""
        
        # Show service info
        echo "Agent Service:"
        kubectl get svc portainer-agent -n portainer
        echo ""
        
        # Get and display the agent address
        echo "========================================="
        echo "  🎯 Portainer Agent Connection Info"
        echo "========================================="
        echo ""
        echo "To connect Portainer to your Kubernetes cluster:"
        echo ""
        echo "1. Open Portainer UI: http://localhost:30002"
        echo "2. Add new environment"
        echo "3. Select 'Agent'"
        echo "4. Use this address:"
        echo ""
        
        AGENT_ADDRESS=$(kubectl get service portainer-agent -n portainer -o jsonpath='{.spec.clusterIP}:{.spec.ports[0].port}' 2>/dev/null)
        
        if [ -n "$AGENT_ADDRESS" ]; then
            echo "    $AGENT_ADDRESS"
        else
            echo "    (Service not ready yet, waiting...)"
            sleep 3
            AGENT_ADDRESS=$(kubectl get service portainer-agent -n portainer -o jsonpath='{.spec.clusterIP}:{.spec.ports[0].port}')
            echo "    $AGENT_ADDRESS"
        fi
        
        echo ""
        echo "========================================="
        echo ""
    else
        echo "❌ Failed to apply Portainer Agent manifest"
        exit 1
    fi
else
    echo "❌ Failed to download Portainer Agent manifest"
    exit 1
fi

