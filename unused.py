from kubernetes import client, config
from datetime import datetime, timedelta
import pandas as pd

# Load Kubernetes config (read-only ServiceAccount recommended for production)
config.load_kube_config()

# Initialize API clients
core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
custom_objects_api = client.CustomObjectsApi()

# Define a time threshold (last 30 days)
THIRTY_DAYS_AGO = datetime.now() - timedelta(days=30)

# Helper: Check if resource is older than 30 days
def is_older_than_30_days(timestamp):
    if not timestamp:
        return False
    return timestamp < THIRTY_DAYS_AGO

# Helper: Load namespaces from input file
def load_namespaces(file_path):
    with open(file_path, "r") as file:
        return [line.strip() for line in file if line.strip()]

# Step 1: Get all resources linked to Pods in specific namespaces
def get_pod_resources(namespaces):
    resources = {
        "config_maps": set(),
        "secrets": set(),
        "persistent_volume_claims": set(),
        "service_accounts": set(),
    }

    for namespace in namespaces:
        pods = core_v1.list_namespaced_pod(namespace, timeout_seconds=30).items
        for pod in pods:
            # Collect ConfigMaps, Secrets, PVCs, and ServiceAccounts
            for volume in pod.spec.volumes or []:
                if volume.config_map:
                    resources["config_maps"].add(volume.config_map.name)
                if volume.secret:
                    resources["secrets"].add(volume.secret.secret_name)
                if volume.persistent_volume_claim:
                    resources["persistent_volume_claims"].add(volume.persistent_volume_claim.claim_name)

            if pod.spec.service_account_name:
                resources["service_accounts"].add(pod.spec.service_account_name)

    return resources

# Step 2: Identify unused resources (including Istio CRDs)
def get_unused_resources(namespaces, pod_resources):
    unused = {
        "config_maps": [],
        "secrets": [],
        "persistent_volume_claims": [],
        "service_accounts": [],
        "istio_gateways": [],
        "istio_virtual_services": [],
        "istio_destination_rules": [],
        "istio_service_entries": [],
    }

    for namespace in namespaces:
        # ConfigMaps
        for cm in core_v1.list_namespaced_config_map(namespace, timeout_seconds=30).items:
            if cm.metadata.name not in pod_resources["config_maps"] and is_older_than_30_days(cm.metadata.creation_timestamp):
                unused["config_maps"].append(f"{namespace}/{cm.metadata.name}")

        # Secrets
        for secret in core_v1.list_namespaced_secret(namespace, timeout_seconds=30).items:
            if secret.metadata.name not in pod_resources["secrets"] and is_older_than_30_days(secret.metadata.creation_timestamp):
                unused["secrets"].append(f"{namespace}/{secret.metadata.name}")

        # PVCs
        for pvc in core_v1.list_namespaced_persistent_volume_claim(namespace, timeout_seconds=30).items:
            if pvc.metadata.name not in pod_resources["persistent_volume_claims"] and is_older_than_30_days(pvc.metadata.creation_timestamp):
                unused["persistent_volume_claims"].append(f"{namespace}/{pvc.metadata.name}")

        # ServiceAccounts
        for sa in core_v1.list_namespaced_service_account(namespace, timeout_seconds=30).items:
            if sa.metadata.name not in pod_resources["service_accounts"] and is_older_than_30_days(sa.metadata.creation_timestamp):
                unused["service_accounts"].append(f"{namespace}/{sa.metadata.name}")

        # Istio CRDs
        for resource, plural in [
            ("istio_gateways", "gateways"),
            ("istio_virtual_services", "virtualservices"),
            ("istio_destination_rules", "destinationrules"),
            ("istio_service_entries", "serviceentries"),
        ]:
            istio_resources = custom_objects_api.list_namespaced_custom_object(
                group="networking.istio.io", version="v1beta1", namespace=namespace, plural=plural, timeout_seconds=30
            )["items"]

            for res in istio_resources:
                if is_older_than_30_days(res["metadata"]["creationTimestamp"]):
                    unused[resource].append(f"{namespace}/{res['metadata']['name']}")

    return unused

# Step 3: Generate Excel report
def generate_report(unused_resources):
    df = pd.DataFrame.from_dict(unused_resources, orient="index").transpose()
    file_name = "unused_k8s_istio_resources_report.xlsx"
    df.to_excel(file_name, index=False)
    print(f"Report generated: {file_name}")

# Main function
if __name__ == "__main__":
    # Input file containing namespaces
    input_file = "namespaces.txt"

    try:
        print("Loading namespaces from file...")
        namespaces = load_namespaces(input_file)

        print("Fetching pod-related resources...")
        pod_resources = get_pod_resources(namespaces)

        print("Identifying unused resources...")
        unused_resources = get_unused_resources(namespaces, pod_resources)

        print("Generating report...")
        generate_report(unused_resources)

        print("Script execution completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
