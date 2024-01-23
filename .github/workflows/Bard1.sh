#!/bin/bash

# Replace with your Azure Key Vault name
keyvault_name="your-keyvault-name"

# Enable verbose output to capture hidden values
export AZURE_CLI_DEBUG=true

# Get raw data with names and string-casted values
raw_output=$(az keyvault secret list --vault-name $keyvault_name --query "[].{name:name,value:value.tostring}" -o tsv)

# Clear debug flag after data retrieval
unset AZURE_CLI_DEBUG

# Ensure output isn't empty
if [[ -z "$raw_output" ]]; then
  echo "Error: Could not retrieve secrets from Key Vault."
  exit 1
fi

# Extract and store secrets
while IFS= read -r name value; do
  echo "$name: $value" >> secrets.txt
done <<< "$raw_output"

echo "Secret names and values stored in secrets.txt"
