#!/bin/bash

# Your Azure Key Vault name
keyVaultName="your-keyvault-name"

# Get the list of secret names
secretNames=$(az keyvault secret list --vault-name $keyVaultName --query "[].name" -o tsv)

# Create or clear the output file
outputFile="secrets_output.txt"
echo -n > "$outputFile"

# Loop through secret names and get values
for secretName in $secretNames; do
    secretValue=$(az keyvault secret show --vault-name $keyVaultName --name "$secretName" --query 'value' -o tsv)
    echo -e "$secretName\t$secretValue" >> "$outputFile"
done

echo "Secrets exported to $outputFile"
