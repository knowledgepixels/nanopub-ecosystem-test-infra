# Remember to start the cluster with the right ulimits (Chaos-Mesh requires higher ulimits)
minikube start -p dem --nodes=3 --docker-opt default-ulimits=nofile=65536:65536 --extra-config=kube-proxy.mode=ipvs

minikube addons enable volumesnapshots -p dem
minikube addons enable csi-hostpath-driver -p dem
minikube addons disable storage-provisioner -p dem
minikube addons disable default-storageclass -p dem
# Change the storage provisioner to support multi-node setups and dynamically wait for pods
# Before assigning the storage class

kubectl patch storageclass standard -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
kubectl apply -f ./storage.yaml
