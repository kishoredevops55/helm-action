#!/bin/bash

# Define the apps
apps=("platform" "app" "Istio" "K8" "trace")

# Function to execute commands based on app name
execute_commands() {
    app=$1
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

# Main script
for app in "${apps[@]}"; do
    execute_commands $app
done
