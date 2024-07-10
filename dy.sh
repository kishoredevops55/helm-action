#!/bin/bash

NAMESPACE=$1
PVC_NAME=$2

if [ -z "$NAMESPACE" ] || [ -z "$PVC_NAME" ]; then
  echo "Usage: $0 <namespace> <pvc-name>"
  exit 1
fi

# Extract the StatefulSet name and ordinal from the PVC name
IFS='-' read -r _ STATEFULSET_NAME ORDINAL <<< "${PVC_NAME#*-}"

if [ -z "$STATEFULSET_NAME" ] || [ -z "$ORDINAL" ]; then
  echo "PVC name $PVC_NAME does not match the expected format"
  exit 1
fi

# Check if the StatefulSet exists in the namespace
STS_EXISTS=$(kubectl get statefulsets -n $NAMESPACE | grep -w $STATEFULSET_NAME)
if [ -z "$STS_EXISTS" ]; then
  echo "StatefulSet $STATEFULSET_NAME not found in namespace $NAMESPACE"
  exit 1
fi

# Derive the pod name from the StatefulSet name and ordinal
POD_NAME="${STATEFULSET_NAME}-${ORDINAL}"

# Check if the pod exists (if it's deleted, this might not return anything)
POD_EXISTS=$(kubectl get pods -n $NAMESPACE | grep -w $POD_NAME)
if [ -z "$POD_EXISTS" ]; then
  echo "Pod $POD_NAME not found in namespace $NAMESPACE"
else
  echo "Pod $POD_NAME was created by StatefulSet $STATEFULSET_NAME and used PVC $PVC_NAME"
fi

echo "StatefulSet: $STATEFULSET_NAME"
echo "Pod: $POD_NAME"
