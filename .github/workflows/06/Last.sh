#!/bin/bash

# Function to check if a file contains dynamic values
check_dynamic_values() {
    local file_path="$1"
    local line_number=0
    local dynamic_values_found=false
    local hard_coded_values_found=false

    echo "Checking $file_path for dynamic and hard-coded values..."

    while IFS= read -r line; do
        ((line_number++))
        if grep -Eq '(\${.*}|{{.*}})' <<< "$line"; then
            echo "Warning: Possible dynamic value found at line $line_number"
            dynamic_values_found=true
        fi

        if grep -Eqv '(\${.*}|{{.*}})' <<< "$line"; then
            echo "Warning: Possible hard-coded value found at line $line_number"
            hard_coded_values_found=true
        fi
    done < "$file_path"

    if [ "$dynamic_values_found" = false ]; then
        echo "No dynamic values found in $file_path"
    fi

    if [ "$hard_coded_values_found" = false ]; then
        echo "No hard-coded values found in $file_path"
    fi
}

# Function to validate Helm charts using helm lint
validate_helm_chart() {
    local chart_path="$1"
    local chart_name=$(basename "$chart_path")

    echo "Validating Helm chart: $chart_name"
    helm lint "$chart_path" || exit 1
}

# Check if the Helm chart path is provided as an argument
if [ -z "$1" ]; then
    echo "Usage: $0 <helm_chart_path>"
    exit 1
fi

helm_chart_path="$1"

# Check if the given path is a directory
if [ ! -d "$helm_chart_path" ]; then
    echo "Error: $helm_chart_path is not a directory"
    exit 1
fi

# Check if the directory contains a Chart.yaml file
if [ ! -f "$helm_chart_path/Chart.yaml" ]; then
    echo "Error: $helm_chart_path does not contain a Chart.yaml file"
    exit 1
fi

# Check dynamic and hard-coded values in templates
templates_path="$helm_chart_path/templates"
if [ -d "$templates_path" ]; then
    echo "Checking for dynamic and hard-coded values in templates directory: $templates_path"
    for template in $(find "$templates_path" -type f -name '*.yaml'); do
        check_dynamic_values "$template"
    done
else
    echo "Warning: No templates directory found in the Helm chart"
fi

# Validate Helm chart using helm lint
validate_helm_chart "$helm_chart_path"

echo "Helm chart validation passed successfully!"
