#!/bin/bash

# Define the Helm chart directory
HELM_CHART_DIR="path/to/your/helm/chart"

# List variables defined in values.yaml
variables=$(grep -E '^\s*\w+:' "$HELM_CHART_DIR/values.yaml" | awk '{print $1}')

# Iterate over variables
for var in $variables; do
    # Check if variable is used in any template file
    if grep -rq "\${{?\s*\.Values\.${var}\s*}}?" "$HELM_CHART_DIR/templates"; then
        echo "Variable $var is used"
    else
        echo "Variable $var is unused"
    fi
done
