import requests
import os
import pandas as pd
from datetime import datetime
import time  # optional: for a small delay between requests

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
# Note: we now fetch only dashboards (not folders)
payload = {
    "query": "+",
    "tags": [],
    "sort": "-views_last_30_days",
    "starred": False,
    "deleted": False,
    "kind": ["dashboard"],  # only dashboards
    "limit": 5000
}

# -------------------------
# Functions
# -------------------------
def fetch_dashboards():
    """
    Fetch dashboards (only dashboards, no folders) sorted by views in the last 30 days.
    Returns the JSON response from search-v2.
    """
    response = requests.post(SEARCH_API_URL, json=payload, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def fetch_dashboard_folder(uid):
    """
    For a given dashboard UID, call the dashboard details endpoint
    and return the folder title (i.e. its location). If not found, return "General".
    """
    details_url = f"{GRAFANA_URL}/api/dashboards/uid/{uid}"
    try:
        response = requests.get(details_url, headers=HEADERS)
        response.raise_for_status()
        dashboard_details = response.json()
        # The details JSON contains a "meta" block with "folderTitle"
        folder_title = dashboard_details.get("meta", {}).get("folderTitle", "General")
        return folder_title
    except requests.exceptions.RequestException:
        return "Unknown Folder"


def extract_dashboard_data(dashboards):
    """
    Extracts dashboard name, UID, folder (location), and last 30 days' views count.
    Uses the search-v2 response for names, UIDs, and view counts,
    then calls fetch_dashboard_folder() to resolve the correct folder.
    """
    data = []

    if "frames" not in dashboards:
        print("Unexpected response structure from search-v2.")
        return data

    for item in dashboards["frames"]:
        values = item.get("data", {}).get("values", [])
        if len(values) < 9:
            print("Unexpected data structure in item; skipping.")
            continue

        # values[0]: names, values[1]: uids, values[8]: views
        names = values[0]
        uids = values[1]
        # Note: values[2] may be the folder uid from the search,
        # but we will get the full location from the dashboard details API.
        views = values[8]

        for name, uid, view in zip(names, uids, views):
            folder_path = fetch_dashboard_folder(uid)
            data.append({
                "Dashboard Name": name,
                "UID": uid,
                "Folder Path": folder_path,
                "Views (Last 30 Days)": view
            })
            # Optional: small delay to avoid hammering the API if many dashboards exist
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
