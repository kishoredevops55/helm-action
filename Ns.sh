#!/bin/bash

# Check if a namespace is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <namespace>"
    exit 1
fi

# Set the namespace
NAMESPACE=$1

# Change the current context's namespace
kubectl config set-context --current --namespace="$NAMESPACE"

# Verify the change
CURRENT_NS=$(kubectl config view --minify --output 'jsonpath={..namespace}')
echo "Switched to namespace: $CURRENT_NS"
