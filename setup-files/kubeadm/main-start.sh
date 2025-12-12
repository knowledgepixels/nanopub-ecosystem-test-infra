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
sudo chmod 777 /etc/containerd/config.toml
sudo sed -i 's/            SystemdCgroup = false/            SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl restart containerd

# Here, the control plane endpoint is set to a specific private IP of the master node
sudo kubeadm init --control-plane-endpoint 192.168.8.22

# To set up kubectl to work properly
mkdir -p $HOME/.kube
sudo cp /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

kubeadm token create --print-join-command
echo "Please run the above command on all worker nodes (after running the worker.sh script) to join them to the cluster."