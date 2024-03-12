#!/bin/bash

# Check if an app name was provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 app_name"
    exit 1
fi

# The app name is the first command-line argument
app=$1

# Function to execute commands based on app name
execute_commands() {
    case $app in
        "platform")
            echo "Executing commands for platform"
            kubectl get pods
            kubectl get deploy $app
            ;;
        "app")
            echo "Executing commands for app"
            kubectl get pods
            kubectl get deploy $app
            ;;
        "Istio")
            echo "Executing commands for Istio"
            kubectl get pods -n istio-system
            kubectl get svc -n istio-system
            ;;
        "K8")
            echo "Executing commands for K8"
            kubectl get nodes
            kubectl get namespaces
            ;;
        "trace")
            echo "Executing commands for trace"
            kubectl get events --all-namespaces
            ;;
        *)
            echo "Unknown app: $app"
            ;;
    esac
}

# Execute the commands for the provided app
execute_commands
