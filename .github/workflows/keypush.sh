#!/bin/bash

keyVaultName="your-keyvault-name"
csvFilePath="secrets.csv"
keyVaultUrl="https://$keyVaultName.vault.azure.net"

while IFS=, read -r secretName secretValue; do
    existingValue=$(az keyvault secret show --vault-name $keyVaultName --name $secretName --query 'value' --output tsv 2>/dev/null)

    if [ "$existingValue" == "$secretValue" ]; then
        echo "Secret '$secretName' already exists with matching value: $secretValue"
    elif [ -n "$existingValue" ]; then
        echo "Secret '$secretName' exists but has a different value. Current value: $existingValue, Expected value: $secretValue"
        # Add logic here for handling mismatched values, e.g., updating the secret
    else
        # Add the secret to Azure Key Vault
        az keyvault secret set --vault-name $keyVaultName --name $secretName --value "$secretValue" --output none
        echo "Added secret: '$secretName'"
    fi
done < "$csvFilePath"
