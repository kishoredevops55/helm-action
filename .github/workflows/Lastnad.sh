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
    echo "Updating tags for resources in resource group $rg_name..."

    # Fetch resource IDs within the resource group
    resource_ids=$(az resource list --resource-group "$rg_name" --query "[].id" -o tsv)

    # Update tags for each resource
    for resource_id in $resource_ids; do
        az tag update --resource-id "$resource_id" --operation merge --tags $tag_key=$tag_value
        echo "Updated tags for resource with ID $resource_id"
    done
done
