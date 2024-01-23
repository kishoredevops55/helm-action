#!/bin/bash

# Your Azure Key Vault name
keyVaultName="your-keyvault-name"

# List all secrets in the Key Vault
secrets=$(az keyvault secret list --vault-name $keyVaultName --output table)

# Extract secret names and values using text processing
secretNames=$(echo "$secrets" | grep -E '^(\S+)\s+\S+\s+\S+$' | awk '{print $1}')
secretValues=$(for name in $secretNames; do az keyvault secret show --vault-name $keyVaultName --name $name --query 'value' --output tsv; done)

# Print secret names and values in the specified format
echo "SecretName\tSecretValue"
for ((i=1; i<=${#secretNames[@]}; i++)); do
  currentName=${secretNames[$i-1]}
  currentValue=${secretValues[$i-1]}
  printf "%s\t%s\n" "$currentName" "$currentValue"
done

echo "Secrets exported in the specified format"
