kind delete cluster

kind create cluster --config ./KubernetesConfigs/00-cluster-config.yaml

kubectl apply -f ./KubernetesConfigs/01-configMap.yaml
kubectl apply -f ./KubernetesConfigs/02-postgres-pv.yaml 
kubectl apply -f ./KubernetesConfigs/03-postgres-pvc.yaml 
kubectl apply -f ./KubernetesConfigs/04-postgres-deployment.yaml
kubectl apply -f ./KubernetesConfigs/05-postgres-ClusterIP.yaml
kubectl apply -f ./KubernetesConfigs/05.1-postgres-NodePort.yaml 
kubectl apply -f ./KubernetesConfigs/06-api-deployment.yaml
kubectl apply -f ./KubernetesConfigs/07-api-NodePort.yaml
kubectl apply -f ./KubernetesConfigs/08-auth-deployment.yaml 
kubectl apply -f ./KubernetesConfigs/09-auth-ClusterIP.yaml
kubectl apply -f ./KubernetesConfigs/10-catalogue-deployment.yaml
kubectl apply -f ./KubernetesConfigs/11-catalogue-ClusterIP.yaml
kubectl apply -f ./KubernetesConfigs/12-portainer-pvc.yaml
kubectl apply -f ./KubernetesConfigs/13-portainer-deployment.yaml
kubectl apply -f ./KubernetesConfigs/14-portainer-NodePort.yaml

Write-Output "Cluster created!"
kubectl get all -o wide
