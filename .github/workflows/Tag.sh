acr_name="<registry-name>"
repo_name="<repository-name>"

# Get the list of image digests with their tags
tags=$(az acr repository show-tags --name $acr_name --repository $repo_name --orderby time_desc --output tsv)

# Loop through each tag and get the digest and last modified time
echo "$tags" | while IFS=$'\t' read -r tag digest; do
  last_modified=$(az acr repository show-manifests --name $acr_name --repository $repo_name --digest $digest --query "lastUpdateTime" --output tsv)
  echo "Image: $repo_name:$tag, Digest: $digest, Last Modified: $last_modified"
done
