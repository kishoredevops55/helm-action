#!/bin/bash

NAMESPACE=$1
PVC_NAME=$2

if [ -z "$NAMESPACE" ] || [ -z "$PVC_NAME" ]; then
  echo "Usage: $0 <namespace> <pvc-name>"
  exit 1
fi

# Extract the StatefulSet or Deployment name and ordinal from the PVC name
IFS='-' read -r _ CONTROLLER_NAME ORDINAL <<< "${PVC_NAME#*-}"

if [ -z "$CONTROLLER_NAME" ] || [ -z "$ORDINAL" ]; then
  echo "PVC name $PVC_NAME does not match the expected format"
  exit 1
fi

# Check StatefulSets
echo "Checking StatefulSets in namespace: $NAMESPACE for PVC: $PVC_NAME"
STATEFULSETS=$(kubectl get statefulsets -n $NAMESPACE -o json | jq -r ".items[] | select(.spec.volumeClaimTemplates[]?.metadata.name == \"$PVC_NAME\" or .spec.template.spec.volumes[]?.persistentVolumeClaim.claimName == \"$PVC_NAME\") | .metadata.name")

for sts in $STATEFULSETS; do
  if [[ "$PVC_NAME" == *"$sts"* ]]; then
    POD_NAME="${sts}-${ORDINAL}"
    echo "PVC $PVC_NAME was used by StatefulSet $sts and Pod $POD_NAME"
  fi
done

# Check Deployments
echo "Checking Deployments in namespace: $NAMESPACE for PVC: $PVC_NAME"
DEPLOYMENTS=$(kubectl get deployments -n $NAMESPACE -o json | jq -r ".items[] | select(.spec.template.spec.volumes[]?.persistentVolumeClaim.claimName == \"$PVC_NAME\") | .metadata.name")

for dep in $DEPLOYMENTS; do
  if [[ "$PVC_NAME" == *"$dep"* ]]; then
    # Infer pod name (assuming standard naming conventions)
    POD_NAME="${dep}-${ORDINAL}"
    echo "PVC $PVC_NAME was used by Deployment $dep and Pod $POD_NAME"
  fi
done

# Note: The above inference assumes that the naming pattern is closely followed.
# If the naming pattern is different, additional logic might be needed.
