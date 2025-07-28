# Here, start the worker nodes with the join command printed above
# Remember to do it before you install the CNI plugin

helm repo add cilium https://helm.cilium.io/
helm install cilium cilium/cilium --version 1.17.6 --namespace kube-system

# install cilium CLI

CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
CLI_ARCH=amd64
if [ "$(uname -m)" = "aarch64" ]; then CLI_ARCH=arm64; fi
curl -L --fail --remote-name-all https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}
sha256sum --check cilium-linux-${CLI_ARCH}.tar.gz.sha256sum
sudo tar xzvfC cilium-linux-${CLI_ARCH}.tar.gz /usr/local/bin
rm cilium-linux-${CLI_ARCH}.tar.gz{,.sha256sum}

systemctl restart containerd
systemctl restart kubectl

helm install openebs openebs/openebs   --set engines.replicated.mayastor.enabled=false  --set loki.minio.persistence.enabled=false --set loki.localpvScConfig.enabled=false --set engines.local.lvm.enabled=false   --set engines.local.zfs.enabled=false   --namespace openebs   --create-namespace

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

# Install MetalLB for load balancing
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.15.2/config/manifests/metallb-native.yaml

# Configure MetalLB with a range of IPs - you can change this to your needs
kubectl apply -f ./metallb-config.yaml
kubectl apply -f ./metal-l2-ad.yaml