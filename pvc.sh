#!/bin/bash

NAMESPACE=$1
PVC_NAME=$2

if [ -z "$NAMESPACE" ] || [ -z "$PVC_NAME" ]; then
  echo "Usage: $0 <namespace> <pvc-name>"
  exit 1
fi

echo "Searching for pods that used PVC: $PVC_NAME in namespace: $NAMESPACE"
PODS=$(kubectl get pods -n $NAMESPACE -o json | jq -r ".items[] | select(.spec.volumes[]?.persistentVolumeClaim.claimName == \"$PVC_NAME\") | .metadata.name")

if [ -z "$PODS" ]; then
  echo "No pods found that used PVC: $PVC_NAME"
  exit 1
fi

for pod in $PODS; do
  echo "Pod: $pod"
  OWNER_KIND=$(kubectl get pod $pod -n $NAMESPACE -o jsonpath='{.metadata.ownerReferences[0].kind}')
  OWNER_NAME=$(kubectl get pod $pod -n $NAMESPACE -o jsonpath='{.metadata.ownerReferences[0].name}')
  echo "Owned by: $OWNER_KIND - $OWNER_NAME"
done
