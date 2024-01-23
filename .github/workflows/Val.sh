#!/bin/bash

# Your Azure Key Vault name
keyVaultName="your-keyvault-name"

# List all secrets in the Key Vault
secrets=$(az keyvault secret list --vault-name $keyVaultName --output table)

# Extract secret names and values using text processing
secretNames=$(echo "$secrets" | grep -E '^(\S+)\s+\S+\s+\S+$' | awk '{print $1}')
secretValues=$(for name in $secretNames; do az keyvault secret show --vault-name $keyVaultName --name $name --query 'value' --output tsv; done)

# Create a CSV file with secret names and values
echo "SecretName,SecretValue" > secrets.csv
for ((i=1; i<=${#secretNames[@]}; i++)); do
  echo "${secretNames[$i-1]},${secretValues[$i-1]}" >> secrets.csv
done

echo "Secrets exported to secrets.csv"
