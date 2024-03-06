#!/bin/bash

# Define the directory containing the Helm chart
HELM_CHART_DIR="Helmchart"

# Find the values.yaml files within the Helm chart directory and its subdirectories
VALUES_FILES=$(find "$HELM_CHART_DIR" -type f -name "values.yaml")

if [ -z "$VALUES_FILES" ]; then
    echo "No values.yaml files found in $HELM_CHART_DIR or its subdirectories"
    exit 1
fi

# Initialize variable to store unused variables
unused_variables=""

# Iterate over each values.yaml file
while IFS= read -r VALUES_FILE; do
    # Render the Helm chart
    rendered_chart=$(helm template "$HELM_CHART_DIR" -f "$VALUES_FILE")

    # List variables defined in values.yaml
    variables=$(awk '/^[a-zA-Z0-9_-]+:/ { print $1 }' "$VALUES_FILE")

    # Check for unused variables
    for var in $variables; do
        if ! grep -q "\${{?\s*\.Values\.${var}\s*}}?" <<< "$rendered_chart"; then
            # Append the unused variable and its line number to the list
            unused_variables+="Unused variable '$var' in $VALUES_FILE"
            unused_variables+=" (line $(grep -n "$var" "$VALUES_FILE" | cut -d':' -f1))\n"
        fi
    done
done <<< "$VALUES_FILES"

# Output the list of unused variables
if [ -z "$unused_variables" ]; then
    echo "No unused variables found in $HELM_CHART_DIR"
else
    echo -e "Unused variables:\n$unused_variables"
fi
