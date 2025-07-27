sudo swapoff -a
systemctl restart kubelet
sudo sysctl -w net.ipv4.ip_forward=1

# Here, use the join command printed by kubeadm init on the master node