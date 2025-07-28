# We start with disabling swap
sudo swapoff -a
apt install -y apt-transport-https ca-certificates curl gpg
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' > /etc/apt/sources.list.d/kubernetes.list

sudo sysctl -w net.ipv4.ip_forward=1

apt update && apt install -y kubelet kubeadm
apt-mark hold kubelet kubeadm
kubeadm init --pod-network-cidr=10.244.0.0/16
systemctl restart kubelet

apt update && apt install -y containerd
mkdir /etc/containerd
containerd config default > /etc/containerd/config.toml
sed -i -e "s/SystemdCgroup = false/SystemdCgroup = true/g" /etc/containerd/config.toml
systemctl restart containerd

sudo modprobe br_netfilter

kubeadm token create --print-join-command
echo "Please run the above command on all worker nodes (after running the worker.sh script) to join them to the cluster."