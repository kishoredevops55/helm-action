acr_name="myregistry"
image_name="myimage"

# Get the list of image tags
tags=$(az acr repository show-tags --name $acr_name --repository $image_name --output tsv)

# Loop through each tag and print "image:tag"
for tag in $tags; do
  echo "image:$image_name:$tag"
done
