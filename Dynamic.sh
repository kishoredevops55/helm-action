#!/bin/bash

NAMESPACE=$1
PVC_NAME=$2

if [ -z "$NAMESPACE" ] || [ -z "$PVC_NAME" ]; then
  echo "Usage: $0 <namespace> <pvc-name>"
  exit 1
fi

# Function to check if a controller uses the PVC
check_controller() {
  CONTROLLER_TYPE=$1
  CONTROLLERS=$(kubectl get $CONTROLLER_TYPE -n $NAMESPACE -o json | jq -r ".items[] | select(.spec.volumeClaimTemplates[]?.metadata.name == \"$PVC_NAME\" or .spec.template.spec.volumes[]?.persistentVolumeClaim.claimName == \"$PVC_NAME\") | .metadata.name")
  
  if [ -n "$CONTROLLERS" ]; then
    echo "PVC $PVC_NAME might have been used by the following $CONTROLLER_TYPE(s):"
    echo "$CONTROLLERS"
  else
    echo "No $CONTROLLER_TYPE found using PVC: $PVC_NAME"
  fi
}

# Check StatefulSets
echo "Checking StatefulSets in namespace: $NAMESPACE for PVC: $PVC_NAME"
check_controller "statefulsets"

# Check Deployments
echo "Checking Deployments in namespace: $NAMESPACE for PVC: $PVC_NAME"
check_controller "deployments"

# Check DaemonSets
echo "Checking DaemonSets in namespace: $NAMESPACE for PVC: $PVC_NAME"
check_controller "daemonsets"

# Check ReplicaSets
echo "Checking ReplicaSets in namespace: $NAMESPACE for PVC: $PVC_NAME"
check_controller "replicasets"

# Check Pods directly (in case they are not managed by a controller)
echo "Checking Pods in namespace: $NAMESPACE for PVC: $PVC_NAME"
PODS=$(kubectl get pods -n $NAMESPACE -o json | jq -r ".items[] | select(.spec.volumes[]?.persistentVolumeClaim.claimName == \"$PVC_NAME\") | .metadata.name")
if [ -n "$PODS" ]; then
  echo "PVC $PVC_NAME was used by the following Pods:"
  echo "$PODS"
else
  echo "No Pods found using PVC: $PVC_NAME"
fi
