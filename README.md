This repository contains the test infrastructure configuration of the Nanopublication ecosystem.

### Main charts

The `helm-chart` directory contains separate subcharts for Query ( as `query`) and Registry ( as `registry`) instances. They can be deployed separately or as a part of the larger `nanopub` chart. If deployed as a part of the `nanopub` chart, both Query and Registry instances will be connected by default and can be configured to be deployed together on a separate node (through setting `global.nodeSelectorLabel` in the `helm-chart/values.yaml` file). 

`setup-files/general-query-service.yaml` and `setup-files/general-registry-service.yaml` specify overarching services that will connect to all Query instances and all Registry instances in the cluster regardless of the release. The services use the default Kubernetes load balancer of your distribution.  

To deploy them as is, run:

```
helm install nanopub helm-chart
kubectl apply -f general-query-service.yaml
kubectl apply -f general-registry-service.yaml
```

### Monitoring and visualization

Aside from the main chart, the repository contains a setup for monitoring and visualization consisting of Prometheus (used to scrape the metrics from Query and Registry instances), Victoria Metrics (used for persistent storage of these metrics) and Grafana (used to visualize the scraped metrics). 

To set it up, follow the instructions below.

Start by installing Victoria Metrics with the options predefined by running:

```
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm install vms vm/victoria-metrics-single -f monitoring/vm-values.yaml --namespace="monitoring" --create-namespace
```

By default, VM will run as a monolith, connect to the host machine on the node port `31333` and retain the data for 1 year. All of these options can be modified through changing the appropriate fields in `metrics/vm-values.yaml` and running

`helm upgrade --install vms vm/victoria-metrics-single -f metrics/vm-values.yaml --namespace="monitoring" --create-namespace` .

Then install Prometheus through:

```
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/prometheus -f monitoring/prometheus-values.yaml --namespace="monitoring" --create-namespace --set kube-state-metrics.enabled="false"
```

This should cause Prometheus to connect automatically to the `/metrics` endpoints exposed by the Registry and Query instances located in the same cluster, as well as to the VM instance configured before. Prometheus server will be available on the host machine on node port `31165`.

Finally, install Grafana with:

```
helm repo add grafana https://grafana.github.io/helm-charts
helm install grafana grafana/grafana -f monitoring/grafana-values.yaml --namespace="monitoring" --create-namespace
```

Grafana will automatically connect to the Prometheus and VM instances configured above. The dashboard will be exposed on the host machine on port `31430`. By default, authentication to the dashboard will be disabled. Grafana should be preloaded with select dashboards by default.

### Multi-node setup

All of the above can be automatically configured and deployed using the `multi-node-setup.sh` script. The script accepts one argument - the number of nanopub instances to deploy - and deploys each per worker node along with the preconfigured monitoring set up on the master node.

By default, the Registry instances are deployed in test mode - so that they do not propagate changes to the main nanopublication network. Peer URLs are generated automatically through the script.

```
./multi-node-setup.sh <replica-number>
```

The script also includes the installation and setup of a chaos emulation tool, `ChaosMesh`. The tool can be used to emulate networking problems in Kubernetes, including latency and bandwidth.

### Cluster setup

If you want to set up a Kubernetes cluster from scratch in a way that will be compatible with the testing infrastructure, or just want to check out how to modify your current configuration, look into `setup-files/minikube` and `setup-files/kubeadm` respectively. 

#### Minikube

Minikube requires minimal initial setup, but can be tough to work with more advanced Kubernetes configurations. To set it up for testing purposes, run `setup-files/minikube/setup.sh`.

#### Kubeadm

Kubeadm requires a more complex installation at the start, but is more flexible down the line. Here, a setup with `containerd` (container runtime), `cillium` (CNI plugin), and `MetalLB` (load balancer) is described. 

Please first make sure that the IPs specified in `setup-files/kubeadm/metal-config.yaml` fit into your setup - they need to belong to your LAN and be unused by other devices. Then run `setup-files/kubeadm/main-start.sh <CONTROL-PLANE-ENDPOINT-IP>` on the main node first, follow with `setup-files/kubeadm/worker.sh` on all the worker nodes to properly configure and connect them, and then finish by running `setup-files/kubeadm/main-end.sh` on the main node. 

## Backups

After successfully creating your cluster, you can back up your configuration by running `./backup.sh`. The script will create a directory with the YAML descriptions of all your Kubernetes resources.