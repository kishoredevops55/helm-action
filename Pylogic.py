import datetime
import pandas as pd
from tabulate import tabulate
import subprocess
import os

COST_PER_GB = 0.21601728

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    if error:
        raise Exception(error)
    return output.decode('utf-8').strip()

def get_namespaces():
    namespaces = run_command("echo $NAMESPACE").split()
    return namespaces

def get_pvc_list(namespace):
    try:
        pvc_list = run_command(f"kubectl get pvc -n {namespace} --no-headers | awk '{{print $1}}'").split()
    except Exception as e:
        print(f"No resources found in {namespace} namespace.")
        pvc_list = []
    return pvc_list

def convert_to_gb(capacity_str):
    if "Gi" in capacity_str:
        return float(capacity_str.replace('Gi', ''))
    elif "Mi" in capacity_str:
        return float(capacity_str.replace('Mi', '')) / 1024
    else:
        return 0

def get_pvc_capacity(namespace):
    try:
        pvc_capacity = run_command(f"kubectl get pvc -n {namespace} --no-headers | grep -E 'Bound' | awk '{{print $4}}'").split()
        pvc_capacity_gb = [convert_to_gb(capacity) for capacity in pvc_capacity]
    except Exception as e:
        print(f"No resources found in {namespace} namespace.")
        pvc_capacity_gb = []
    return pvc_capacity_gb

def calculate_pvc_cost(pvc_capacity_gb):
    return [capacity * COST_PER_GB for capacity in pvc_capacity_gb]

def get_unattached_pvcs(namespace, pvc_list, pvc_capacity_gb):
    unattached_pvcs = []
    pvc_costs = calculate_pvc_cost(pvc_capacity_gb)
    for i, pvc in enumerate(pvc_list):
        pvc_status = run_command(f"kubectl describe pvc {pvc} -n {namespace} | grep -E 'Used By: <none>'") or None
        if pvc_status:
            pod_name, controller_type, controller_name = get_pod_and_deployment_name(namespace, pvc)
            unattached_pvcs.append((get_cluster_name(), namespace, pvc, pvc_capacity_gb[i], pod_name, controller_type, controller_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pvc_costs[i]))
    return unattached_pvcs

def get_pod_and_deployment_name(namespace, pvc_name):
    try:
        parts = pvc_name.split('-', 1)
        if len(parts) > 1:
            prefix, rest = parts
            if rest.rsplit('-', 1)[-1].isdigit():
                pod_name = rest
                sts_name = rest.rsplit('-', 1)[0]
                return pod_name, "StatefulSet", sts_name
            else:
                deployment_name = rest
                pod_name = f"{deployment_name}-placeholder-for-pod-name"
                return pod_name, "Deployment", deployment_name
        else:
            pod_name = sts_name = pvc_name
            return pod_name, "Unknown", sts_name
    except Exception as e:
        return "Error retrieving pod/deployment name", "Error", str(e)

def get_cluster_name():
    cluster = run_command("kubectl config current-context")
    return cluster.replace('-admin', '')

def apply_excel_formatting(file_name, df):
    wb = Workbook()
    ws = wb.active
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), 1):
        for c_idx, value in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=value)
            cell.fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
            cell.border = Border(bottom=Side(style='thin'))
            if r_idx == 1:
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.border = Border(bottom=Side(style='thin'))
    for column_cells in ws.columns:
        length = max(len(str(cell.value)) for cell in column_cells) + 2
        ws.column_dimensions[column_cells[0].column_letter].width = length
    wb.save(file_name)

def load_team_data(file_path):
    with open(file_path, 'r') as file:
        data = file.read().splitlines()
    return data

def main(namespace_file, platform_file, ingestion_file, support_file):
    namespaces = get_namespaces()

    platform_apps = load_team_data(platform_file)
    ingestion_apps = load_team_data(ingestion_file)
    support_apps = load_team_data(support_file)

    all_unattached_pvcs = []
    for namespace in namespaces:
        pvc_list = get_pvc_list(namespace)
        pvc_capacity_gb = get_pvc_capacity(namespace)
        unattached_pvcs = get_unattached_pvcs(namespace, pvc_list, pvc_capacity_gb)
        all_unattached_pvcs.extend(unattached_pvcs)

    print(tabulate(all_unattached_pvcs, headers=["Cluster Name", "Namespace", "Unattached PVC Name", "Capacity GB", "Unattached Pod Name", "Controller Type", "Controller Name", "Date", "Cost ($)"]))

    df = pd.DataFrame(all_unattached_pvcs, columns=["Cluster Name", "Namespace", "Unattached PVC Name", "Capacity GB", "Unattached Pod Name", "Controller Type", "Controller Name", "Date", "Cost ($)"])
    df.columns = ["Cluster Name", "Namespace", "Unattached PVC Name", "Capacity GB", "Unattached Pod Name", "Kubernetes Deployment Type", "Kubernetes Deployment Name", "Date", "Cost ($)"]

    email_recipients = []
    for index, row in df.iterrows():
        pvc_name = row["Unattached PVC Name"]
        recipients = {"devops_team@example.com", "support_team@example.com"}  # Default recipients
        if any(app in pvc_name for app in platform_apps):
            recipients.add("platform_team@example.com")
        if any(app in pvc_name for app in ingestion_apps):
            recipients.add("ingestion_team@example.com")
        if any(app in pvc_name for app in support_apps):
            recipients.add("support_team@example.com")
        email_recipients.append(recipients)

    unique_recipients = set().union(*email_recipients)
    
    file_name = f"{get_cluster_name()}-{datetime.datetime.now().strftime('%d-%m-%Y')}.xlsx"
    apply_excel_formatting(file_name, df)

    print(f"Excel file with advanced formatting created at: {os.path.abspath(file_name)}")

    with open('unattached_pvcs_found.txt', 'w') as f:
        f.write('true' if len(all_unattached_pvcs) > 0 else 'false')

    with open('email_recipients.txt', 'w') as f:
        f.write(','.join(unique_recipients))

if __name__ == "__main__":
    import sys
    namespace_file = sys.argv[1]
    platform_file = sys.argv[2]
    ingestion_file = sys.argv[3]
    support_file = sys.argv[4]
    main(namespace_file, platform_file, ingestion_file, support_file)
  
