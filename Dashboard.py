import requests
import os
import pandas as pd
from datetime import datetime
import time  # Optional, for throttling API calls

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

# Payload to fetch only dashboards from search-v2
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
    If your Grafana supports nested folders, each folder object is expected
    to have a 'parentUid' key.
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
    Returns a tuple: (dashboard_title, folder_uid)
    - dashboard_title is obtained from the 'title' key inside the 'dashboard' object.
    - folder_uid is obtained from meta.folderUid.
    """
    details_url = f"{GRAFANA_URL}/api/dashboards/uid/{uid}"
    try:
        response = requests.get(details_url, headers=HEADERS)
        response.raise_for_status()
        details = response.json()
        dashboard_title = details.get("dashboard", {}).get("title", "Unknown Dashboard")
        meta = details.get("meta", {})
        folder_uid = meta.get("folderUid")
        return dashboard_title, folder_uid
    except requests.exceptions.RequestException:
        return "Unknown Dashboard", None


def get_full_folder_path(folder_uid, folder_mapping):
    """
    Given a folder UID and a folder mapping, build the full folder path.
    
    - If folder_uid is missing or not found, return "Dashboards".
    - If the folder's title is "General", return "Dashboards".
    - Otherwise, build the full path by prepending parent folders until a parent
      with title "General" is encountered.
      
    For example, if a dashboard is in:
        Parent Folder -> Child Folder
    the full path will be: "Parent Folder / Child Folder".
    """
    if not folder_uid or folder_uid not in folder_mapping:
        return "Dashboards"
    
    folder = folder_mapping[folder_uid]
    # If the folder's title is "General", then it means no custom folder was set.
    if folder.get("title", "") == "General":
        return "Dashboards"
    
    path_parts = [folder.get("title", "")]
    current = folder
    while current.get("parentUid"):
        parent_uid = current.get("parentUid")
        if parent_uid in folder_mapping:
            parent = folder_mapping[parent_uid]
            # Stop if parent is the default folder "General"
            if parent.get("title", "") == "General":
                break
            path_parts.insert(0, parent.get("title", ""))
            current = parent
        else:
            break
    return " / ".join(path_parts)


def extract_dashboard_data(dashboards, folder_mapping):
    """
    Extracts each dashboard's actual title, UID, full folder path, and last 30 days' view count.
    Uses fetch_dashboard_details() to get a reliable dashboard title and folder UID.
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

        # values[1] contains dashboard UIDs, values[8] contains view counts.
        uids = values[1]
        views = values[8]

        for uid, view in zip(uids, views):
            dashboard_title, folder_uid = fetch_dashboard_details(uid)
            full_folder_path = get_full_folder_path(folder_uid, folder_mapping)
            data.append({
                "Dashboard Name": dashboard_title,
                "UID": uid,
                "Folder Path": full_folder_path,
                "Views (Last 30 Days)": view
            })
            # Optional: delay to avoid hammering the API
            time.sleep(0.1)
    return data


def export_to_excel(data):
    """
    Exports the collected dashboard data to an Excel file.
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
    
