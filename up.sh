#!/bin/bash

# Read the content of text.txt
content=$(<text.txt)

# Replace "-" with "_" and convert to uppercase
transformed_content=$(echo "$content" | tr '-' '_' | tr '[:lower:]' '[:upper:]')

# Output the transformed content
echo "$transformed_content"
