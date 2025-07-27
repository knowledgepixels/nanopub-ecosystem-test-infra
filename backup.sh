#!/bin/bash

# Directory to store backups
BACKUP_DIR="k8s-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Backing up cluster to $BACKUP_DIR ..."

# Cluster-scoped resources
CLUSTER_RESOURCES=(
  nodes
  persistentvolumes
  clusterroles
  clusterrolebindings
  customresourcedefinitions
  storageclasses
  priorityclasses
  mutatingwebhookconfigurations
  validatingwebhookconfigurations
  apiservices
)

# Namespaced resources to include
NAMESPACED_RESOURCES=(
  pods
  deployments
  services
  configmaps
  secrets
  daemonsets
  statefulsets
  jobs
  cronjobs
  serviceaccounts
  roles
  rolebindings
  persistentvolumeclaims
  networkpolicies
  ingresses
)

# Backup cluster-scoped resources
echo "Backing up cluster-scoped resources..."
for resource in "${CLUSTER_RESOURCES[@]}"; do
  echo "  - $resource"
  kubectl get "$resource" -o yaml > "$BACKUP_DIR/cluster-${resource}.yaml" 2>/dev/null
done

# Get all namespaces
NAMESPACES=$(kubectl get ns -o jsonpath='{.items[*].metadata.name}')

# Backup namespaced resources
for ns in $NAMESPACES; do
  echo "Backing up namespace: $ns"
  mkdir -p "$BACKUP_DIR/namespaces/$ns"
  for resource in "${NAMESPACED_RESOURCES[@]}"; do
    echo "  - $resource"
    kubectl get "$resource" -n "$ns" -o yaml > "$BACKUP_DIR/namespaces/$ns/${resource}.yaml" 2>/dev/null
  done
done

echo "✅ Backup completed in: $BACKUP_DIR"
