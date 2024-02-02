#!/bin/bash

# Your Azure Key Vault name
keyVaultName="your-keyvault-name"

# CSV file path
csvFilePath="secrets.csv"

# Azure Key Vault URL
keyVaultUrl="https://$keyVaultName.vault.azure.net"

# Loop through the CSV file and add secrets to Azure Key Vault
while IFS=, read -r secretName secretValue; do
    # Add the secret to Azure Key Vault
    az keyvault secret set --vault-name $keyVaultName --name $secretName --value "$secretValue" --output none
done < "$csvFilePath"
