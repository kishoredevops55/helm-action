acr_name="<registry-name>"
repo_name="<repository-name>"

# Get the list of image tags
tags=$(az acr repository show --name $acr_name --repository $repo_name --output json | grep '"tags":' | sed 's/.*"tags": \[\([^]]*\)\].*/\1/' | tr -d '[],"')

# Loop through each tag and get the digest and last modified time
for tag in $tags; do
  digest=$(az acr repository show-manifests --name $acr_name --repository $repo_name --top 1 --orderby time_desc --query "[0].digest" --output tsv)
  last_modified=$(az acr repository show-manifests --name $acr_name --repository $repo_name --digest $digest --query "[0].lastUpdateTime" --output tsv)
  echo "Image: $repo_name:$tag, Digest: $digest, Last Modified: $last_modified"
done
