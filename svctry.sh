#!/bin/bash

# Set default namespace (configurable)
NAMESPACE="your_namespace"

# Function to handle errors
function handle_error() {
  local exit_status=$?
  echo "Error: $1" >&2
  echo "Command exited with status $exit_status" >&2
  exit $exit_status
}

# Function to validate namespace
function validate_namespace() {
  if ! kubectl get namespace "$1" > /dev/null 2>&1; then
    handle_error "Namespace $1 does not exist."
  fi
}

# Get the namespace from the user (optional)
read -p "Enter the namespace to scan (default: $NAMESPACE): " INPUT_NAMESPACE
if [[ ! -z "$INPUT_NAMESPACE" ]]; then
  validate_namespace "$INPUT_NAMESPACE"
  NAMESPACE="$INPUT_NAMESPACE"
fi

# Get ServiceEntries
SERVICE_ENTRIES=$(kubectl get serviceentries -n "$NAMESPACE" -o=jsonpath='{.items[*].metadata.name}' || handle_error "Failed to get ServiceEntries")

# Process ServiceEntries
declare -A ENTRY_COUNTS
DUPLICATE_ENTRIES=()
PROBLEMATIC_ENTRIES=()

for ENTRY_NAME in $SERVICE_ENTRIES; do
  ((ENTRY_COUNTS["$ENTRY_NAME"]++))

  # Check for problematic entries (same name, different ports)
  PORT_COUNT=$(kubectl get serviceentry "$ENTRY_NAME" -n "$NAMESPACE" -o=jsonpath='{.spec.ports[*].number}' | sort -u | wc -l || handle_error "Error processing ServiceEntry: $ENTRY_NAME")
  if [[ $PORT_COUNT -gt 1 ]]; then
    PROBLEMATIC_ENTRIES+=("$ENTRY_NAME")
  fi
done

# Output results
echo "Scan results for namespace: $NAMESPACE"

# Function to print array elements
function print_array() {
  local array_name="$1"
  local array=("${!array_name}")
  for element in "${array[@]}"; do
    echo "    $element"
  done
}

if [[ ${#DUPLICATE_ENTRIES[@]} -gt 0 ]]; then
  echo "  Duplicate ServiceEntries:"
  print_array DUPLICATE_ENTRIES
fi

if [[ ${#PROBLEMATIC_ENTRIES[@]} -gt 0 ]]; then
  echo "  Problematic ServiceEntries (same name, different ports):"
  print_array PROBLEMATIC_ENTRIES
fi

if [[ ${#DUPLICATE_ENTRIES[@]} -eq 0 && ${#PROBLEMATIC_ENTRIES[@]} -eq 0 ]]; then
  echo "  No duplicates or problematic ServiceEntries found."
fi
