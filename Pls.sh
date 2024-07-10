#!/bin/bash

NAMESPACE=$1
PVC_NAME=$2

if [ -z "$NAMESPACE" ] || [ -z "$PVC_NAME" ]; then
  echo "Usage: $0 <namespace> <pvc-name>"
  exit 1
fi

echo "Searching for controllers that might have used PVC: $PVC_NAME in namespace: $NAMESPACE"

# Check StatefulSets
STATEFULSETS=$(kubectl get statefulsets -n $NAMESPACE -o json | jq -r ".items[] | select(.spec.volumeClaimTemplates[]?.metadata.name == \"$PVC_NAME\" or .spec.template.spec.volumes[]?.persistentVolumeClaim.claimName == \"$PVC_NAME\") | .metadata.name")

for sts in $STATEFULSETS; do
  # Extract the potential StatefulSet name and ordinal from the PVC name
  if [[ "$PVC_NAME" == *"$sts"* ]]; then
    ORDINAL=$(echo "$PVC_NAME" | grep -oE '[0-9]+$')
    POD_NAME="${sts}-${ORDINAL}"
    echo "PVC $PVC_NAME was used by StatefulSet $sts and Pod $POD_NAME"
  fi
done

# Check Deployments
DEPLOYMENTS=$(kubectl get deployments -n $NAMESPACE -o json | jq -r ".items[] | select(.spec.template.spec.volumes[]?.persistentVolumeClaim.claimName == \"$PVC_NAME\") | .metadata.name")

for dep in $DEPLOYMENTS; do
  # Extract the potential Deployment name and ordinal from the PVC name
  if [[ "$PVC_NAME" == *"$dep"* ]]; then
    ORDINAL=$(echo "$PVC_NAME" | grep -oE '[0-9]+$')
    POD_NAME="${dep}-${ORDINAL}"
    echo "PVC $PVC_NAME was used by Deployment $dep and Pod $POD_NAME"
  fi
done

# Check ReplicaSets
REPLICASETS=$(kubectl get replicasets -n $NAMESPACE -o json | jq -r ".items[] | select(.spec.template.spec.volumes[]?.persistentVolumeClaim.claimName == \"$PVC_NAME\") | .metadata.name")

for rs in $REPLICASETS; do
  if [[ "$PVC_NAME" == *"$rs"* ]]; then
    ORDINAL=$(echo "$PVC_NAME" | grep -oE '[0-9]+$')
    POD_NAME="${rs}-${ORDINAL}"
    echo "PVC $PVC_NAME was used by ReplicaSet $rs and Pod $POD_NAME"
  fi
done

# Check DaemonSets
DAEMONSETS=$(kubectl get daemonsets -n $NAMESPACE -o json | jq -r ".items[] | select(.spec.template.spec.volumes[]?.persistentVolumeClaim.claimName == \"$PVC_NAME\") | .metadata.name")

for ds in $DAEMONSETS; do
  if [[ "$PVC_NAME" == *"$ds"* ]]; then
    echo "PVC $PVC_NAME was used by DaemonSet $ds"
  fi
done

# Final output if no matches found
if [ -z "$STATEFULSETS" ] && [ -z "$DEPLOYMENTS" ] && [ -z "$REPLICASETS" ] && [ -z "$DAEMONSETS" ]; then
  echo "No controllers found that match PVC: $PVC_NAME in namespace: $NAMESPACE"
fi
