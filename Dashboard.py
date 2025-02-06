import requests
import os
import pandas as pd
from datetime import datetime

# Grafana Configuration
GRAFANA_URL = os.getenv("GRAFANA_URL", "https://example.com/grafana")
API_KEY = os.getenv("GRAFANA_API_KEY")

if not API_KEY or not API_KEY.strip():
    raise ValueError("GRAFANA_API_KEY environment variable is not set or empty")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Grafana API endpoint
SEARCH_API_URL = f"{GRAFANA_URL}/api/search-v2"

# API payload to fetch dashboards sorted by views in the last 30 days
payload = {
    "query": "+",
    "tags": [],
    "sort": "-views_last_30_days",
    "starred": False,
    "deleted": False,
    "kind": ["dashboard", "folder"],
    "limit": 5000  # Increase limit to ensure no data is missed
}


def fetch_dashboards():
    """Fetch all dashboards sorted by views in the last 30 days."""
    response = requests.post(SEARCH_API_URL, json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def extract_dashboard_data(dashboards):
    """Extracts dashboard name, UID, full folder path, and last 30 days' views count."""
    data = []

    if "frames" not in dashboards:
        print("Unexpected response structure.")
        return data

    for item in dashboards["frames"]:
        values = item.get("data", {}).get("values", [])
        if len(values) < 9:
            print("Unexpected data structure in item.")
            continue

        names, uids, folders, views = values[0], values[1], values[2], values[8]

        for name, uid, folder, view in zip(names, uids, folders, views):
            folder_path = resolve_full_folder_path(folder)
            data.append({
                "Dashboard Name": name,
                "UID": uid,
                "Folder Path": folder_path,
                "Views (Last 30 Days)": view
            })

    return data


def resolve_full_folder_path(folder_uid):
    """Fetches the full folder path including parent and subfolders."""
    if not folder_uid:
        return "General"  # Default folder

    folder_url = f"{GRAFANA_URL}/api/folders/{folder_uid}"
    try:
        response = requests.get(folder_url, headers=HEADERS)
        response.raise_for_status()
        folder_data = response.json()
        return folder_data.get("title", "Unknown Folder")
    except requests.exceptions.RequestException:
        return "Unknown Folder"


def export_to_excel(data):
    """Exports data to an Excel file."""
    if not data:
        print("No data to export.")
        return

    df = pd.DataFrame(data)
    df.sort_values(by="Views (Last 30 Days)", ascending=True, inplace=True)

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"grafana_dashboard_usage_{current_time}.xlsx"

    df.to_excel(excel_filename, index=False, engine="openpyxl")
    print(f"Data exported successfully to: {excel_filename}")


def main():
    """Main function to fetch, process, and export dashboard data."""
    try:
        dashboards = fetch_dashboards()
        dashboard_data = extract_dashboard_data(dashboards)
        export_to_excel(dashboard_data)
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
