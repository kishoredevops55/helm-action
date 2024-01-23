#!/bin/bash

# Replace with your Azure Key Vault name
keyvault_name="your-keyvault-name"

# Generate raw output from Azure CLI (including names and values)
raw_output=$(az keyvault secret list --vault-name $keyvault_name --query "[].{name:name,value:value}" -o tsv)

# Extract and store secrets using a more robust approach
while IFS= read -r name value; do
  echo "$name: $value" >> secrets.txt
done <<< "$raw_output"

echo "Secret names and values stored in secrets.txt"
