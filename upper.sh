#!/bin/bash

# Directory containing input files
input_directory="/path/to/input_directory"

# Function to transform filename
transform_filename() {
    local filename=$1
    # Replace "-" with "_" and convert to uppercase
    local transformed_filename=$(echo "$filename" | tr '-' '_' | tr '[:lower:]' '[:upper:]')
    echo "$transformed_filename"
}

# Iterate over files in the input directory and transform filenames
for file in "$input_directory"/*; do
    if [ -f "$file" ]; then
        # Extract filename from the full path
        filename=$(basename "$file")
        # Transform filename
        transformed_filename=$(transform_filename "$filename")
        # Rename file with transformed filename
        mv "$file" "$input_directory/$transformed_filename"
        echo "Transformed $filename to $transformed_filename"
    fi
done
