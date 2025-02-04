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
    """Fetch all dashboards sorted by views in the last 30 days from search-v2 API."""
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

def fetch_dashboard_details(uid):
    """Fetch the correct dashboard name and folder ID using the dashboard UID."""
    url = f"{GRAFANA_URL}/api/dashboards/uid/{uid}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        dashboard_info = response.json()
        dashboard_name = dashboard_info.get("dashboard", {}).get("title", "Unknown Dashboard")
        folder_id = dashboard_info.get("meta", {}).get("folderId", None)  # Fetch folder ID
        return dashboard_name, folder_id
    except requests.exceptions.RequestException:
        return "Unknown Dashboard", None

def fetch_folder_name(folder_id, folder_cache):
    """Fetch the folder name using the folder ID."""
    if folder_id is None or folder_id == 0:
        return "General"

    if folder_id in folder_cache:
        return folder_cache[folder_id]

    url = f"{GRAFANA_URL}/api/folders"
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        folders = response.json()

        for folder in folders:
            if folder["id"] == folder_id:
                folder_cache[folder_id] = folder["title"]
                return folder["title"]

        return "Unknown Folder"
    except requests.exceptions.RequestException:
        return "Unknown Folder"

def main():
    dashboards = fetch_dashboards()
    if not dashboards or "frames" not in dashboards:
        print("Unexpected response structure")
        return

    folder_cache = {}  # Cache to store folder names
    data = []
    
    for item in dashboards["frames"]:
        values = item.get("data", {}).get("values", [])
        if len(values) < 9:
            print("Unexpected data structure in item")
            continue

        uids, views = values[1], values[8]

        for uid, view in zip(uids, views):
            dashboard_name, folder_id = fetch_dashboard_details(uid)  # Fetch dashboard name & folder ID
            folder_name = fetch_folder_name(folder_id, folder_cache)  # Get correct folder name

            data.append({
                "Dashboard Name": dashboard_name,  
                "UID": uid,
                "Folder Path": folder_name,  # Corrected folder path
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
