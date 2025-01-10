kind delete cluster
kind create cluster --config ./KubernetesConfigs/00-cluster-config.yaml
kubectl apply -f ./KubernetesConfigs/01-configMap.yaml
kubectl apply -f ./KubernetesConfigs/02-postgres-pv.yaml 
kubectl apply -f ./KubernetesConfigs/03-postgres-pvc.yaml 
kubectl apply -f ./KubernetesConfigs/04-postgres-pod.yaml
kubectl apply -f ./KubernetesConfigs/05-postgres-ClusterIP.yaml 
kubectl apply -f ./KubernetesConfigs/06-api-pod.yaml
kubectl apply -f ./KubernetesConfigs/07-api-NodePort.yaml

# make sure auth-pod starts only when the other two pods are up
Start-Sleep -Seconds 10
kubectl apply -f ./KubernetesConfigs/08-auth-pod.yaml 
kubectl apply -f ./KubernetesConfigs/09-auth-ClusterIP.yaml

Write-Output "Cluster created!"
kubectl get all -o wide
