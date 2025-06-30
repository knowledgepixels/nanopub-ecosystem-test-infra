#!/bin/bash

# Change the storage provisioner to support multi-node setups and dynamically wait for pods
# Before assigning the storage class

minikube addons enable volumesnapshots -p dem
minikube addons enable csi-hostpath-driver -p dem
minikube addons disable storage-provisioner -p dem
minikube addons disable default-storageclass -p dem
kubectl patch storageclass standard -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
kubectl apply -f setup-files/storage.yaml

# Add all the necessary Helm repositories

helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts


replicas=$1

# Find all master nodes and label them

master=($(kubectl get nodes -l node-role.kubernetes.io/control-plane -o jsonpath='{.items[*].metadata.name}'))
for node in "${master[@]}"; do
  echo "Master node: $node"
  kubectl label node $node --overwrite nodeSelectorLabel="master"
done

# Find all worker nodes and label them

workers=($(kubectl get nodes -l '!node-role.kubernetes.io/control-plane' -o jsonpath='{.items[*].metadata.name}'))
for (( i=1; i<${#workers[@]}+1; i++ )); do
  index=$((i - 1))
  echo "Labeling worker node ${workers[$index]} with nodeSelectorLabel=worker-$((i))"
  kubectl label node ${workers[$index]} --overwrite nodeSelectorLabel="worker-$((i))"
done

if [ -z "$replicas" ]; then
  echo "Usage: $0 <number_of_replicas>"
  exit 1
fi

# Install the monitoring stack on the master node

helm upgrade --install vms vm/victoria-metrics-single -f monitoring/vm-values.yaml --set server.nodeSelector.nodeSelectorLabel="master"
helm upgrade --install prometheus prometheus-community/prometheus -f monitoring/prometheus-values.yaml --set kube-state-metrics.enabled="false" --set prometheus.server.nodeSelector.nodeSelectorLabel="master"
helm upgrade --install grafana grafana/grafana -f monitoring/grafana-values.yaml --set nodeSelector.nodeSelectorLabel="master"

# loop from 1 to $replicas
# by default schedule nanopubs only to worker nodes

# Create a joined string of registry peer URLs

joined=""
for i in $(seq 1 $replicas); do
    joined+="http://nanopub-$i-registry-application:9292"
    if [ $i -lt $replicas ]; then
        joined+=";"
    fi
done

echo "$joined"

# Create nanopub instances on worker nodes

for i in $(seq 1 $replicas); do
  echo "Creating replica $i"
  helm upgrade --install nanopub-$i helm-chart --set global.nodeSelectorLabel="worker-$((i))" --set registry.application.registryPeerUrls="$joined"
done

# Apply the general services for registry and query

kubectl apply -f setup-files/general-query-service.yaml
kubectl apply -f setup-files/general-registry-service.yaml