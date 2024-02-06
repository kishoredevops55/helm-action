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
    echo "Updating resources in resource group $rg_name..."

    # Fetch resource IDs within the resource group
    resource_ids=$(az resource list --resource-group "$rg_name" --query "[].id" -o tsv)

    # Loop through each resource ID
    while IFS= read -r resource_id; do
        # Fetch current resource name
        resource_name=$(az resource show --id "$resource_id" --query "name" -o tsv)

        # Update resource name
        updated_resource_name="$tag_value-$resource_name"
        az resource update --ids "$resource_id" --set name="$updated_resource_name"

        echo "Updated name for resource with ID $resource_id: $resource_name -> $updated_resource_name"
    done <<< "$resource_ids"
done
