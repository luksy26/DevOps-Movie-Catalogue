kind delete cluster
kind create cluster --config 00-cluster-config.yaml

Write-Output "Kind Cluster created!"

kubectl cluster-info --context kind-kind
