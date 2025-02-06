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

# Fetch only dashboards
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


def fetch_dashboard_details(uid):
    """
    For a given dashboard UID, retrieve detailed info using GET /api/dashboards/uid/<uid>.
    Returns a tuple: (dashboard_title, folder_title).
    Uses the 'title' key within the 'dashboard' object for the actual dashboard title.
    If the folder is reported as 'General' (the default parent), it will now return "Dashboards".
    """
    details_url = f"{GRAFANA_URL}/api/dashboards/uid/{uid}"
    try:
        response = requests.get(details_url, headers=HEADERS)
        response.raise_for_status()
        details = response.json()
        dashboard_title = details.get("dashboard", {}).get("title", "Unknown Dashboard")
        folder_title = details.get("meta", {}).get("folderTitle", "General")
        # If the folder is 'General', replace it with "Dashboards"
        if folder_title == "General":
            folder_title = "Dashboards"
        return dashboard_title, folder_title
    except requests.exceptions.RequestException:
        return "Unknown Dashboard", "Unknown Folder"


def extract_dashboard_data(dashboards):
    """
    Extracts each dashboard's actual title (from details),
    UID, folder (location), and last 30 days' view count.
    """
    data = []

    if "frames" not in dashboards:
        print("Unexpected response structure from search-v2.")
        return data

    # search-v2 returns a list of frames; each frame's data.values is a list of arrays.
    for item in dashboards["frames"]:
        values = item.get("data", {}).get("values", [])
        if len(values) < 9:
            print("Unexpected data structure in item; skipping.")
            continue

        # values[1] contains the UIDs and values[8] the view counts.
        uids = values[1]
        views = values[8]

        for uid, view in zip(uids, views):
            dashboard_title, folder_title = fetch_dashboard_details(uid)
            data.append({
                "Dashboard Name": dashboard_title,
                "UID": uid,
                "Folder Path": folder_title,
                "Views (Last 30 Days)": view
            })
            # Optional: delay to avoid hammering the API
            time.sleep(0.1)
            
    return data


def export_to_excel(data):
    """Exports the data to an Excel file."""
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
