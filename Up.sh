#!/bin/bash

NAMESPACE=$1
PVC_NAME=$2

if [ -z "$NAMESPACE" ] || [ -z "$PVC_NAME" ]; then
  echo "Usage: $0 <namespace> <pvc-name>"
  exit 1
fi

echo "Searching for the deleted pod that might have used PVC: $PVC_NAME in namespace: $NAMESPACE"

# Extract the controller name and ordinal from the PVC name
# Assuming the PVC name format is "data-<controller-name>-<ordinal>"
IFS='-' read -r PREFIX CONTROLLER_NAME ORDINAL <<< "${PVC_NAME}"

# Check if the extracted values are valid
if [ -z "$CONTROLLER_NAME" ] || [ -z "$ORDINAL" ]; then
  echo "PVC name $PVC_NAME does not match the expected format"
  exit 1
fi

# Check StatefulSets
STATEFULSETS=$(kubectl get statefulsets -n $NAMESPACE -o json | jq -r ".items[] | select(.metadata.name == \"$CONTROLLER_NAME\") | .metadata.name")

for sts in $STATEFULSETS; do
  if [[ "$PVC_NAME" == *"$sts"* ]]; then
    POD_NAME="${sts}-${ORDINAL}"
    echo "PVC $PVC_NAME was likely used by StatefulSet $sts and Pod $POD_NAME"
  fi
done

# Check Deployments and their ReplicaSets
DEPLOYMENTS=$(kubectl get deployments -n $NAMESPACE -o json | jq -r ".items[] | select(.metadata.name == \"$CONTROLLER_NAME\") | .metadata.name")

for dep in $DEPLOYMENTS; do
  if [[ "$PVC_NAME" == *"$dep"* ]]; then
    REPLICASETS=$(kubectl get replicasets -n $NAMESPACE -l "app=$dep" -o json | jq -r '.items[] | .metadata.name')
    for rs in $REPLICASETS; do
      if [[ "$PVC_NAME" == *"$rs"* ]]; then
        POD_NAME="${rs}-${ORDINAL}"
        echo "PVC $PVC_NAME was likely used by ReplicaSet $rs and Pod $POD_NAME (Deployment $dep)"
      fi
    done
  fi
done

# Final output if no matches found
if [ -z "$STATEFULSETS" ] && [ -z "$DEPLOYMENTS" ]; then
  echo "No StatefulSets or Deployments found that match PVC: $PVC_NAME in namespace: $NAMESPACE"
fi
