# Remember to start the cluster with the right ulimits (Chaos-Mesh requires higher ulimits)
minikube start -p dem --nodes=3 --docker-opt default-ulimits=nofile=65536:65536

# Install chaos-mesh for chaos engineering experiments
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm install chaos-mesh chaos-mesh/chaos-mesh --namespace=chaos-mesh --create-namespace
