import requests
import pandas as pd
from datetime import datetime

# Set your Grafana URL and API Key
GRAFANA_URL = "https://your-grafana-instance.com"  # Replace with your Grafana URL
API_KEY = "your_api_key_here"  # Replace with your actual API key

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def fetch_dashboards():
    """Fetch the list of all dashboards sorted by views in the last 30 days."""
    url = f"{GRAFANA_URL}/api/search-v2"
    body = {
        "query": "",
        "tags": [],
        "sort": "-views_last_30_days",
        "starred": False,
        "deleted": False,
        "kind": ["dashboard"],
        "limit": 1000  # Adjust limit as needed
    }

    try:
        response = requests.post(url, json=body, headers=HEADERS)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

def fetch_folder_path(folder_uid):
    """Fetch full folder path given a folder UID."""
    if not folder_uid:
        return "General"

    url = f"{GRAFANA_URL}/api/folders/{folder_uid}"
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        folder_info = response.json()
        return folder_info.get("title", "Unknown Folder")
    except requests.exceptions.RequestException:
        return "Unknown Folder"

def main():
    dashboards = fetch_dashboards()
    if not dashboards or "frames" not in dashboards:
        print("Unexpected response structure")
        return

    data = []
    
    for item in dashboards["frames"]:
        values = item.get("data", {}).get("values", [])
        if len(values) < 9:
            print("Unexpected data structure in item")
            continue

        names, uids, folder_uids, views = values[0], values[1], values[2], values[8]

        for name, uid, folder_uid, view in zip(names, uids, folder_uids, views):
            full_folder_path = fetch_folder_path(folder_uid)
            data.append({
                "Dashboard Name": name,
                "UID": uid,
                "Folder Path": full_folder_path,
                "Views (Last 30 Days)": view
            })

    # Export to Excel
    df = pd.DataFrame(data)
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"grafana_dashboard_usage_{current_time}.xlsx"
    df.to_excel(excel_filename, index=False, engine="openpyxl")

    print(f"Data exported successfully to: {excel_filename}")

if __name__ == "__main__":
    main()
