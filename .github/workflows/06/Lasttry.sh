#!/bin/bash

# Function to check if a line contains a hard-coded value
check_hard_coded_values() {
    local file_path="$1"
    local line_number=0
    local hard_coded_values_found=false

    echo "Checking $file_path for hard-coded values..."

    while IFS= read -r line; do
        ((line_number++))
        # Check if the line contains a key-value pair in YAML format
        if grep -Eq '^[[:space:]]*[a-zA-Z0-9_-]+:[[:space:]]*([^{].+)?$' <<< "$line"; then
            # Check if the line contains a hard-coded value (excluding lines with template syntax)
            if ! grep -Eq '{{.*}}' <<< "$line" && grep -Eq ':[[:space:]]*"[^"]+"' <<< "$line"; then
                echo "Warning: Hard-coded string value found at line $line_number in $file_path"
                hard_coded_values_found=true
            fi
            if ! grep -Eq '{{.*}}' <<< "$line" && grep -Eq ':[[:space:]]*[0-9]+' <<< "$line"; then
                echo "Warning: Hard-coded numeric value found at line $line_number in $file_path"
                hard_coded_values_found=true
            fi
            if ! grep -Eq '{{.*}}' <<< "$line" && grep -Eq ':[[:space:]]*[a-zA-Z0-9_-]+' <<< "$line"; then
                echo "Warning: Hard-coded key-value pair found at line $line_number in $file_path"
                hard_coded_values_found=true
            fi
        fi
    done < "$file_path"

    if [ "$hard_coded_values_found" = false ]; then
        echo "No hard-coded values found in $file_path"
    fi
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

# Check hard-coded values in Helm templates
templates_path="$helm_chart_path/templates"
if [ -d "$templates_path" ]; then
    echo "Checking for hard-coded values in Helm templates directory: $templates_path"
    for template in $(find "$templates_path" -type f -name '*.yaml'); do
        check_hard_coded_values "$template"
    done
else
    echo "Warning: No templates directory found in the Helm chart"
fi

echo "Helm chart validation complete!"
