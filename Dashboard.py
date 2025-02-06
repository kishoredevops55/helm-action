import requests
import os
import pandas as pd
from datetime import datetime
import time  # optional, for throttling API calls

# -------------------------
# Configuration
# -------------------------
GRAFANA_URL = os.getenv("GRAFANA_URL", "https://example.com/grafana")
API_KEY = os.getenv("GRAFANA_API_KEY")
if not API_KEY or not API_KEY.strip():
    raise ValueError("GRAFANA_API_KEY is not set or empty")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# -------------------------
# Endpoints and Payloads
# -------------------------
SEARCH_API_URL = f"{GRAFANA_URL}/api/search-v2"
FOLDERS_API_URL = f"{GRAFANA_URL}/api/folders"

# Payload to fetch only dashboards
payload = {
    "query": "+",
    "tags": [],
    "sort": "-views_last_30_days",
    "starred": False,
    "deleted": False,
    "kind": ["dashboard"],
    "limit": 5000
}

# -------------------------
# Functions
# -------------------------
def fetch_dashboards():
    """
    Fetch dashboards sorted by views in the last 30 days.
    Returns the JSON response from search-v2.
    """
    response = requests.post(SEARCH_API_URL, json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def fetch_folders():
    """
    Fetch all folders from Grafana.
    Returns a mapping from folder UID to the folder object.
    Note: If your Grafana instance supports nested folders, folder objects should
    include a 'parentUid' key.
    """
    try:
        response = requests.get(FOLDERS_API_URL, headers=HEADERS)
        response.raise_for_status()
        folders = response.json()
        # Build mapping: uid -> folder object
        folder_mapping = {folder["uid"]: folder for folder in folders}
        return folder_mapping
    except requests.exceptions.RequestException:
        print("Failed to fetch folders.")
        return {}


def fetch_dashboard_details(uid):
    """
    For a given dashboard UID, retrieve detailed info using GET /api/dashboards/uid/<uid>.
    Returns the dashboard's actual title (using the 'title' key inside the 'dashboard' object).
    """
    details_url = f"{GRAFANA_URL}/api/dashboards/uid/{uid}"
    try:
        response = requests.get(details_url, headers=HEADERS)
        response.raise_for_status()
        details = response.json()
        dashboard_title = details.get("dashboard", {}).get("title", "Unknown Dashboard")
        return dashboard_title
    except requests.exceptions.RequestException:
        return "Unknown Dashboard"


def get_full_folder_path(folder_uid, folder_mapping):
    """
    Given a folder UID and a folder mapping, recursively build the full folder path.
    If no folder is found or if folder_uid is empty, returns "Dashboards".
    
    For example, if a folder is nested:
        Parent Folder -> Child Folder
    The full path becomes: "Parent Folder / Child Folder".
    
    If the folder title is "General", it's substituted with "Dashboards".
    """
    if not folder_uid or folder_uid not in folder_mapping:
        return "Dashboards"
    
    folder = folder_mapping[folder_uid]
    # If the folder title is "General", treat it as the default ("Dashboards")
    if folder.get("title", "") == "General":
        return "Dashboards"
    
    path_parts = []
    current = folder
    # Loop to build the full path using parentUid if present.
    while current:
        title = current.get("title", "")
        if title == "General":
            title = "Dashboards"
        path_parts.insert(0, title)
        parent_uid = current.get("parentUid")
        if parent_uid and parent_uid in folder_mapping:
            current = folder_mapping.get(parent_uid)
        else:
            current = None
    full_path = " / ".join(path_parts)
    return full_path


def extract_dashboard_data(dashboards, folder_mapping):
    """
    Extracts each dashboard's actual title (from details),
    UID, full folder path, and last 30 days' view count.
    """
    data = []
    if "frames" not in dashboards:
        print("Unexpected response structure.")
        return data

    for item in dashboards["frames"]:
        values = item.get("data", {}).get("values", [])
        if len(values) < 9:
            print("Unexpected data structure in item; skipping.")
            continue

        # From the search-v2 result:
        #   values[1]: list of dashboard UIDs
        #   values[2]: list of folder UIDs (may be empty or "General")
        #   values[8]: list of view counts (last 30 days)
        uids = values[1]
        folder_uids = values[2]
        views = values[8]

        for uid, folder_uid, view in zip(uids, folder_uids, views):
            dashboard_title = fetch_dashboard_details(uid)
            full_folder_path = get_full_folder_path(folder_uid, folder_mapping)
            data.append({
                "Dashboard Name": dashboard_title,
                "UID": uid,
                "Folder Path": full_folder_path,
                "Views (Last 30 Days)": view
            })
            # Optional: small delay to avoid hammering the API
            time.sleep(0.1)
            
    return data


def export_to_excel(data):
    """
    Exports the data to an Excel file.
    """
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
    """
    Main function to fetch, process, and export dashboard data.
    """
    try:
        dashboards = fetch_dashboards()
        folder_mapping = fetch_folders()
        dashboard_data = extract_dashboard_data(dashboards, folder_mapping)
        export_to_excel(dashboard_data)
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
    
