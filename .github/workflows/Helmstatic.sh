#!/bin/bash

# Specify the path to your Helm charts
helmChartsPath="/path/to/your/helm/charts"

# Function to check if a file contains dynamic values
check_dynamic_values() {
    local file_path=$1
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
    local chart_path=$1
    helm lint "$chart_path" || exit 1
}

# Check dynamic values in templates
for chart in "$helmChartsPath"/*/; do
    for template in "$chart"/templates/*.yaml; do
        check_dynamic_values "$template"
    done
done

# Validate Helm charts using helm lint
for chart in "$helmChartsPath"/*/; do
    validate_helm_charts "$chart"
done

echo "Helm chart validation passed successfully!"
