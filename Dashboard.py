import requests
import os
import pandas as pd
from datetime import datetime

# Grafana Configuration
GRAFANA_URL = os.getenv("GRAFANA_URL", "https://example.com/grafana-enterprise")
API_KEY = os.getenv("GRAFANA_API_KEY")

if not API_KEY or not API_KEY.strip():
    raise ValueError("GRAFANA_API_KEY environment variable is not set or empty")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

SEARCH_API_URL = f"{GRAFANA_URL}/api/search-v2"

# API payload
payload = {
    "query": "+",
    "tags": [],
    "sort": "-views_last_30_days",
    "starred": False,
    "deleted": False,
    "kind": ["dashboard", "folder"],
    "limit": 1777
}


def fetch_dashboards():
    """Fetch the list of all dashboards sorted by views in the last 30 days."""
    response = requests.post(SEARCH_API_URL, json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def fetch_folder_mappings():
    """Fetch all folders and return a mapping of UID -> Full Path."""
    folder_url = f"{GRAFANA_URL}/api/folders"
    response = requests.get(folder_url, headers=HEADERS)
    
    if response.status_code != 200:
        print("Failed to fetch folder data, defaulting to folder UID")
        return {}

    folders = response.json()
    folder_map = {f["uid"]: f["title"] for f in folders}  # Map folder UID -> Folder Name
    return folder_map


def main():
    """Main function to fetch and export dashboard data."""
    try:
        dashboards = fetch_dashboards()
        folder_map = fetch_folder_mappings()  # Get correct folder names

        if "frames" not in dashboards:
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
                folder_name = folder_map.get(folder_uid, "General")  # Map UID -> Folder Name
                data.append({
                    "Dashboard Name": name,
                    "UID": uid,
                    "Folder Path": folder_name,
                    "Views (Last 30 Days)": view
                })

        # Export to Excel
        df = pd.DataFrame(data)
        df.sort_values(by="Views (Last 30 Days)", ascending=True, inplace=True)

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"grafana_dashboard_usage_{current_time}.xlsx"

        df.to_excel(excel_filename, index=False, engine="openpyxl")
        print(f"Data exported successfully to: {excel_filename}")

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
            
