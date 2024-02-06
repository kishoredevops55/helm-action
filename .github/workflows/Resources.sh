#!/bin/bash

# Input variables
tag_key="dtier"
tag_value="DR3"
resource_groups_file="resource_groups.txt"  # File containing list of resource group names

# Check if resource groups file exists
if [ ! -f "$resource_groups_file" ]; then
    echo "Error: Resource groups file '$resource_groups_file' not found."
    exit 1
fi

# Read resource group names from file into array
resource_groups=()
while IFS= read -r line; do
    resource_groups+=("$line")
done < "$resource_groups_file"

# Loop through each resource group
for rg_name in "${resource_groups[@]}"; do
    # Check if tag key exists and its value matches
    existing_value=$(az group show --name "$rg_name" --query "tags.$tag_key" -o tsv)
    if [[ "$existing_value" != "$tag_value" ]]; then
        # Update tag value
        az group update --name "$rg_name" --set tags.$tag_key=$tag_value
        echo "Updated tag for resource group $rg_name"
    else
        echo "Tag for resource group $rg_name is already up to date"
    fi
done
