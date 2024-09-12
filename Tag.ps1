# Define the input file path
$inputFile = "path\to\your\inputfile.csv"  # Replace with your actual file path

# Define output log file path with the current date and time for IST timezone
$date = (Get-Date).ToUniversalTime().AddHours(5.5).ToString("yyyy-MM-dd_HH-mm-ss")
$outputLogFile = "UpdateTagsLog_$date.txt"

# Initialize the log file
Add-Content -Path $outputLogFile -Value "Tag Update Log - $date (IST)`n"

# Import the CSV file
try {
    $data = Import-Csv -Path $inputFile -ErrorAction Stop
} catch {
    Write-Host "Error: Unable to read input CSV file. Check the file path and format. Error: $_"
    Add-Content -Path $outputLogFile -Value "Error: Unable to read input CSV file. Error: $_`n"
    exit 1  # Exit the script with an error code
}

# Retrieve all subscriptions for the authenticated account
try {
    $subscriptions = Get-AzSubscription -ErrorAction Stop
} catch {
    Write-Host "Error: Failed to retrieve Azure subscriptions. Error: $_"
    Add-Content -Path $outputLogFile -Value "Error: Failed to retrieve Azure subscriptions. Error: $_`n"
    exit 1
}

# Define the new tag you want to add/update
$newTagName = "Tag Name"  # Replace with your desired tag name
$newTagValue = "Tag Value"  # Replace with your desired tag value

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
        $message = "Subscription '$subscriptionName' not found. Skipping this entry."
        Write-Host $message
        Add-Content -Path $outputLogFile -Value "$message`n"
        continue  # Skip to the next resource if subscription is not found
    }

    $subscriptionId = $subscription.Id

    # Set the subscription context dynamically for each resource
    try {
        Set-AzContext -SubscriptionId $subscriptionId -ErrorAction Stop
        $message = "Switched to subscription: $subscriptionName ($subscriptionId)"
        Write-Host $message
        Add-Content -Path $outputLogFile -Value "$message`n"
    } catch {
        $message = "Failed to set context for subscription: $subscriptionName. Error: $_"
        Write-Host $message
        Add-Content -Path $outputLogFile -Value "$message`n"
        continue  # Skip to the next resource if setting the subscription context fails
    }

    # Construct the Resource ID dynamically
    $resourceId = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroupName/providers/$resourceType/$resourceName"

    # Get the current tags of the resource
    try {
        $resource = Get-AzResource -ResourceId $resourceId -ErrorAction Stop
        $existingTags = $resource.Tags
    } catch {
        $message = "Failed to retrieve resource '$resourceName' in resource group '$resourceGroupName'. Error: $_"
        Write-Host $message
        Add-Content -Path $outputLogFile -Value "$message`n"
        continue  # Skip to the next resource if resource retrieval fails
    }

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
            $message = "Updating tag '$newTagName' for resource '$resourceName' in resource group '$resourceGroupName'"
            Write-Host $message
            Add-Content -Path $outputLogFile -Value "$message`n"
            $tags[$newTagName] = $newTagValue
        } else {
            $message = "Tag '$newTagName' with value '$newTagValue' already exists for resource '$resourceName'. Skipping."
            Write-Host $message
            Add-Content -Path $outputLogFile -Value "$message`n"
        }
    } else {
        # Add the new tag
        $message = "Adding new tag '$newTagName' with value '$newTagValue' for resource '$resourceName' in resource group '$resourceGroupName'"
        Write-Host $message
        Add-Content -Path $outputLogFile -Value "$message`n"
        $tags[$newTagName] = $newTagValue
    }

    # Update the tags on the resource
    try {
        Update-AzTag -ResourceId $resourceId -Tag $tags -Operation Merge -ErrorAction Stop
        $message = "Tags updated successfully for resource '$resourceName' in resource group '$resourceGroupName'."
        Write-Host $message
        Add-Content -Path $outputLogFile -Value "$message`n"
    } catch {
        $message = "Error updating tags for resource '$resourceName' in resource group '$resourceGroupName'. Error: $_"
        Write-Host $message
        Add-Content -Path $outputLogFile -Value "$message`n"
    }
}

Write-Host "Tag update process completed. Check the log file: $outputLogFile"
