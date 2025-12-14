#!/bin/bash

# Add all the necessary Helm repositories

helm repo add vm https://victoriametrics.github.io/helm-charts/
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add chaos-mesh https://charts.chaos-mesh.org

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

# Remove taints from master nodes to allow scheduling
kubectl taint nodes $(kubectl get nodes --selector=node-role.kubernetes.io/master | awk 'FNR==2{print $1}') node-role.kubernetes.io/master-
kubectl taint nodes $(kubectl get nodes --selector=node-role.kubernetes.io/master | awk 'FNR==2{print $1}') node-role.kubernetes.io/control-plane:NoSchedule-

# Install the monitoring stack on the master node
kubectl apply -f monitoring/grafana-dashboards/dashboard.yaml -n monitoring
helm upgrade --install vms vm/victoria-metrics-single -f monitoring/vm-values.yaml --set server.nodeSelector.nodeSelectorLabel="master" --namespace="monitoring" --create-namespace
helm upgrade --install prometheus prometheus-community/prometheus -f monitoring/prometheus-values.yaml --set prometheus.server.nodeSelector.nodeSelectorLabel="master" --namespace="monitoring" --create-namespace
helm upgrade --install grafana grafana/grafana -f monitoring/grafana-values.yaml --set nodeSelector.nodeSelectorLabel="master" --namespace="monitoring" --create-namespace

# Set up monitoring to be persistent

pv=$(kubectl get pvc -l app.kubernetes.io/instance=prometheus --namespace=monitoring -o yaml | grep volumeName | awk '{print $2}')
kubectl patch pv $pv -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'
pv=$(kubectl get pvc -l app.kubernetes.io/instance=vms --namespace=monitoring -o yaml | grep volumeName | awk '{print $2}')
kubectl patch pv $pv -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'

# loop from 1 to $replicas
# by default schedule nanopubs only to worker nodes

# Create a joined string of registry peer URLs

joined=""
for i in $(seq 1 $replicas); do
    joined+="http://nanopub-$i-registry-application:9292/"
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

# Change networking to ipvs and restart kube-proxy (we have to do this to enable round robin load balancing)
kubectl get configmap kube-proxy -n kube-system -o json | \
jq --arg newconf "$(cat <<EOF
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: ipvs
ipvs:
  strictARP: true
  scheduler: rr
EOF
)" '.data["config.conf"] = $newconf' | \
kubectl apply -f -

echo "Restarting kube-proxy pods..."
 kubectl delete pod -n kube-system -l k8s-app=kube-proxy


# Apply the general services for registry and query

kubectl apply -f setup-files/general-query-service.yaml
kubectl apply -f setup-files/general-registry-service.yaml

# Install Chaos Mesh for testing
# If you do not use containerd, change the socketPath accordingly

helm upgrade --install --set chaosDaemon.runtime=containerd --set chaosDaemon.socketPath=/run/containerd/containerd.sock --set dashboard.securityMode=false chaos-mesh chaos-mesh/chaos-mesh --namespace=chaos-mesh --set installCRDs=true --create-namespace
