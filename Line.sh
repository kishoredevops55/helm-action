#!/bin/bash

# Define the Helm chart directory
HELM_CHART_DIR="path/to/your/helm/chart"

# List variables defined in values.yaml along with line numbers
variables=$(grep -nE '^\s*\w+:' "$HELM_CHART_DIR/values.yaml" | awk -F ":" '{print $1,$2}')

# Iterate over variables
for var_line in $variables; do
    # Extract variable name and line number
    var=$(echo "$var_line" | awk '{print $2}')
    line_number=$(echo "$var_line" | awk '{print $1}')

    # Check if variable is used in any template file
    if grep -rq "\${{?\s*\.Values\.${var}\s*}}?" "$HELM_CHART_DIR/templates"; then
        echo "Variable $var is used"
    else
        echo "Variable $var is unused at line $line_number in values.yaml"
    fi
done
