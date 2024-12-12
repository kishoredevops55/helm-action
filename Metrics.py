import requests
import pandas as pd

PROMETHEUS_URL = "http://<prometheus-server>"  # Replace with your Prometheus server URL
POD_1 = "pod_name_1"
POD_2 = "pod_name_2"

def fetch_metrics_and_labels(pod_name):
    """Fetch all metric names and their labels for a given pod."""
    url = f"{PROMETHEUS_URL}/api/v1/series"
    params = {"match[]": f"{{pod_name=\"{pod_name}\"}}"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()["data"]
    
    metrics = {}
    for series in data:
        metric_name = series["__name__"]
        labels = {key: value for key, value in series.items() if key != "__name__"}
        if metric_name not in metrics:
            metrics[metric_name] = []
        metrics[metric_name].append(labels)
    
    return metrics

def compare_metrics(metrics_1, metrics_2):
    """Compare metrics names between two pods."""
    metrics_1_names = set(metrics_1.keys())
    metrics_2_names = set(metrics_2.keys())
    
    new_metrics = metrics_2_names - metrics_1_names
    missing_metrics = metrics_1_names - metrics_2_names
    common_metrics = metrics_1_names & metrics_2_names
    
    return new_metrics, missing_metrics, common_metrics

def compare_labels(metrics_1, metrics_2, common_metrics):
    """Compare labels and their values for common metrics."""
    label_differences = []
    
    for metric in common_metrics:
        labels_1 = metrics_1[metric]
        labels_2 = metrics_2[metric]
        
        if labels_1 != labels_2:
            label_differences.append({
                "Metric Name": metric,
                "Pod 1 Labels": labels_1,
                "Pod 2 Labels": labels_2
            })
    
    return label_differences

# Fetch metrics and labels for both pods
metrics_pod1 = fetch_metrics_and_labels(POD_1)
metrics_pod2 = fetch_metrics_and_labels(POD_2)

# Compare metrics
new_metrics, missing_metrics, common_metrics = compare_metrics(metrics_pod1, metrics_pod2)

# Compare labels for common metrics
label_differences = compare_labels(metrics_pod1, metrics_pod2, common_metrics)

# Prepare data for Excel
data_summary = [
    {"Pod Name": POD_1, "Metric Count": len(metrics_pod1)},
    {"Pod Name": POD_2, "Metric Count": len(metrics_pod2)},
]

# Save to Excel
with pd.ExcelWriter("pod_metrics_comparison.xlsx", engine="openpyxl") as writer:
    # Summary Sheet
    pd.DataFrame(data_summary).to_excel(writer, index=False, sheet_name="Summary")
    
    # New Metrics Sheet
    pd.DataFrame({"New Metrics": list(new_metrics)}).to_excel(writer, index=False, sheet_name="New Metrics")
    
    # Missing Metrics Sheet
    pd.DataFrame({"Missing Metrics": list(missing_metrics)}).to_excel(writer, index=False, sheet_name="Missing Metrics")
    
    # Label Differences Sheet
    if label_differences:
        pd.DataFrame(label_differences).to_excel(writer, index=False, sheet_name="Label Differences")
    else:
        pd.DataFrame([{"Info": "No label differences found"}]).to_excel(writer, index=False, sheet_name="Label Differences")

print("Results saved to pod_metrics_comparison.xlsx")
