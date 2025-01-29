from kubernetes import client, config
import pandas as pd

# Load kubeconfig (Use config.load_incluster_config() if running inside a cluster)
config.load_kube_config()

# Initialize API clients
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()
rbac_v1 = client.RbacAuthorizationV1Api()
networking_v1 = client.NetworkingV1Api()
autoscaling_v1 = client.AutoscalingV1Api()
custom_objects_api = client.CustomObjectsApi()

# Function to find unused Persistent Volumes
def find_unused_pvs():
    return [pv.metadata.name for pv in v1.list_persistent_volume().items if pv.status.phase == "Available"]

# Function to find unused ConfigMaps & Secrets
def find_unused_configmaps_and_secrets():
    used_configmaps, used_secrets = set(), set()
    pods = v1.list_pod_for_all_namespaces().items
    for pod in pods:
        if pod.spec.volumes:
            for volume in pod.spec.volumes:
                if volume.config_map:
                    used_configmaps.add(volume.config_map.name)
                if volume.secret:
                    used_secrets.add(volume.secret.secret_name)
    all_configmaps = {cm.metadata.name for cm in v1.list_config_map_for_all_namespaces().items}
    all_secrets = {sec.metadata.name for sec in v1.list_secret_for_all_namespaces().items}
    return list(all_configmaps - used_configmaps), list(all_secrets - used_secrets)

# Function to find unused Services
def find_unused_services():
    unused_services = []
    for svc in v1.list_service_for_all_namespaces().items:
        endpoints = v1.read_namespaced_endpoints(svc.metadata.name, svc.metadata.namespace)
        if not endpoints.subsets:
            unused_services.append(svc.metadata.name)
    return unused_services

# Function to find idle Deployments, StatefulSets, DaemonSets, and Replicasets
def find_idle_workloads():
    idle_deployments = [d.metadata.name for d in apps_v1.list_deployment_for_all_namespaces().items if d.status.replicas == 0]
    idle_statefulsets = [s.metadata.name for s in apps_v1.list_stateful_set_for_all_namespaces().items if s.status.replicas == 0]
    idle_daemonsets = [d.metadata.name for d in apps_v1.list_daemon_set_for_all_namespaces().items if d.status.current_number_scheduled == 0]
    idle_replicasets = [r.metadata.name for r in apps_v1.list_replica_set_for_all_namespaces().items if r.status.replicas == 0]
    return idle_deployments, idle_statefulsets, idle_daemonsets, idle_replicasets

# Function to find unused Jobs & CronJobs
def find_unused_jobs():
    unused_jobs = [j.metadata.name for j in batch_v1.list_job_for_all_namespaces().items if j.status.succeeded or j.status.failed]
    unused_cronjobs = [cj.metadata.name for cj in batch_v1.list_cron_job_for_all_namespaces().items if not cj.spec.suspend]
    return unused_jobs, unused_cronjobs

# Function to find unused RBAC resources (Roles, RoleBindings, ClusterRoles)
def find_unused_rbac():
    unused_roles = [r.metadata.name for r in rbac_v1.list_role_for_all_namespaces().items]
    unused_rolebindings = [rb.metadata.name for rb in rbac_v1.list_role_binding_for_all_namespaces().items]
    unused_clusterroles = [cr.metadata.name for cr in rbac_v1.list_cluster_role().items]
    return unused_roles, unused_rolebindings, unused_clusterroles

# Function to find unused ServiceAccounts
def find_unused_service_accounts():
    return [sa.metadata.name for sa in v1.list_service_account_for_all_namespaces().items]

# Function to find unused PodDisruptionBudgets (PDBs)
def find_unused_pdbs():
    return [pdb.metadata.name for pdb in v1.list_pod_disruption_budget_for_all_namespaces().items]

# Function to find unused Custom Resource Definitions (CRDs)
def find_unused_crds():
    return [crd.metadata.name for crd in custom_objects_api.list_cluster_custom_object("apiextensions.k8s.io", "v1", "customresourcedefinitions")["items"]]

# Function to find unused StorageClasses
def find_unused_storage_classes():
    return [sc.metadata.name for sc in v1.list_storage_class().items]

# Function to find unused NetworkPolicies
def find_unused_network_policies():
    return [np.metadata.name for np in networking_v1.list_network_policy_for_all_namespaces().items]

# Function to find unused Horizontal Pod Autoscalers (HPAs)
def find_unused_hpas():
    return [hpa.metadata.name for hpa in autoscaling_v1.list_horizontal_pod_autoscaler_for_all_namespaces().items]

# Function to save results to an Excel file
def save_results_to_excel(unused_resources):
    with pd.ExcelWriter("unused_k8s_resources.xlsx") as writer:
        for resource, items in unused_resources.items():
            if items:
                df = pd.DataFrame(items, columns=["Unused " + resource])
                df.to_excel(writer, sheet_name=resource, index=False)
    print("✅ Results saved to 'unused_k8s_resources.xlsx'")

# Main function to scan for unused resources
def scan_unused_resources():
    print("🔍 Scanning Kubernetes cluster for unused resources...")

    unused_resources = {
        "PersistentVolumes": find_unused_pvs(),
        "ConfigMaps": find_unused_configmaps_and_secrets()[0],
        "Secrets": find_unused_configmaps_and_secrets()[1],
        "Services": find_unused_services(),
        "Deployments": find_idle_workloads()[0],
        "StatefulSets": find_idle_workloads()[1],
        "DaemonSets": find_idle_workloads()[2],
        "ReplicaSets": find_idle_workloads()[3],
        "Jobs": find_unused_jobs()[0],
        "CronJobs": find_unused_jobs()[1],
        "Roles": find_unused_rbac()[0],
        "RoleBindings": find_unused_rbac()[1],
        "ClusterRoles": find_unused_rbac()[2],
        "ServiceAccounts": find_unused_service_accounts(),
        "PodDisruptionBudgets": find_unused_pdbs(),
        "CRDs": find_unused_crds(),
        "StorageClasses": find_unused_storage_classes(),
        "NetworkPolicies": find_unused_network_policies(),
        "HorizontalPodAutoscalers": find_unused_hpas(),
    }

    save_results_to_excel(unused_resources)

# Run the script
if __name__ == "__main__":
    scan_unused_resources()
