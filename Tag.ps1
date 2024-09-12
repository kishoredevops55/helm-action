# Define the input file path
$inputFile = "path\to\your\inputfile.csv"  # Replace with your actual file path

# Import the CSV file
$data = Import-Csv -Path $inputFile

# Retrieve all subscriptions for the authenticated account
$subscriptions = Get-AzSubscription

# Iterate over each row in the input data
foreach ($row in $data) {
    # Extract details from the input file
    $subscriptionName = $row.SUBSCRIPTION  # Subscription name from the CSV
    $resourceGroupName = $row.'RESOURCE GROUP'
    $resourceName = $row.'RESOURCE NAME'
    $resourceType = $row.'RESOURCE TYPE'

    # Get the subscription ID based on the subscription name
    $subscription = $subscriptions | Where-Object { $_.Name -eq $subscriptionName }

    if (-not $subscription) {
        Write-Host "Subscription '$subscriptionName' not found. Skipping this entry."
        continue  # Skip to the next resource if subscription is not found
    }

    $subscriptionId = $subscription.Id

    # Set the subscription context dynamically for each resource
    try {
        Set-AzContext -SubscriptionId $subscriptionId -ErrorAction Stop
        Write-Host "Switched to subscription: $subscriptionName ($subscriptionId)"
    } catch {
        Write-Host "Failed to set context for subscription: $subscriptionName. Error: $_"
        continue  # Skip to the next resource if setting the subscription context fails
    }

    # Construct the Resource ID dynamically
    $resourceId = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroupName/providers/$resourceType/$resourceName"

    # Get the current tags of the resource
    try {
        $resource = Get-AzResource -ResourceId $resourceId -ErrorAction Stop
        $existingTags = $resource.Tags
    } catch {
        Write-Host "Failed to retrieve resource '$resourceName' in resource group '$resourceGroupName'. Error: $_"
        continue  # Skip to the next resource if resource retrieval fails
    }

    # Define the new tag you want to add/update
    $newTagName = "Tag Name"  # Replace with your desired tag name
    $newTagValue = "Tag Value"  # Replace with your desired tag value

    # Initialize the tags in the desired format
    $tags = @{}

    # Check if the existing tags are not null and add them to the hash table
    if ($existingTags) {
        foreach ($key in $existingTags.Keys) {
            $tags[$key] = $existingTags[$key]
        }
    }

    # Check if the tag already exists and update it, or add it if it doesn't exist
    if ($tags.ContainsKey($newTagName)) {
        # If the tag value is different, update it
        if ($tags[$newTagName] -ne $newTagValue) {
            Write-Host "Updating tag '$newTagName' for resource '$resourceName' in resource group '$resourceGroupName'"
            $tags[$newTagName] = $newTagValue
        } else {
            Write-Host "Tag '$newTagName' with value '$newTagValue' already exists for resource '$resourceName'. Skipping."
        }
    } else {
        # Add the new tag
        Write-Host "Adding new tag '$newTagName' with value '$newTagValue' for resource '$resourceName' in resource group '$resourceGroupName'"
        $tags[$newTagName] = $newTagValue
    }

    # Update the tags on the resource
    try {
        Update-AzTag -ResourceId $resourceId -Tag $tags -Operation Merge -ErrorAction Stop
        Write-Host "Tags updated successfully for resource '$resourceName' in resource group '$resourceGroupName'."
    } catch {
        Write-Host "Error updating tags for resource '$resourceName' in resource group '$resourceGroupName'. Error: $_"
    }
}
