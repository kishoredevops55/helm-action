#!/bin/bash

# Replace with your Azure Key Vault name
keyvault_name="your-keyvault-name"

# Generate raw output from Azure CLI (without jq formatting)
raw_output=$(az keyvault secret list --vault-name $keyvault_name --query [] -o tsv)

# Extract secret names and values using sed
while IFS= read -r line; do
  secret_name=$(echo $line | sed -n 's/\([^ ]*\) .*/\1/p')
  secret_value=$(az keyvault secret show --name $secret_name --vault-name $keyvault_name --query value -o tsv)
  echo "$secret_name: $secret_value" >> secrets.txt
done <<< "$raw_output"

echo "Secret names and values stored in secrets.txt"
