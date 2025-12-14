# We start with disabling swap
sudo swapoff -a
# We make it permanent by modifying /etc/fstab
sudo sed -i.bak '/\sswap\s/s/^/#/' /etc/fstab

# We set up rules about forwarding to enable proper functioning of networking in the cluster

sudo modprobe br_netfilter
sudo modprobe overlay

sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl -w net.bridge.bridge-nf-call-iptables=1
sudo sysctl -w net.bridge.bridge-nf-call-ip6tables=1

sudo apt-get update
# apt-transport-https may be a dummy package; if so, you can skip that package
# This is just the installation script from the main kubernetes website
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.34/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
sudo chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg # allow unprivileged APT programs to read this keyring
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.34/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo chmod 644 /etc/apt/sources.list.d/kubernetes.list   # helps tools such as command-not-found to work correctly
sudo apt-get update
sudo apt-get install -y kubectl
sudo apt-get install -y kubeadm
sudo apt-get install -y kubelet

systemctl restart kubelet

apt update && apt install -y containerd
sudo mkdir /etc/containerd
sudo containerd config default | sudo tee /etc/containerd/config.toml
sudo chmod 644 /etc/containerd/config.toml
sudo sed -i 's/            SystemdCgroup = false/            SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl restart containerd

# Here, use the join command printed by kubeadm init on the master node