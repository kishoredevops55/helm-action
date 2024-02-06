#!/bin/bash

# Find all Helm charts in the current directory and its subdirectories
helmCharts=$(find . -type d -name charts -exec dirname {} \;)

# Function to check if a file contains dynamic values
check_dynamic_values() {
    local file_path="$1"
    local line_number=0

    while IFS= read -r line; do
        ((line_number++))
        if grep -Eq '(\${.*}|{{.*}})' <<< "$line"; then
            echo "Warning: Possible dynamic value found in $file_path at line $line_number"
        fi
    done < "$file_path"
}

# Function to validate Helm charts using helm lint
validate_helm_charts() {
    local chart_path="$1"
    helm lint "$chart_path" || exit 1
}

# Loop through each Helm chart
for chart in $helmCharts; do
    # Check dynamic values in templates
    for template in $(find "$chart/templates" -type f -name '*.yaml'); do
        check_dynamic_values "$template"
    done

    # Validate Helm chart using helm lint
    validate_helm_charts "$chart"
done

echo "Helm chart validation passed successfully!"
